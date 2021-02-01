import logging
import os
import re
import webbrowser

import pyautogui
import socketio
import uvicorn
import yaml
from fastapi import FastAPI, Response, status
from fastapi.requests import Request
from fastapi.responses import PlainTextResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from oauthlib.oauth2 import MobileApplicationClient
from requests_oauthlib import OAuth2Session

import config
from helpers import update_redemption_status
from keyboard import auto_press_key

app = FastAPI(title='0xQWERTY - an in-game keyboard for your viewers')
templates = Jinja2Templates(directory=os.path.join(config.ROOT_DIR, 'templates'))
sio = socketio.AsyncClient(reconnection_attempts=16, logger=True, engineio_logger=True)

games = {}
rewards = []
configuredGames = []
currentUser = {}
twitch = OAuth2Session(client=MobileApplicationClient(client_id=config.CLIENT_ID),
                       redirect_uri=config.REDIRECT_URI, scope=config.SCOPES)
# Client ID header is not sent by default, so just manually add it to the headers
twitch.headers['Client-Id'] = config.CLIENT_ID


@app.on_event('startup')
async def prompt_auth():
    global games, rewards, configuredGames

    with open(os.path.join(config.ROOT_DIR, 'games.yaml')) as f:
        games = yaml.safe_load(f)
    for key, game in games.items():
        games[key] = re.compile(game)

    with open(os.path.join(config.PWD, 'rewards.yaml')) as f:
        rewards = yaml.safe_load(f)
    configuredGames = list(set([key for r in rewards for key in r['actions'].keys()]))

    await sio.connect(config.QWERTY_API_BASE_URL)
    authorization_url, state = twitch.authorization_url(config.TWITCH_AUTH_BASE_URL)
    webbrowser.open(authorization_url)


@app.on_event('shutdown')
async def shutdown():
    await sio.disconnect()


@app.get('/s/auth-callback', response_class=HTMLResponse)
async def render_page(request: Request):
    return templates.TemplateResponse('auth-callback.html',
                                      {'request': request, 'app_name': app.title, 'base_url': config.BASE_URL})


@app.get('/s/dashboard', response_class=HTMLResponse)
async def render_page(request: Request):
    return templates.TemplateResponse('dashboard.html',
                                      {'request': request, 'app_name': app.title, 'base_url': config.BASE_URL})


@app.get('/a/auth-url', response_class=PlainTextResponse)
async def auth_url():
    authorization_url, state = twitch.authorization_url(config.TWITCH_AUTH_BASE_URL)
    return authorization_url


@app.get('/a/token-from-url', status_code=status.HTTP_200_OK)
async def auth(url: str, response: Response):
    global currentUser, twitch

    # Try to store and use token
    token_valid = True
    try:
        twitch.token_from_fragment(url)
        resp = twitch.get('https://api.twitch.tv/helix/users')
        if resp.status_code == 200:
            parsed = resp.json()
            currentUser = parsed['data'][0]
            await sio.emit('join', f'streamer:{currentUser.get("login")}')
        elif resp.status_code == 401:
            token_valid = False
    except Exception as e:
        logging.error('Failed to get current user from Twitch API')
        logging.error(e)
        token_valid = False

    if not token_valid:
        response.status_code = status.HTTP_401_UNAUTHORIZED

    return token_valid


@sio.event
async def connect():
    print('connection established')


@sio.on('redemption')
async def on_message(data):
    print('Channel points redeemed!', data)
    fulfilled = False
    redemption_id = data.get('id')
    reward_id = data.get('reward_id')
    reward = next((r for r in rewards if r['id'] == reward_id), None)
    active_window_title = str(pyautogui.getActiveWindowTitle())
    active_game = next(
        (key for key in games.keys() if key in configuredGames and games[key].match(active_window_title)),
        None
    )
    if reward is not None and active_game is not None:
        action = reward['actions'].get(active_game)
        if action.get('action_type') == 'keypress':
            print(f'Pressing {hex(action["action_value"])}')
            auto_press_key(action['action_value'])
        fulfilled = True
    elif reward is not None and active_game is None:
        print('Game window not active, skipping')

    await update_redemption_status(twitch, redemption_id, currentUser.get('id'), reward_id, fulfilled)


@sio.event
async def disconnect():
    print('disconnected from server')


if __name__ == '__main__':
    uvicorn.run(app, host=config.LISTEN_ADDR, port=config.LISTEN_PORT)
