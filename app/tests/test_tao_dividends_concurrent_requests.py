import os
import pytest
import asyncio
from httpx import AsyncClient, Limits
from unittest.mock import patch
from dotenv import load_dotenv
from fastapi import status

from ..main import app

# Load environment variables from .env
load_dotenv()

# Mock or Set Environment Variables
DEFAULT_NETUID = int(os.environ.get("DEFAULT_NETUID"))
DEFAULT_HOTKEY = os.environ.get("DEFAULT_HOTKEY")
VALID_AUTH_TOKEN = os.environ.get("AUTH_TOKEN")
INVALID_AUTH_TOKEN = "invalid_token"


# Semaphore to limit the number of concurrent requests
semaphore = asyncio.Semaphore(100)  # Allow up to 100 concurrent requests

limits = Limits(max_connections=100, max_keepalive_connections=50)


async def single_request(client, params, headers):
    """
    Helper function to send a single request.
    Uses a semaphore to limit concurrency.
    """
    async with semaphore:
        response = await client.get("/api/v1/tao_dividends", params=params, headers=headers)
        assert response.status_code == 200
        json_response = response.json()
        assert "cached" in json_response
        assert "data" in json_response


@pytest.mark.asyncio
async def test_tao_dividends_concurrent_requests():
    """
    Test 1000 simultaneous requests with a concurrency control.
    """
    params = {
        "netuid": DEFAULT_NETUID,
        "hotkey": DEFAULT_HOTKEY,
        "trade": False
    }
    headers = {
        "Authorization": f"Bearer {VALID_AUTH_TOKEN}"
    }

    # AsyncClient with increased limits
    async with AsyncClient(base_url="http://localhost:8000", limits=limits) as client:
        # Generate 1000 tasks, using the semaphore for concurrency
        tasks = [single_request(client, params, headers) for _ in range(1000)]
        await asyncio.gather(*tasks)
