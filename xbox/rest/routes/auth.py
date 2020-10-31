import secrets
import aiohttp

from typing import Optional, List
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import RedirectResponse
from http import HTTPStatus

from .. import singletons
from ..common import generate_authentication_status, generate_authentication_manager
from ..schemas.general import GeneralResponse
from ..schemas.auth import AuthenticationStatus, AuthSessionConfig


router = APIRouter()

@router.get('/')
def authentication_overview():
    if not singletons.authentication_manager:
        raise HTTPException(status_code=404, detail='Authorization not done')

    return generate_authentication_status(singletons.authentication_manager)


@router.get('/login', status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def xboxlive_login(
    client_id: str,
    client_secret: Optional[str],
    redirect_uri: str,
    scopes: List[str]
):
    auth_session_config = AuthSessionConfig(
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


@router.get('/callback', response_model=AuthenticationStatus)
async def xboxlive_login_callback(
    code: str,
    error: Optional[str],
    state: Optional[str]
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
    async with aiohttp.ClientSession() as http_session:
        auth_mgr = generate_authentication_manager(auth_session_config, http_session)
        await auth_mgr.refresh_tokens()
    
    authentication_manager = auth_mgr
    return generate_authentication_status(authentication_manager)

@router.get('/logout', response_model=GeneralResponse)
async def xboxlive_logout():
    authentication_manager = None
    return GeneralResponse(success=True)
