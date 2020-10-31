from typing import Tuple, Optional
import aiohttp
from fastapi import Query, Header, HTTPException, status
from xbox.webapi.api.language import DefaultXboxLiveLanguages, XboxLiveLanguage

from . import singletons
from .common import generate_authentication_status
from .schemas.auth import AuthenticationStatus

from xbox.webapi.api.client import XboxLiveClient


def console_connected(liveid: str):
    console = singletons.console_cache.get(liveid)
    if not console:
        raise HTTPException(status_code=400, detail=f'Console {liveid} is not alive')
    elif not console.connected:
        raise HTTPException(status_code=400, detail=f'Console {liveid} is not connected')
    return console


def console_exists(liveid: str):
    console = singletons.console_cache.get(liveid)
    if not console:
        raise HTTPException(status_code=400, detail=f'Console info for {liveid} is not available')

    return console


async def get_xbl_client() -> Optional[XboxLiveClient]:
    return singletons.xbl_client


def get_authorization(
    anonymous: Optional[bool] = Query(default=True)
) -> Optional[AuthenticationStatus]:
    if anonymous:
        return None
    elif not singletons.authentication_manager:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Authorization data not available'
        )
    return generate_authentication_status(singletons.authentication_manager)
