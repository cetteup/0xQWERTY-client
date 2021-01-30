import logging
import os
import webbrowser

import pyautogui
import socketio
import uvicorn
from fastapi import FastAPI, Response, status
from fastapi.requests import Request
from fastapi.responses import PlainTextResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from oauthlib.oauth2 import MobileApplicationClient
from requests_oauthlib import OAuth2Session

import config
from keyboard import auto_press_key
from helpers import update_redemption_status

app = FastAPI(title='twitch-channel-point-commander')
templates = Jinja2Templates(directory=os.path.join(config.ROOT_DIR, 'templates'))
sio = socketio.AsyncClient(reconnection_attempts=16, logger=True, engineio_logger=True)

currentUser = {}
twitch = OAuth2Session(client=MobileApplicationClient(client_id=config.CLIENT_ID),
                       redirect_uri=config.REDIRECT_URI, scope=config.SCOPES)
# Client ID header is not sent by default, so just manually add it to the headers
twitch.headers['Client-Id'] = config.CLIENT_ID


@app.on_event('startup')
async def prompt_auth():
    await sio.connect('https://qwerty-server.herokuapp.com')
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
    await sio.emit('join', 'streamer:lifebd')


@sio.on('redemption')
async def on_message(data):
    print('Channel points redeemed!', data)
    fulfilled = False
    redemption_id = data.get('id')
    reward_id = data.get('reward_id')
    if str(pyautogui.getActiveWindowTitle()).startswith('BF2 (v1.5.3153-802.0'):
        if reward_id == 'd63eef98-207f-4f48-8e60-ab6230c270af':
            print('pressing 1')
            auto_press_key(0x2)
        elif reward_id == 'b15e264d-e34f-4177-9abe-54191653fd5e':
            print('pressing space')
            auto_press_key(0x39)
        fulfilled = True
    else:
        print('Game window not active, skipping')

    await update_redemption_status(twitch, redemption_id, currentUser.get('id'), reward_id, fulfilled)


@sio.event
async def disconnect():
    print('disconnected from server')


if __name__ == '__main__':
    uvicorn.run(app, host=config.LISTEN_ADDR, port=config.LISTEN_PORT)
