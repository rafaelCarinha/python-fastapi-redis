# Updated imports
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from redis import Redis
from celery.result import AsyncResult
import os
import json
from  app.services.sentiment_based_staking_task import celery_app
from app.services.tao_staking_service import fetch_tao_dividends
from app.services.cache_utilities import get_cached_data, set_cache

from dotenv import load_dotenv
import logging


load_dotenv()

# Configure the root logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Initialize FastAPI application
app = FastAPI(title="Asynchronous Dividends API")
redis_client = Redis(
    host=os.environ.get("REDIS_HOST"),
    port=int(os.environ.get("REDIS_PORT"))
)

# Bearer token authentication
security = HTTPBearer()


@app.get("/")
async def root():
    logger.info("Hello World Test")
    return {"message": "Hello World Test"}


@app.get("/api/v1/tao_dividends")
async def tao_dividends(
        netuid: int = Query(os.environ.get("DEFAULT_NETUID"), description="Netuid of the blockchain"),
        hotkey: str = Query(os.environ.get("DEFAULT_HOTKEY"),
                            description="Hotkey for the account"),
        trade: bool = Query(False, description="Trigger sentimental staking"),
        token: HTTPAuthorizationCredentials = Depends(security),
):
    # Validate Bearer Token
    logger.info(os.environ.get("AUTH_TOKEN"))
    if token.credentials != os.environ.get("AUTH_TOKEN"):
        print('Not Authenticated')
        raise HTTPException(status_code=401, detail="Invalid or missing token")

    # Check cache
    cache_key = f"{netuid}:{hotkey}"
    cached_data = get_cached_data(redis_client, cache_key)
    if cached_data:
        return {"cached": True, "data": cached_data}

    # Query Tao Dividends & Cache
    try:
        dividends = await fetch_tao_dividends(netuid, hotkey)
        cache_ttl = int(os.environ.get("CACHE_TTL"))
        set_cache(redis_client, cache_key, dividends, ttl=cache_ttl)

        # Trigger sentiment tasks if trade=True
        if trade:
            task = celery_app.send_task("tasks.analyze_sentiment_and_execute", args=(netuid, hotkey))
            return {"cached": False, "data": dividends, "task_id": task.id}

        return {"cached": False, "data": dividends}
    except Exception as e:
        logger.info(str(e))
        raise HTTPException(status_code=500, detail=str(e))