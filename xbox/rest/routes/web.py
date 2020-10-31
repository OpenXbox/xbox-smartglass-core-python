from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from ..deps import get_xbl_client

from xbox.webapi.api.client import XboxLiveClient
from xbox.webapi.api.provider.titlehub import TitleFields
from xbox.webapi.api.provider.titlehub import models as titlehub_models
from xbox.webapi.api.provider.lists import models as lists_models

router = APIRouter()


@router.get('/title/{title_id}', response_model=titlehub_models.Title)
async def download_title_info(
    client: XboxLiveClient = Depends(get_xbl_client),
    *,
    title_id: int
):
    if not client:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='You have to login first')

    try:
        resp = await client.titlehub.get_title_info(title_id, [TitleFields.IMAGE])
        return resp.titles[0]
    except KeyError:
        raise HTTPException(status_code=404, detail='Cannot find titles-node json response')
    except IndexError:
        raise HTTPException(status_code=404, detail='No info for requested title not found')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Download of titleinfo failed, error: {e}')


@router.get('/titlehistory', response_model=titlehub_models.TitleHubResponse)
async def download_title_history(
    client: XboxLiveClient = Depends(get_xbl_client),
    max_items: Optional[int] = 5
):
    if not client:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='You have to login first')

    try:
        resp = await client.titlehub.get_title_history(client.xuid, max_items=max_items)
        return resp
    except Exception as e:
        return HTTPException(status_code=400, detail=f'Download of titlehistory failed, error: {e}')


@router.get('/pins', response_model=lists_models.ListsResponse)
async def download_pins(
    client: XboxLiveClient = Depends(get_xbl_client)
):
    if not client:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='You have to login first')

    try:
        resp = await client.lists.get_items(client.xuid)
        return resp
    except Exception as e:
        return HTTPException(status_code=400, detail=f'Download of pins failed, error: {e}')
