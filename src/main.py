import logging
import os
import webbrowser

import uvicorn
from fastapi import FastAPI, Response, status
from fastapi.requests import Request
from fastapi.responses import PlainTextResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_utils.tasks import repeat_every
from oauthlib.oauth2 import MobileApplicationClient
from requests_oauthlib import OAuth2Session

import config

app = FastAPI(title='twitch-channel-point-commander')
currentUser = {}
twitch = OAuth2Session(client=MobileApplicationClient(client_id=config.CLIENT_ID),
                       redirect_uri=config.REDIRECT_URI, scope=config.SCOPES)
# Client ID header is not sent by default, so just manually add it to the headers
twitch.headers['Client-Id'] = config.CLIENT_ID

app.mount('/static', StaticFiles(directory=os.path.join(config.ROOT_DIR, 'static'), html=True), name='static')
templates = Jinja2Templates(directory=os.path.join(config.ROOT_DIR, 'templates'))


@app.on_event('startup')
async def prompt_auth():
    authorization_url, state = twitch.authorization_url(config.TWITCH_AUTH_BASE_URL)
    webbrowser.open(authorization_url)


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
            await check_redemptions()
        elif resp.status_code == 401:
            token_valid = False
    except Exception as e:
        logging.error(e)
        token_valid = False

    if not token_valid:
        response.status_code = status.HTTP_401_UNAUTHORIZED

    return token_valid


@repeat_every(seconds=5 * 60)
async def check_redemptions():
    global currentUser

    try:
        resp = twitch.get('https://api.twitch.tv/helix/channel_points/custom_rewards/redemptions',
                          params={'broadcaster_id': currentUser.get('id')})
        if resp.status_code == 200:
            print(resp.json())
        else:
            logging.warning(f'Failed')
    except Exception:
        logging.error(f'Failed')


if __name__ == '__main__':
    uvicorn.run(app, host=config.LISTEN_ADDR, port=config.LISTEN_PORT)
