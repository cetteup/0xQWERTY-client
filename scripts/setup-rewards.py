import argparse
import logging
import sys

from requests_oauthlib import OAuth2Session

from src import config

parser = argparse.ArgumentParser(description='Setup 0xQWERTY channel point rewards and corresponding EventSub '
                                             'subscriptions for a streamer')
parser.add_argument('--user-access-token', help='User access token for the streamer\'s Twitch account', type=str,
                    required=True)
parser.add_argument('--app-access-token', help='App access token for 0xQWERTY', type=str, required=True)
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('--reward-titles', help='Titles of rewards to set up (space separated)', nargs='+', type=str)
group.add_argument('--reward-count', help='Number of rewards to set up', type=int)
parser.add_argument('--eventsub-secret', help='Secret used for verifying a EventSub challenge request signature',
                    type=str)
parser.add_argument('--eventsub-callback', help='Callback endpoint to supply for EventSub subscriptions', type=str,
                    default='https://0xqwerty-api.cetteup.com/webhooks/eventsub-callback')
parser.add_argument('--add', help='Whether to add given list/number of rewards regardless of existing ones',
                    dest='add', action='store_true')
parser.add_argument('--debug-log', help='Output tons of debugging information', dest='debug_log', action='store_true')
parser.set_defaults(add=False, debug_log=False)
args = parser.parse_args()

logging.basicConfig(level=logging.DEBUG if args.debug_log else logging.INFO,
                    format='%(asctime)s %(levelname)-8s: %(message)s')

# Make sure secret has valid length
if not 10 < len(args.eventsub_secret) < 100:
    logging.error(f'EventSub secret must be between 10 and 100 characters long (given secret is '
                  f'{len(args.eventsub_secret)} long )')
    sys.exit(1)

# Set up oauth2 session for user
twitchUser = OAuth2Session(config.CLIENT_ID, token={'access_token': args.user_access_token})
# Client ID header is not sent by default, so just manually add it to the headers
twitchUser.headers['Client-Id'] = config.CLIENT_ID

# Set up oauth2 session for app
twitchApp = OAuth2Session(config.CLIENT_ID, token={'access_token': '7osacjvbrem39qut3l04oyudphak8u'})
twitchApp.headers['Client-Id'] = config.CLIENT_ID

logging.debug('Fetching current user details')
currentUser = {}
try:
    resp = twitchUser.get('https://api.twitch.tv/helix/users')
    if resp.status_code == 200:
        parsed = resp.json()
        currentUser = parsed['data'][0]
    else:
        logging.error(f'Failed to fetch current user details ({resp.status_code}/{resp.reason})')
        sys.exit(1)
except Exception as e:
    logging.debug(e)
    logging.error('Failed to fetch current user details')
    sys.exit(1)

logging.info(f'Running setup action for {currentUser["login"]}')

logging.debug('Fetching existing rewards')
rewards = []
try:
    resp = twitchUser.get('https://api.twitch.tv/helix/channel_points/custom_rewards',
                          params={'broadcaster_id': currentUser["id"], 'only_manageable_rewards': 1})
    if resp.status_code == 200:
        parsed = resp.json()
        rewards = parsed['data']
    else:
        logging.error(f'Failed to fetch existing rewards ({resp.status_code}/{resp.reason})')
        sys.exit(1)
except Exception as e:
    logging.debug(e)
    logging.error(f'Failed to fetch existing rewards')
    sys.exit(1)

logging.info(f'Found {len(rewards)} existing rewards')

if len(rewards) < len(args.reward_titles) or args.add:
    # TODO: add new rewards
    pass

logging.debug(f'Fetching existing EventSub subscriptions')
# TODO: Add pagination handling
subscriptions = []
try:
    resp = twitchApp.get('https://api.twitch.tv/helix/eventsub/subscriptions',
                         params={'type': 'channel.channel_points_custom_reward_redemption.add'})
    if resp.status_code == 200:
        parsed = resp.json()
        subscriptions = parsed['data']
    else:
        logging.error(f'Failed to fetch existing EventSub subscriptions ({resp.status_code}/{resp.reason})')
        sys.exit(1)
except Exception as e:
    logging.debug(e)
    logging.error(f'Failed to fetch existing EventSub subscriptions')
    sys.exit(1)

# Filter out irrelevant subscriptions
rewardIds = [r['id'] for r in rewards]
subscriptions = [s for s in subscriptions if s['condition']['broadcaster_user_id'] == currentUser['id'] and
                 s['condition']['reward_id'] in rewardIds]

logging.info(f'Found existing EventSub subscriptions for {len(subscriptions)}/{len(rewards)} rewards')

# Add subscriptions for rewards that no subscription was found for
if len(subscriptions) != len(rewards):
    subscriptionsRewardIds = [s['condition']['reward_id'] for s in subscriptions]
    rewardsWithOutSubscriptions = [r for r in rewards if r['id'] not in subscriptionsRewardIds]

    logging.debug(f'Adding {len(rewardsWithOutSubscriptions)} new subscriptions')
    addedSubscriptions = []
    for reward in rewardsWithOutSubscriptions:
        try:
            resp = twitchApp.post('https://api.twitch.tv/helix/eventsub/subscriptions',
                                  json={
                                      'type': 'channel.channel_points_custom_reward_redemption.add',
                                      'version': '1',
                                      'condition': {
                                          'broadcaster_user_id': str(currentUser['id']),
                                          'reward_id': reward['id']
                                      },
                                      'transport': {
                                          'method': 'webhook',
                                          'callback': args.eventsub_callback,
                                          'secret': args.eventsub_secret
                                      }
                                  })
            if resp.status_code == 202:
                parsed = resp.json()
                addedSubscriptions.append(parsed['data'][0])
            else:
                logging.error(f'Failed to add EventSub subscription ({resp.status_code}/{resp.reason})')
        except Exception as e:
            logging.debug(e)
            logging.error(f'Failed to add EventSub subscription')

    logging.info(f'Added {len(addedSubscriptions)} new EventSub subscriptions')

    # TODO: Check status to make sure subscriptions have been enabled
