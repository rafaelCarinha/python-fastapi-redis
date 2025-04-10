## Environment Variables

### Example `.env` File

Below is an example of how these variables can be stored in a `.env` file:

```bash
DATURA_API_KEY=
CHUTES_API_KEY=

REDIS_HOST=localhost
REDIS_PORT=6379

AUTH_TOKEN=your_bearer_token

DEFAULT_NETUID=
DEFAULT_HOTKEY=

OPENTENSOR_URL=wss://entrypoint-finney.opentensor.ai:443

CACHE_TTL=120
```

Be sure to replace the placeholders with actual values when deploying or running the application in your local environment.

---


## Start Redis
```brew services start redis```

## Test Redis
```redis-cli -h localhost -p 6379 ping```

## Install Bittensor (Downgrade Fast API to 0.110.1 for compatibility)
```uv add "bittensor @ git+https://github.com/opentensor/bittensor```

## Install BitTensor CLI
```pip install bittensor-cli==9.1.0```

## Create a New Wallet
```btcli wallet new_coldkey --wallet.name default```

## Install Pytest
```uv add pytest pytest-asyncio httpx```

## Run via Docker
```docker compose up --build```

## Test Main Endpoint
```cd app```
```pytest -v```

## Check celery logs
```celery worker --loglevel=debug```

## Check Docker worker logs
```docker compose logs worker```
