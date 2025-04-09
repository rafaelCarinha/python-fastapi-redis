## Start Redis
```brew services start redis```

## Install Bittensor (Downgrade Fast API to 0.110.1 for compatibility)
```uv add "bittensor @ git+https://github.com/opentensor/bittensor"
```

## Run Docker
```uvicorn main:app --host 0.0.0.0 --port 80```