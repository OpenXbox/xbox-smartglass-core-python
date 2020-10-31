import secrets
import aiohttp

from typing import Optional
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import RedirectResponse

from .. import singletons, schemas
from ..common import generate_authentication_status, generate_authentication_manager

from xbox.webapi.scripts import CLIENT_ID, CLIENT_SECRET
from xbox.webapi.api.client import XboxLiveClient

router = APIRouter()


@router.get('/', response_model=schemas.AuthenticationStatus)
def authentication_overview():
    if not singletons.authentication_manager:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='You have to login first')

    return generate_authentication_status(singletons.authentication_manager)


@router.get('/login', status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def xboxlive_login(
    client_id: str = CLIENT_ID,
    client_secret: Optional[str] = CLIENT_SECRET,
    redirect_uri: str = 'http://localhost:5557/auth/callback',
    scopes: str = 'Xboxlive.signin,Xboxlive.offline_access'
):
    if scopes:
        scopes = scopes.split(',')

    auth_session_config = schemas.AuthSessionConfig(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scopes=scopes
    )

    # Create local instance of AuthenticationManager
    # -> Final instance will be created and saved in the
    #    callback route
    auth_mgr = generate_authentication_manager(auth_session_config)

    # Generating a random state to transmit in the authorization url
    session_state = secrets.token_hex(10)
    # Storing the state/session config so it can be retrieved
    # in the callback function
    singletons.auth_session_configs.update({session_state: auth_session_config})

    authorization_url = auth_mgr.generate_authorization_url(state=session_state)
    return RedirectResponse(authorization_url)


@router.get('/callback', status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def xboxlive_login_callback(
    code: str,
    state: str,
    error: Optional[str] = None
):
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    elif not code or not state:
        parameter_name = 'Code' if not code else 'State'
        error_detail = f'{parameter_name} missing from authorization callback'
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_detail)

    # Get auth session config that was set previously when
    # generating authorization redirect
    auth_session_config = singletons.auth_session_configs.get(state)
    if not auth_session_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Auth session config for state \'{state}\' not found'
        )

    # Construct authentication manager that will be cached
    auth_mgr = generate_authentication_manager(
        auth_session_config,
        singletons.http_session
    )
    await auth_mgr.request_tokens(code)

    singletons.authentication_manager = auth_mgr
    singletons.xbl_client = XboxLiveClient(singletons.authentication_manager)
    return RedirectResponse(url='/auth')


@router.get('/refresh', status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def refresh_tokens():
    if not singletons.authentication_manager:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='You have to login first')

    async with aiohttp.ClientSession() as http_session:
        singletons.authentication_manager.session = http_session
        singletons.authentication_manager.oauth = await singletons.authentication_manager.refresh_oauth_token()
        singletons.authentication_manager.user_token = await singletons.authentication_manager.request_user_token()
        singletons.authentication_manager.xsts_token = await singletons.authentication_manager.request_xsts_token()

    return RedirectResponse(url='/auth')


@router.get('/logout', response_model=schemas.GeneralResponse)
async def xboxlive_logout():
    singletons.authentication_manager = None
    return schemas.GeneralResponse(success=True)
