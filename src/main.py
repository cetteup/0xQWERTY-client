import argparse
import os
import webbrowser

import pydirectinput
import socketio
import uvicorn
import yaml
from fastapi import FastAPI, Response, status
from fastapi.requests import Request
from fastapi.responses import PlainTextResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from oauthlib.oauth2 import MobileApplicationClient
from pydantic import BaseModel
from requests_oauthlib import OAuth2Session

import config
from gamedetector import GameDetector
from helpers import setup_eventsub_subscriptions, update_redemption_status
from logger import logger

parser = argparse.ArgumentParser(description='0xQWERTY - an in-game keyboard for your viewers (Windows client)')
parser.add_argument('--version', action='version', version='0xQWERTY-client 0.1.1')
parser.add_argument('--auto-fulfill', help='Automatically mark redemptions as fulfilled if game window is active',
                    dest='auto_fulfill', action='store_true')
parser.add_argument('--refund', help='Cancel and refund all redemptions regardless of whether action was taken',
                    dest='refund', action='store_true')
parser.set_defaults(auto_fulfill=False, refund=False)
args = parser.parse_args()

app = FastAPI(title='0xQWERTY - an in-game keyboard for your viewers')
templates = Jinja2Templates(directory=os.path.join(config.ROOT_DIR, 'templates'))
sio = socketio.AsyncClient(reconnection_attempts=16, logger=True, engineio_logger=True)

# Disable pydirectinput failsafe points
pydirectinput.FAILSAFE = False

rewards = []
currentUser = {}
gameDetector = GameDetector()
twitch = OAuth2Session(client=MobileApplicationClient(client_id=config.CLIENT_ID),
                       redirect_uri=config.REDIRECT_URI, scope=config.SCOPES)
# Client ID header is not sent by default, so just manually add it to the headers
twitch.headers['Client-Id'] = config.CLIENT_ID


@app.on_event('startup')
async def prompt_auth():
    global sio, rewards, gameDetector

    with open(os.path.join(config.PWD, 'rewards.yaml')) as f:
        rewards = yaml.safe_load(f)
    configuredGames = list(set([key for r in rewards for key in r['actions'].keys()]))

    gameDetector.set_configured_games(configuredGames)

    await sio.connect(config.QWERTY_API_BASE_URL)
    authorization_url, state = twitch.authorization_url(config.TWITCH_AUTH_BASE_URL)
    logger.info(f'Opening browser for Twitch authentication ({authorization_url})')
    webbrowser.open(authorization_url)


@app.on_event('shutdown')
async def shutdown():
    await sio.disconnect()


@app.get('/s/auth-callback', response_class=HTMLResponse)
async def render_page(request: Request):
    return templates.TemplateResponse('auth-callback.html',
                                      {'request': request, 'app_name': app.title, 'base_url': config.BASE_URL})


@app.get('/a/auth-url', response_class=PlainTextResponse)
async def auth_url():
    authorization_url, state = twitch.authorization_url(config.TWITCH_AUTH_BASE_URL)
    return authorization_url


class TokenFromUrlDTO(BaseModel):
    url: str


@app.post('/a/token-from-url', status_code=status.HTTP_204_NO_CONTENT)
async def auth(dto: TokenFromUrlDTO, response: Response):
    global currentUser, twitch

    # Try to store and use token
    token_valid = True
    try:
        twitch.token_from_fragment(dto.url)
        resp = twitch.get('https://api.twitch.tv/helix/users')
        if resp.ok:
            parsed = resp.json()
            currentUser = parsed['data'][0]
            await sio.emit('join', f'streamer:{currentUser["login"]}')
            await setup_eventsub_subscriptions(twitch, currentUser["id"])
            logger.info('Authentication complete, listening for redemptions')
        elif resp.status_code == 401:
            token_valid = False
    except Exception as e:
        logger.error('Failed to get current user from Twitch API')
        logger.error(e)
        token_valid = False

    if not token_valid:
        response.status_code = status.HTTP_401_UNAUTHORIZED


@sio.event
async def connect():
    logger.info('Connection to socket.io server established')


@sio.on('redemption')
async def on_message(data):
    global gameDetector

    logger.debug('Channel points redeemed!', data)
    fulfilled = False
    redemption_id = data.get('id')
    reward_id = data.get('reward_id')
    reward = next((r for r in rewards if r['id'] == reward_id), None)
    active_game = gameDetector.get_active_game()
    if reward is not None and active_game is not None:
        action = reward['actions'].get(active_game)
        if action.get('action_type') == 'keypress':
            logger.info(f'Pressing key for reward redemption ({action["action_value"]})')
            fulfilled = pydirectinput.press([str(action['action_value'])])
            if not fulfilled:
                logger.error('Keypress failed')
    elif reward is not None and active_game is None:
        logger.info('Received redemption while game window was not active, skipping')

    """
    If auto fulfilling is enabled or no action was taken, update redemption status via Twitch API to
    a) fulfilled, if action was triggered and refunding is not forced
    b) canceled, if no action was taken or refunding is forced (will refund points to user)
    """
    if args.auto_fulfill or not fulfilled:
        await update_redemption_status(
            twitch,
            redemption_id,
            currentUser.get('id'),
            reward_id,
            fulfilled and not args.refund
        )


@sio.event
def connect_error(data):
    logger.error('Connection to 0xqwerty server failed!')


@sio.event
async def disconnect():
    logger.warning('Disconnected from 0xqwerty server')


if __name__ == '__main__':
    uvicorn.run(
        app,
        host=config.LISTEN_ADDR,
        port=config.LISTEN_PORT,
        log_config=os.path.join(config.ROOT_DIR, 'logging.yaml')
    )
