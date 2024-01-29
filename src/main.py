import argparse
import logging.config
import os
import webbrowser
from contextlib import asynccontextmanager

import pydirectinput
import socketio
import uvicorn
from fastapi import FastAPI, Response, status
from fastapi.requests import Request
from fastapi.responses import PlainTextResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from oauthlib.oauth2 import MobileApplicationClient
from requests_oauthlib import OAuth2Session

import config
from classes import RewardActionType, TokenFromUrlDTO
from gamedetector import GameDetector
from logger import logger
from rewardmanager import RewardManager, RewardManagerError
from utility import load_client_config, load_logging_config, sleep_sigterm, dump_client_config

parser = argparse.ArgumentParser(
    description='0xQWERTY - Automatically press keys in-game when Twitch viewers redeem channel point rewards'
)
parser.add_argument('--version', action='version', version='0xQWERTY-client v1.0.7')
args = parser.parse_args()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global sio, cc, gameDetector

    configured_games = list(set([key for r in cc.rewards for key in r.actions.keys()]))

    gameDetector.set_configured_games(configured_games)

    await sio.connect(config.QWERTY_API_BASE_URL)
    authorization_url, state = twitch.authorization_url(config.TWITCH_AUTH_BASE_URL)
    logger.info(f'Opening browser for Twitch authentication ({authorization_url})')
    webbrowser.open(authorization_url)

    yield

    await sio.disconnect()


app = FastAPI(title='0xQWERTY-client', lifespan=lifespan)
templates = Jinja2Templates(directory=os.path.join(config.ROOT_DIR, 'templates'))
sio = socketio.AsyncClient(reconnection_attempts=16, logger=True, engineio_logger=True)

# Disable pydirectinput failsafe points
pydirectinput.FAILSAFE = False

broadcaster = {}
gameDetector = GameDetector()
rm = RewardManager()
twitch = OAuth2Session(client=MobileApplicationClient(client_id=config.CLIENT_ID),
                       redirect_uri=config.REDIRECT_URI, scope=config.SCOPES)
# Client ID header is not sent by default, so just manually add it to the headers
twitch.headers['Client-Id'] = config.CLIENT_ID


@app.get('/s/auth-callback', response_class=HTMLResponse)
async def render_page(request: Request):
    return templates.TemplateResponse('auth-callback.html',
                                      {'request': request, 'app_name': app.title, 'base_url': config.BASE_URL})


@app.get('/a/auth-url', response_class=PlainTextResponse)
async def auth_url():
    authorization_url, state = twitch.authorization_url(config.TWITCH_AUTH_BASE_URL)
    return authorization_url


@app.post('/a/token-from-url', status_code=status.HTTP_204_NO_CONTENT)
async def auth(dto: TokenFromUrlDTO, response: Response):
    global broadcaster

    # Try to store and use token
    token_valid = True
    try:
        twitch.token_from_fragment(dto.url)
        resp = twitch.get('https://api.twitch.tv/helix/users')
        if resp.ok:
            parsed = resp.json()
            broadcaster = parsed['data'][0]
        elif resp.status_code == 401:
            token_valid = False
    except Exception as e:
        logger.error('Failed to get current user from Twitch API')
        logger.error(e)
        token_valid = False

    if not token_valid:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return

    await sio.emit('join', f'streamer:{broadcaster["login"]}')

    # Complete reward manager configuration
    rm.set_broadcaster_id(broadcaster["id"])
    rm.set_session(twitch)

    modified = False
    try:
        modified = rm.setup_rewards(cc.rewards)
    except RewardManagerError as e:
        logger.critical(str(e))
        sleep_sigterm()

    if modified:
        dump_client_config(cc)

    # Run subscription setup separately so errors here don't stop us from updating the client config
    try:
        rm.subscribe_to_redemptions()
    except RewardManagerError as e:
        logger.critical(str(e))
        sleep_sigterm()

    logger.info('Setup complete, listening for redemptions')


@sio.event
async def connect():
    logger.info('Connection to socket.io server established')

    # Rejoin redemption announcement room if broadcaster is already set
    if broadcaster.get('login') is not None:
        await sio.emit('join', f'streamer:{broadcaster["login"]}')


@sio.on('redemption')
async def on_message(data):
    logger.debug('Received channel point redemption', data)
    fulfilled = False
    redemption_id = data.get('id')
    reward_id = data.get('reward_id')
    reward = next((r for r in cc.rewards if r.id == reward_id), None)
    active_game = gameDetector.get_active_game()
    if reward is not None and active_game is not None:
        action = reward.actions.get(active_game)
        if action is not None and action.type is RewardActionType.KEYPRESS:
            logger.info(f'Pressing key for reward redemption ({action.value})')
            fulfilled = pydirectinput.press([str(action.value)])
            if not fulfilled:
                logger.error('Keypress failed')
    elif reward is not None and active_game is None:
        logger.info('Received redemption while game window was not active, skipping')

    """
    If auto fulfilling/refunding is enabled or no action was taken, update redemption status via Twitch API to
    a) fulfilled, if action was triggered and refunding is not forced
    b) canceled, if no action was taken or refunding is forced (will refund points to user)
    """
    if cc.auto_fulfill or cc.refund or not fulfilled:
        try:
            rm.update_redemption_status(
                redemption_id,
                reward_id,
                fulfilled and not cc.refund
            )
        except RewardManagerError as e:
            logger.error(str(e))


@sio.event
def connect_error(data):
    logger.error('Connection to 0xqwerty server failed!')


@sio.event
async def disconnect():
    logger.warning('Disconnected from 0xqwerty server')


if __name__ == '__main__':
    lc = load_logging_config()
    logging.config.dictConfig(lc)

    cc = load_client_config()

    logger.setLevel(cc.log_level)

    uvicorn.run(
        app,
        host=config.LISTEN_ADDR,
        port=config.LISTEN_PORT,
        log_config=lc
    )
