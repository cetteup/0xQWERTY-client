import uuid
import urllib.parse

from typing import Tuple

from src import config


def get_auth_url() -> Tuple[str, str]:
    state = str(uuid.uuid4())
    params = {
        'client_id': config.CLIENT_ID,
        'redirect_uri': config.REDIRECT_URI,
        'response_type': 'token',
        'scope': " ".join(config.SCOPES),
        'state': state
    }
    return f'{config.TWITCH_AUTH_BASE_URL}?{urllib.parse.urlencode(params)}', state
