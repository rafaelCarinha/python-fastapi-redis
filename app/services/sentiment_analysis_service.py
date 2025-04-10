import os
import logging

import aiohttp
import requests

from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set log level to INFO (change to DEBUG for more detailed logs)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)  # Use module-level logger


def analyze_sentiment(netuid: int):
    """
    Analyze sentiment for tweets related to a given netuid.
    :param netuid: The netuid to analyze sentiment for.
    :return: The sentiment score (default to 0 if unavailable).
    """

    logger.info("Starting sentiment analysis for NetUID: %d", netuid)

    # Fetch tweets using Datura.ai API
    datura_api_key = os.environ.get("DATURA_API_KEY")
    if not datura_api_key:
        logger.error("DATURA_API_KEY environment variable is not set.")
        return 0

    try:
        logger.info("Fetching tweets for NetUID: %d from Datura.ai.", netuid)
        response = requests.get(
            f"https://apis.datura.ai/twitter",
            headers={"Authorization": f"Bearer {datura_api_key}"},
            params={"query": f"Bittensor netuid {netuid}"}
        )
        if response.status_code != 200:
            logger.error("Failed to fetch tweets from Datura.ai. Status code: %d, Response: %s",
                         response.status_code, response.text)
            return 0
        tweets = response.json()
        logger.info("Successfully fetched tweets for NetUID: %d. Number of tweets: %d",
                    netuid, len(tweets))
    except Exception as e:
        logger.error("Error fetching tweets from Datura.ai for NetUID: %d. Error: %s", netuid, str(e))
        return 0


    # Analyze sentiment with Chutes.ai
    """Send a list of tweets for sentiment analysis to Chutes.ai."""
    chutes_api_key = os.environ.get("CHUTES_API_KEY")
    if not chutes_api_key:
        logger.error("CHUTES_API_KEY environment variable is not set.")
        return 0

    # Define API request details
    url = "https://llm.chutes.ai/v1/completions"
    headers = {
        "Authorization": "Bearer " + chutes_api_key,
        "Content-Type": "application/json"  # Explicit Content-Type header
    }
    body = {
        "model": "unsloth/Llama-3.2-3B-Instruct",
        "prompt": f"From the following tweets: {tweets}, please provide a sentiment score between (-100 to +100).",
        "stream": False,
        "max_tokens": 1024,
        "temperature": 0.7
    }

    try:
        logger.info("Sending tweets for sentiment analysis to Chutes.ai.")
        # Send the POST request synchronously
        response = requests.post(url, headers=headers, json=body)

        # Check for a successful response
        if response.status_code == 200:
            result = response.json()  # Extract JSON response
            sentiment_score = result.get("score", 0)  # Extract sentiment score
            logger.info(
                "Successfully analyzed sentiment for NetUID: %d. Sentiment score: %f",
                netuid, sentiment_score
            )
            return sentiment_score
        else:
            # Handle API errors with logging
            logger.error(
                "Failed to analyze sentiment with Chutes.ai. "
                "Status code: %d, Response: %s",
                response.status_code, response.text
            )
            return 0
    except Exception as e:
        # Log unexpected exceptions
        logger.error(
            "Error analyzing sentiment with Chutes.ai for NetUID: %d. Error: %s",
            netuid, str(e)
        )
        return 0
