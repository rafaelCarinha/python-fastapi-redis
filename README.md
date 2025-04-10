## Start Redis
```brew services start redis```

## Install Bittensor (Downgrade Fast API to 0.110.1 for compatibility)
```uv add "bittensor @ git+https://github.com/opentensor/bittensor```

## Install BitTensor CLI
```pip install bittensor-cli==9.1.0```

## Create a New Wallet
```btcli new_wallet --wallet_name=default```

## Install Pytest
```uv add pytest pytest-asyncio httpx```

## Test Main Endpoint
```cd app```
```pytest -v```

## Run Docker
```docker compose up --build```

## Run Fast API
```uvicorn main:app --host 0.0.0.0 --port 8000```