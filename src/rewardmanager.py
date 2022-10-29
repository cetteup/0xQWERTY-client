from typing import List, Optional, Any

import requests
from requests_oauthlib import OAuth2Session

import config
from classes import RewardConfig
from logger import logger


class RewardManagerError(Exception):
    pass


class RewardManager:
    broadcaster_id: str
    session: OAuth2Session

    def set_broadcaster_id(self, broadcaster_id: str) -> None:
        self.broadcaster_id = broadcaster_id

    def set_session(self, session: OAuth2Session) -> None:
        self.session = session

    def ensure_is_ready(self):
        if not hasattr(self, 'broadcaster_id') or not isinstance(self.broadcaster_id, str):
            raise RewardManagerError('Broadcaster is not set')
        elif not hasattr(self, 'session') or not isinstance(self.session, OAuth2Session):
            raise RewardManagerError('Session is not set')

    def get_rewards(self) -> List[dict]:
        self.ensure_is_ready()

        try:
            resp = self.session.get('https://api.twitch.tv/helix/channel_points/custom_rewards',
                                    params={
                                        'broadcaster_id': self.broadcaster_id,
                                        'only_manageable_rewards': 1
                                    })
            if resp.ok and self.is_valid_reward_list_response(parsed := resp.json()):
                return parsed['data']
            elif not resp.ok:
                logger.debug(resp.text)
                raise RewardManagerError(f'Failed to fetch existing rewards from Twitch '
                                         f'(HTTP/{resp.status_code}/{resp.reason})')
            else:
                logger.debug(resp.text)
                raise RewardManagerError('Twitch returned invalid response when fetching custom rewards')
        except requests.RequestException as e:
            logger.debug(e)
            raise RewardManagerError('Failed to fetch existing rewards from Twitch')

    @staticmethod
    def is_valid_reward_list_response(parsed_response: Any) -> bool:
        if isinstance(parsed_response, dict) and isinstance(parsed_response.get('data'), list) and \
                all(RewardManager.is_valid_reward_dto(elem) for elem in parsed_response['data']):
            return True

        return False

    @staticmethod
    def is_valid_reward_dto(reward_dto: Any) -> bool:
        if isinstance(reward_dto, dict) and all(key in reward_dto for key in ['id', 'title', 'cost']):
            return True

        return False

    def setup_rewards(self, configured_rewards: List[RewardConfig]) -> bool:
        modified = False
        existing_rewards = self.get_rewards()
        for reward_config in configured_rewards:
            # Don't default to None here when getting from dict, since None == None would treat the reward as found
            existing_reward = next((r for r in existing_rewards if r['id'] == reward_config.id), None)
            if existing_reward is None:
                # Any rewards without an id or with a non-existing id need to be created
                reward_config.id = self.create_reward(reward_config)
                modified = True
            else:
                # Use data from Twitch to update any existing rewards
                title = existing_reward['title']
                if title != reward_config.title:
                    reward_config.title = title
                    modified = True

                cost = existing_reward['cost']
                if cost != reward_config.cost:
                    reward_config.cost = cost
                    modified = True

        logger.info(f'All {len(configured_rewards)} configured rewards are (now) setup on Twitch')
        return modified

    def create_reward(self, reward_config: RewardConfig) -> Optional[str]:
        self.ensure_is_ready()

        try:
            resp = self.session.post(
                'https://api.twitch.tv/helix/channel_points/custom_rewards',
                params={
                    'broadcaster_id': self.broadcaster_id
                },
                json={
                    'title': reward_config.title,
                    'cost': reward_config.cost
                }
            )

            if resp.ok and self.is_valid_create_reward_response(parsed := resp.json()):
                return parsed['data'][0]['id']
            elif not resp.ok:
                logger.debug(resp.text)
                raise RewardManagerError(f'Failed to create custom reward (HTTP/{resp.status_code}/{resp.reason})')
            else:
                logger.debug(resp.text)
                raise RewardManagerError('Twitch returned invalid response when creating custom rewards')
        except requests.RequestException as e:
            logger.debug(e)
            raise RewardManagerError('Failed to create custom reward')

    @staticmethod
    def is_valid_create_reward_response(parsed_response: Any) -> bool:
        if RewardManager.is_valid_reward_list_response(parsed_response) and len(parsed_response) == 1:
            return True

        return False

    def subscribe_to_redemptions(self) -> None:
        reward_ids = [r['id'] for r in self.get_rewards()]

        if len(reward_ids) == 0:
            logger.warning('No manageable rewards found, aborting eventsub setup')
            return

        try:
            resp = requests.post(f'{config.QWERTY_API_BASE_URL}/client/eventsub-setup', json={
                'broadcaster_id': self.broadcaster_id,
                'reward_ids': reward_ids
            })

            if resp.ok:
                logger.info(f'0xQWERTY API is (now) subscribed to redemptions of {len(reward_ids)} managed rewards')
            else:
                logger.debug(resp.text)
                raise RewardManagerError(f'Failed to setup subscriptions for reward redemptions via 0xQWERTY API'
                                         f'(HTTP/{resp.status_code}/{resp.reason})')
        except requests.RequestException as e:
            logger.debug(e)
            raise RewardManagerError('Failed to setup subscriptions for reward redemptions via 0xQWERTY API')

    def update_redemption_status(self, redemption_id: str, reward_id: str, fulfilled: bool = True) -> None:
        self.ensure_is_ready()

        try:
            resp = self.session.patch(
                'https://api.twitch.tv/helix/channel_points/custom_rewards/redemptions',
                params={
                    'id': redemption_id,
                    'broadcaster_id': self.broadcaster_id,
                    'reward_id': reward_id
                },
                json={
                    'status': 'FULFILLED' if fulfilled else 'CANCELED'
                }
            )
            if not resp.ok:
                raise RewardManagerError(f'Failed to update reward redemption status '
                                         f'(HTTP/{resp.status_code}/{resp.reason})')
        except requests.RequestException as e:
            logger.debug(e)
            raise RewardManagerError('Failed to update reward redemption status')
