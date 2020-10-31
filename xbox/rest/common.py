
import aiohttp
from xbox.webapi.authentication.manager import AuthenticationManager

from .schemas.auth import AuthenticationStatus, AuthSessionConfig

def generate_authentication_status(
    manager: AuthenticationManager
) -> AuthenticationStatus:
    return AuthenticationStatus(
        oauth=manager.oauth,
        xsts=manager.xsts_token,
        session_config=AuthSessionConfig(
            client_id=manager._client_id,
            client_secret=manager._client_secret,
            redirect_uri=manager._redirect_uri,
            scopes=manager._scopes
        )
    )

def generate_authentication_manager(
    session_config: AuthSessionConfig,
    http_session: aiohttp.ClientSession = None
) -> AuthenticationManager:
    return AuthenticationManager(
        client_session=http_session,
        client_id=session_config.client_id,
        client_secret=session_config.client_secret,
        redirect_uri=session_config.redirect_uri,
        scopes=session_config.scopes
    )