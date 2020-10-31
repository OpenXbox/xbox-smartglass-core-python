from fastapi import FastAPI

from .api import api_router

app = FastAPI(title='SmartGlass REST server')
app.include_router(api_router)