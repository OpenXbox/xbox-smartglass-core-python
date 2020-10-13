from typing import Optional

from fastapi import APIRouter, Depends
from ..deps import require_authentication

router = APIRouter()

@router.get('/title/<title_id>')
def download_title_info(
    client = Depends(require_authentication),
    *,
    title_id: int
):
    try:
        resp = client.titlehub.get_title_info(title_id, 'image').json()
        return jsonify(resp['titles'][0])
    except KeyError:
        return app.error('Cannot find titles-node json response')
    except IndexError:
        return app.error('No info for requested title not found')
    except Exception as e:
        return app.error('Download of titleinfo failed, error: {0}'.format(e))


@router.get('/titlehistory')
def download_title_history(
    client = Depends(require_authentication),
    max_items: Optional[int] = 5
):
    try:
        resp = client.titlehub.get_title_history(app.xbl_client.xuid, max_items=max_items).json()
        return jsonify(resp)
    except Exception as e:
        return app.error('Download of titlehistory failed, error: {0}'.format(e))


@router.get('/pins')
async def download_pins(
    client = Depends(require_authentication)
):
    try:
        resp = client.lists.get_items(app.xbl_client.xuid, {}).json()
        return await resp.json()
    except Exception as e:
        return app.error('Download of pins failed, error: {0}'.format(e))
