import os

ROOT_DIR = os.path.dirname(__file__).replace('\\src', '')
PWD = os.getcwd()

LISTEN_ADDR = '127.0.0.1'
LISTEN_PORT = 8000
BASE_URL = f'http://localhost:{LISTEN_PORT}'
REDIRECT_URI = f'{BASE_URL}/s/auth-callback'
TWITCH_AUTH_BASE_URL = 'https://id.twitch.tv/oauth2/authorize'
CLIENT_ID = 'jzaeeic6j23u0l2onzm2orovs0uakl'
SCOPES = ['channel:read:redemptions', 'channel:manage:redemptions']

QWERTY_API_BASE_URL = 'https://0xqwerty-api.cetteup.com'
