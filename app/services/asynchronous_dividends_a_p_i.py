# Updated imports
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from redis import Redis
from celery.result import AsyncResult
import os
import json
from worker import celery_app
from tao_staking_service import fetch_tao_dividends
from cache_utilities import get_cached_data, set_cache

# Initialize FastAPI application
app = FastAPI(title="Asynchronous Dividends API")
redis_client = Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379))
)

# Bearer token authentication
security = HTTPBearer()


@app.get("/api/v1/tao_dividends")
async def tao_dividends(
        netuid: int = Query(os.getenv("DEFAULT_NETUID"), description="Netuid of the blockchain"),
        hotkey: str = Query(os.getenv("DEFAULT_HOTKEY"),
                            description="Hotkey for the account"),
        trade: bool = Query(False, description="Trigger sentimental staking"),
        token: HTTPAuthorizationCredentials = Depends(security),
):
    # Validate Bearer Token
    if token.credentials != os.getenv("AUTH_TOKEN", "your_bearer_token"):
        raise HTTPException(status_code=401, detail="Invalid or missing token")

    # Check cache
    cache_key = f"{netuid}:{hotkey}"
    cached_data = get_cached_data(redis_client, cache_key)
    if cached_data:
        return {"cached": True, "data": cached_data}

    # Query Tao Dividends & Cache
    try:
        dividends = await fetch_tao_dividends(netuid, hotkey)
        cache_ttl = int(os.getenv("CACHE_TTL", 120))
        set_cache(redis_client, cache_key, dividends, ttl=cache_ttl)

        # Trigger sentiment tasks if trade=True
        if trade:
            task = celery_app.send_task("tasks.analyze_sentiment_and_execute", args=(netuid, hotkey))
            return {"cached": False, "data": dividends, "task_id": task.id}

        return {"cached": False, "data": dividends}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))