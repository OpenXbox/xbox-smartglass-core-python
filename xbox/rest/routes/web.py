from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from ..deps import require_xbl_client

from xbox.webapi.api.client import XboxLiveClient
from xbox.webapi.api.provider.titlehub import models as titlehub_models
from xbox.webapi.api.provider.lists import models as lists_models

router = APIRouter()

@router.get('/title/<title_id>', response_model=titlehub_models.Title)
async def download_title_info(
    client: XboxLiveClient = Depends(require_xbl_client),
    *,
    title_id: int
):
    try:
        resp = await client.titlehub.get_title_info(title_id, 'image')
        return resp.titles[0]
    except KeyError:
        raise HTTPException(status_code=404, detail='Cannot find titles-node json response')
    except IndexError:
        raise HTTPException(status_code=404, detail='No info for requested title not found')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Download of titleinfo failed, error: {e}')


@router.get('/titlehistory', response_model=titlehub_models.TitleHubResponse)
async def download_title_history(
    client: XboxLiveClient = Depends(require_xbl_client),
    max_items: Optional[int] = 5
):
    try:
        resp = await client.titlehub.get_title_history(app.xbl_client.xuid, max_items=max_items)
        return resp
    except Exception as e:
        return HTTPException(status_code=400, detail=f'Download of titlehistory failed, error: {e}')


@router.get('/pins', response_model=lists_models.ListsResponse)
async def download_pins(
    client: XboxLiveClient = Depends(require_xbl_client)
):
    try:
        resp = await client.lists.get_items(app.xbl_client.xuid, {})
        return resp
    except Exception as e:
        return HTTPException(status_code=400, detail=f'Download of pins failed, error: {e}')
