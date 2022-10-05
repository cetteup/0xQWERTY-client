import json
import os
import sys
import time

import aiohttp
import yaml
from jsonschema import validate, ValidationError
from requests_oauthlib import OAuth2Session

import config
from logger import logger
from classes import ClientConfig


def sleep_exit(exit_code: int, seconds: float = 15.0):
    logger.info(f'Window will close in {seconds} seconds...')
    time.sleep(seconds)
    sys.exit(exit_code)


def load_logging_config() -> dict:
    logging_config_path = os.path.join(config.ROOT_DIR, 'logging.yaml')
    try:
        with open(logging_config_path, 'r') as f:
            return yaml.safe_load(f)
    except (OSError, yaml.YAMLError):
        logger.critical(f'Failed to load logging config from {logging_config_path}')
        sleep_exit(1)


def load_client_config() -> ClientConfig:
    schema_path = os.path.join(config.ROOT_DIR, 'config.schema.json')
    try:
        with open(schema_path, 'r') as s:
            schema = json.load(s)
    except (OSError, json.JSONDecodeError):
        logger.critical(f'Failed to load config JSON schema from {schema_path}')
        sleep_exit(1)

    client_config_path = os.path.join(config.PWD, 'config.yaml')
    try:
        with open(client_config_path, 'r') as c:
            client_config = yaml.safe_load(c)
    except (OSError, yaml.YAMLError):
        logger.critical(f'Failed to load client config from {client_config_path}')
        sleep_exit(1)

    # Ensure actual client config matches schema
    try:
        validate(client_config, schema)
    except ValidationError as e:
        logger.critical(f'Client config does not match schema: {e.json_path}: {e.message}')
        sleep_exit(1)

    return ClientConfig.from_dict(client_config)


async def update_redemption_status(twitch: OAuth2Session, redemption_id: str,
                                   broadcaster_id: str, reward_id: str, fulfilled: bool = True):
    try:
        twitch.patch('https://api.twitch.tv/helix/channel_points/custom_rewards/redemptions',
                     params={
                         'id': redemption_id,
                         'broadcaster_id': broadcaster_id,
                         'reward_id': reward_id
                     },
                     data={
                         'status': 'FULFILLED' if fulfilled else 'CANCELED'
                     })
    except Exception:
        logger.error('Failed to update redemption status')


async def setup_eventsub_subscriptions(twitch: OAuth2Session, broadcaster_id: str) -> bool:
    request_ok = True
    reward_ids = []
    try:
        resp = twitch.get('https://api.twitch.tv/helix/channel_points/custom_rewards',
                          params={
                              'broadcaster_id': broadcaster_id,
                              'only_manageable_rewards': 1
                          })
        if resp.status_code == 200:
            parsed = resp.json()
            reward_ids = [r['id'] for r in parsed['data']]
        else:
            logger.error(f'Failed to fetch existing rewards ({resp.status_code}/{resp.reason})')
    except Exception as e:
        logger.debug(e)
        logger.error(f'Failed to fetch existing rewards')

    # Return false if no rewards were found
    if request_ok and len(reward_ids) == 0:
        logger.warning('No manageable rewards found, aborting eventsub setup')
        return False
    elif not request_ok:
        return False

    setup_ok = True
    async with aiohttp.ClientSession() as session:
        data = {'broadcaster_id': broadcaster_id, 'reward_ids': reward_ids}
        try:
            async with session.post(f'{config.QWERTY_API_BASE_URL}/client/eventsub-setup', json=data) as resp:
                if resp.status == 200:
                    logger.info('Eventsub subscriptions for relevant rewards are all set up')
                else:
                    logger.error(f'Failed to setup eventsub subscriptions (server returned {resp.status})')
                    setup_ok = False

        except aiohttp.ClientError as e:
            logger.debug(e)
            logger.error('Failed to setup eventsub subscriptions')
            setup_ok = False

    return setup_ok

