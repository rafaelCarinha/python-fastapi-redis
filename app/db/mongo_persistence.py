import os
import logging
import motor.motor_asyncio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MongoDB client
MONGO_URI = os.environ.get("MONGO_URI")

if not MONGO_URI:
    logger.error("Missing environment variable: MONGO_URI")
    raise EnvironmentError("MONGO_URI environment variable not set.")

try:
    mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
    db = mongo_client["db"]  # Customize this to your actual database name
    logger.info("Successfully connected to MongoDB.")
except Exception as e:
    logger.exception("Unable to connect to MongoDB: %s", e)
    raise


async def persist_sentiment_data(data: dict) -> str:
    """
    Persist sentiment data into the MongoDB collection.
    
    :param data: Sentiment data dictionary to persist
    :return: ID of the inserted document
    """
    collection = db["sentiment_collection"]
    try:
        result = await collection.insert_one(data)
        document_id = str(result.inserted_id)
        logger.info("Successfully inserted sentiment data with ID: %s", document_id)
        return document_id
    except Exception as e:
        logger.exception("Failed to insert sentiment data: %s", e)
        raise


async def persist_request_data(data: dict) -> str:
    """
    Persist request data into the MongoDB collection.

    :param data: Request data dictionary to persist
    :return: ID of the inserted document
    """
    collection = db["request_collection"]
    try:
        result = await collection.insert_one(data)
        document_id = str(result.inserted_id)
        logger.info("Successfully inserted request data with ID: %s", document_id)
        return document_id
    except Exception as e:
        logger.exception("Failed to insert request data: %s", e)
        raise