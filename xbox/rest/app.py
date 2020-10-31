from fastapi import FastAPI
import uvicorn

from .api import api_router

app = FastAPI(title='SmartGlass REST server')
app.include_router(api_router)

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=5557)
