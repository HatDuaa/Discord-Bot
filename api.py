from concurrent.futures import ThreadPoolExecutor
from fastapi import Depends, FastAPI, APIRouter
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from discord_bot_libs.utils import log_request_time_async


app = FastAPI()


app.add_middleware(BaseHTTPMiddleware, dispatch=log_request_time_async)

# root_router = APIRouter(dependencies=[Depends(verify_access_token)])
root_router = APIRouter()





app.include_router(root_router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Hello Bigger Applications!"}

@app.get("/ping")
def root():
    return {"message": "Pong!"}


def run():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)


def keep_alive():
    with ThreadPoolExecutor(max_workers=2) as executor:
        logger.info("Starting FastAPI server in thread pool")
        future = executor.submit(run)
        try:
            future.result()
        except Exception as e:
            logger.error(f"Error in FastAPI server: {e}")

