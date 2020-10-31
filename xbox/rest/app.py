from fastapi import FastAPI
import uvicorn
import aiohttp

from . import singletons
from .api import api_router

app = FastAPI(title='SmartGlass REST server')


@app.on_event("startup")
async def startup_event():
    singletons.http_session = aiohttp.ClientSession()


@app.on_event("shutdown")
async def shutdown_event():
    await singletons.http_session.close()


app.include_router(api_router)

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=5557)
