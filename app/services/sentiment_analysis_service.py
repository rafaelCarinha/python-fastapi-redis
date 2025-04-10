import requests
import os

from dotenv import load_dotenv
import logging

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set log level to INFO (change to DEBUG for more detailed logs)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def analyze_sentiment(netuid: int):
    # Fetch tweets using Datura.ai API
    datura_api_key = os.environ.get("DATURA_API_KEY")
    tweets = requests.get(f"https://datura.ai/api/v1/twitter/search?query=Bittensor+netuid+{netuid}",
                          headers={"Authorization": f"Bearer {datura_api_key}"}).json()

    # Analyze sentiment with Chutes.ai
    chutes_api_key = os.environ.get("CHUTES_API_KEY")
    sentiment_response = requests.post(
        "https://api.chutes.ai/sentiment",
        json={"tweets": tweets},
        headers={"Authorization": f"cpk_{chutes_api_key}"}
    )

    sentiment_score = sentiment_response.json().get("score", 0)
    return sentiment_score