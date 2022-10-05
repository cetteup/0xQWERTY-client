from typing import List, Optional

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
            if resp.ok:
                parsed = resp.json()
                return parsed.get('data', list())
            else:
                raise RewardManagerError(f'Failed to fetch existing rewards from Twitch '
                                         f'(HTTP/{resp.status_code}/{resp.reason})')
        except requests.RequestException as e:
            logger.debug(e)
            raise RewardManagerError('Failed to fetch existing rewards from Twitch')

    def setup_rewards(self, configured_rewards: List[RewardConfig]) -> bool:
        modified = False
        existing_rewards = self.get_rewards()
        for reward_config in configured_rewards:
            # Don't default to None here when getting from dict, since None == None would treat the reward as found
            existing_reward = next((r for r in existing_rewards if r.get('id', '') == reward_config.id), None)
            if existing_reward is None:
                # Any rewards without an id or with a non-existing id need to be created
                reward_config.id = self.create_reward(reward_config)
                modified = True
            else:
                # Use data from Twitch to update any existing rewards (using current data as fallback)
                title = existing_reward.get('title', reward_config.title)
                if title != reward_config.title:
                    reward_config.title = title
                    modified = True

                cost = existing_reward.get('cost', reward_config.cost)
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
                    'boardcaster_id': self.broadcaster_id
                },
                json={
                    'title': reward_config.title,
                    'cost': reward_config.cost
                }
            )

            if resp.ok:
                parsed = resp.json()
                return parsed.get('id')
            else:
                raise RewardManagerError(f'Failed to create custom reward (HTTP/{resp.status_code}/{resp.reason})')
        except requests.RequestException as e:
            logger.debug(e)
            raise RewardManagerError('Failed to create custom reward')

    def subscribe_to_redemptions(self) -> None:
        reward_ids = [r.get('id') for r in self.get_rewards()]

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
