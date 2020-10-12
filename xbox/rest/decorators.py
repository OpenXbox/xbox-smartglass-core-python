from quart import current_app as app
from http import HTTPStatus
from functools import wraps

"""
Decorators
"""


def console_connected(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        liveid = kwargs.get('liveid')
        console = app.console_cache.get(liveid)
        if not console:
            return app.error('Console {0} is not alive'.format(liveid), HTTPStatus.FORBIDDEN)
        elif not console.connected:
            return app.error('Console {0} is not connected'.format(liveid), HTTPStatus.FORBIDDEN)

        del kwargs['liveid']
        kwargs['console'] = console
        return f(*args, **kwargs)
    return decorated_function


def console_exists(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        liveid = kwargs.get('liveid')
        console = app.console_cache.get(liveid)
        if not console:
            return app.error('Console info for {0} is not available'.format(liveid), HTTPStatus.FORBIDDEN)

        del kwargs['liveid']
        kwargs['console'] = console
        return f(*args, **kwargs)
    return decorated_function


def require_authentication(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not app.authentication_mgr.authenticated:
            return app.error('Not authenticated for Xbox Live', HTTPStatus.UNAUTHORIZED)

        kwargs['client'] = app.xbl_client
        return f(*args, **kwargs)
    return decorated_function
