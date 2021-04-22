import logging

import aiohttp
from requests_oauthlib import OAuth2Session

import config


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
        logging.error('Failed to update redemption status')


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
            logging.error(f'Failed to fetch existing rewards ({resp.status_code}/{resp.reason})')
    except Exception as e:
        logging.debug(e)
        logging.error(f'Failed to fetch existing rewards')

    # Return false if no rewards were found
    if request_ok and len(reward_ids) == 0:
        logging.warning('No manageable rewards found, aborting eventsub setup')
        return False
    elif not request_ok:
        return False

    setup_ok = True
    async with aiohttp.ClientSession() as session:
        data = {'broadcaster_id': broadcaster_id, 'reward_ids': reward_ids}
        try:
            async with session.post(f'{config.QWERTY_API_BASE_URL}/client/eventsub-setup', json=data) as resp:
                if resp.status == 200:
                    logging.info('Eventsub subscriptions for relevant rewards are all set up')
                else:
                    logging.error(f'Failed to setup eventsub subscriptions (server returned {resp.status})')
                    setup_ok = False

        except aiohttp.ClientError as e:
            logging.debug(e)
            logging.error('Failed to setup eventsub subscriptions')
            setup_ok = False

    return setup_ok

