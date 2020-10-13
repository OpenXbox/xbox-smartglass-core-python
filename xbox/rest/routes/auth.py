from typing import Optional
from fastapi import APIRouter
from http import HTTPStatus
from xbox.webapi.authentication.manager import AuthenticationManager

router = APIRouter()


@router.get('/')
def authentication_overview():
    tokens = {
        'access_token': app.authentication_mgr.access_token,
        'refresh_token': app.authentication_mgr.refresh_token,
        'user_token': app.authentication_mgr.user_token,
        'xsts_token': app.authentication_mgr.xsts_token
    }

    data = {}
    for k, v in tokens.items():
        data.update({k: v.to_dict() if v else None})
    userinfo = app.authentication_mgr.userinfo.to_dict() if app.authentication_mgr.userinfo else None

    return app.success(tokens=data, userinfo=userinfo, authenticated=app.authentication_mgr.authenticated)


@router.get('/login')
async def authentication_login():
    pass


@router.get('/callback')
async def authentication_login_post(
    code: str,
    error: str,
    state: Optional[str]
):
    pass