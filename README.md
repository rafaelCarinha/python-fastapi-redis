## Project Overview
This project provides a sentiment-based automated staking system leveraging Celery tasks, sentiment analysis, MongoDB persistence, and Redis queueing. Here’s what the system does:
- **Sentiment Analysis:**
Regularly analyzes sentiment using inputs identified by `netuid`. A sentiment scoring service determines positive or negative sentiments based on external data.
- **Automated TAO Stake/Unstake Logic:**
Based on sentiment score:
    - **Positive Sentiments** trigger automated staking operations (`stake_tao`).
    - **Negative Sentiments** trigger automated unstaking operations (`unstake_tao`).

- **Celery Integration:**
Uses Celery for asynchronous task queuing, scheduling, and execution. Redis is employed as both the broker and backend to handle concurrent task processing efficiently.
- **MongoDB Persistence:**
Stores task execution results, sentiment data, operation type (stake/unstake), and related metadata persistently in a MongoDB database for transparency and historical data retrieval.
- **Logging and Monitoring:**
Logs detailed execution information, error reports, and state changes using standard Python logging, facilitating easier debugging, operational monitoring, and maintenance.


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

MONGO_URI=mongodb://mongo:27017
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

## Query the MongoDB 

### Install mongosh
```uv add mongosh```
### Run mongosh
```mongosh```
### Change the Database
```use db```
### Query the sentiment_collection
```db.sentiment_collection.find()```
