from fastapi import FastAPI

from http import HTTPStatus
from xbox.webapi.authentication.manager import AuthenticationManager
from xbox.webapi.api.client import XboxLiveClient

from .api import api_router

app = FastAPI(title='SmartGlass REST server')

app.include_router(api_router)