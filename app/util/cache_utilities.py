import json
import logging

from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set log level to INFO (change to DEBUG for more detailed logs)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)  # Use module-level logging


def get_cached_data(redis_client, key):
    """
    Retrieve data from the cache. If no data exists for the key, return None.
    """
    try:
        value = redis_client.get(key)
        if value:
            logger.info("Cache hit for key: '%s'", key)
            return json.loads(value)
        else:
            logger.info("Cache miss for key: '%s'", key)
            return None
    except Exception as e:
        logger.error("Error retrieving cache for key: '%s'. Error: %s", key, str(e))
        return None


def set_cache(redis_client, key, data, ttl: int = 120):
    """
    Set data into the cache with a given TTL (time-to-live).
    """
    try:
        redis_client.setex(key, ttl, json.dumps(data))
        logger.info("Cache set for key: '%s' with TTL: %d seconds", key, ttl)
    except Exception as e:
        logger.error("Error setting cache for key: '%s'. Data: '%s'. Error: %s",
                     key, data, str(e))