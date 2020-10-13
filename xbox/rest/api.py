from fastapi import APIRouter

from xbox.rest.routes import root, auth, device, web

api_router = APIRouter()

api_router.include_router(root.router, tags=["root"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(device.router, prefix="/device", tags=["device"])
api_router.include_router(web.router, prefix="/web", tags=["web"])