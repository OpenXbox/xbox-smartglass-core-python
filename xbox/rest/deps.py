from typing import Tuple

from fastapi import Query, Header
from http import HTTPStatus

def console_connected(liveid: str):
    console = app.console_cache.get(liveid)
    if not console:
        return app.error('Console {0} is not alive'.format(liveid), HTTPStatus.FORBIDDEN)
    elif not console.connected:
        return app.error('Console {0} is not connected'.format(liveid), HTTPStatus.FORBIDDEN)
    return console


def console_exists(liveid: str):
    console = app.console_cache.get(liveid)
    if not console:
        return app.error('Console info for {0} is not available'.format(liveid), HTTPStatus.FORBIDDEN)

    return console


def require_authentication(
    auth_header: str = Header(default=None, alias='Authorization')
) -> Tuple[str, str]:
    return 'userhash', 'jwt'
