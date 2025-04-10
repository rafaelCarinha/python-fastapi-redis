# Updated imports
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from redis import Redis
from celery.result import AsyncResult
import os
import json
from  app.services.sentiment_based_staking_task import celery_app
from app.services.tao_staking_service import fetch_tao_dividends, fetch_all_netuids, fetch_all_hotkeys_for_netuid
from app.services.cache_utilities import get_cached_data, set_cache

from dotenv import load_dotenv
import logging


load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set log level to INFO (change to DEBUG for more detailed logs)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
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
        netuid: int | None = None,
        hotkey: str | None = None,
        trade: bool = False,
        token: HTTPAuthorizationCredentials = Depends(security),
):
    # Validate Bearer Token
    logger.info("Validating the authorization token.")
    if token.credentials != os.environ.get("AUTH_TOKEN"):
        raise HTTPException(status_code=401, detail="Invalid or missing token")

    try:
        # Case 1: netuid is omitted, fetch all netuids and their hotkeys
        if netuid is None:
            logger.info("No netuid specified. Retrieving dividends for all netuids and hotkeys.")

            all_dividends = await fetch_all_netuids()
            return {"cached": False, "data": all_dividends}

        # Case 2: hotkey is omitted, fetch all hotkeys for the specified netuid
        if hotkey is None:
            logger.info("No hotkey specified. Retrieving dividends for all hotkeys under netuid=%s.", netuid)

            dividends_for_netuid = await fetch_all_hotkeys_for_netuid(netuid)
            return {"cached": False, "data": dividends_for_netuid}

        # Case 3: Both netuid and hotkey are specified
        logger.info(
            "Fetching dividends for netuid=%s and hotkey=%s.",
            netuid,
            hotkey
        )
        cache_key = f"{netuid}:{hotkey}"
        cached_data = get_cached_data(redis_client, cache_key)
        if cached_data:
            logger.info(
                "Cache hit for key: %s. Returning cached data with Cache status: True",
                cache_key,
            )
            return {"cached": True, "data": cached_data}

        # Fetch dividends and store in cache
        dividends = await fetch_tao_dividends(netuid, hotkey)
        cache_ttl = int(os.environ.get("CACHE_TTL"))  # Default TTL if not set
        set_cache(redis_client, cache_key, dividends, ttl=cache_ttl)

        # Optionally trigger a task if trade=True
        if trade:
            logger.info(
                "Trade flag is True. Triggering sentiment analysis task for netuid=%s, hotkey=%s.",
                netuid, hotkey,
            )
            task = celery_app.send_task("app.services.sentiment_based_staking_task.analyze_sentiment_and_execute", args=(netuid, hotkey))
            logger.info("Sentiment analysis task successfully triggered. Task ID: %s", task.id)

            return {"cached": False, "data": dividends, "task_id": task.id}

        return {"cached": False, "data": dividends}

    except Exception as e:
        logger.error(
            "An error occurred while processing the request: %s", str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")