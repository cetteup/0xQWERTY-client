import logging

from requests_oauthlib import OAuth2Session


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
