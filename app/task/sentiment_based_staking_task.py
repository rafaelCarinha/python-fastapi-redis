import os
from celery import Celery
from app.services.tao_staking_service import stake_tao, unstake_tao
from app.services.sentiment_analysis_service import analyze_sentiment
from app.db.mongo_persistence import persist_sentiment_data  # Import persistence layer
import asyncio

from dotenv import load_dotenv
import logging

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get Redis host and port from environment variables
redis_host = os.environ.get("REDIS_HOST")
redis_port = os.environ.get("REDIS_PORT")

# Build the broker and backend URLs dynamically
broker_url = f"redis://{redis_host}:{redis_port}/0"
backend_url = f"redis://{redis_host}:{redis_port}/0"

# Initialize Celery app
celery_app = Celery(
    "tasks",
    broker=broker_url,
    backend=backend_url
)


@celery_app.task
def analyze_sentiment_and_execute(netuid: int, hotkey: str):
    logger.info(f"Task started: Analyzing sentiment and executing actions for hotkey={hotkey}, netuid={netuid}")

    try:
        # Analyze sentiment
        sentiment_score = analyze_sentiment(netuid)
        logger.info(f"Sentiment analysis completed: netuid={netuid}, sentiment_score={sentiment_score}")

        # Determine stake amount
        stake_amount = 0.01 * abs(sentiment_score)
        logger.info(f"Calculated stake amount: {stake_amount}")

        # Execute staking or unstaking based on sentiment
        if sentiment_score > 0:
            logger.info(f"Positive sentiment detected. Staking {stake_amount} for hotkey={hotkey} on netuid={netuid}")
            result = stake_tao(hotkey, netuid, stake_amount)
            operation = "stake"
        else:
            logger.info(f"Negative sentiment detected. Unstaking {stake_amount} for hotkey={hotkey} on netuid={netuid}")
            result = unstake_tao(hotkey, netuid, stake_amount)
            operation = "unstake"

        logger.info(f"Task completed successfully for hotkey={hotkey}, netuid={netuid}. Response: {result}")

        # Async MongoDB persistence
        persisted_data = {
            "netuid": netuid,
            "hotkey": hotkey,
            "sentiment_score": sentiment_score,
            "operation": operation,
            "stake_amount": stake_amount,
            "result": result
        }

        # Ensure event loop integration for asynchronous operation
        asyncio.run(persist_sentiment_data(persisted_data))
        logger.info(f"Persisted result to MongoDB for hotkey={hotkey}, netuid={netuid}")

        return result

    except Exception as e:
        logger.error(f"An error occurred while processing hotkey={hotkey}, netuid={netuid}. Error: {e}", exc_info=True)
        raise
