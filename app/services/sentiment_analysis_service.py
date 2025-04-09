import requests
import os


def analyze_sentiment(netuid: int):
    # Fetch tweets using Datura.ai API
    datura_api_key = os.getenv("DATURA_API_KEY", "default_datura_key")
    tweets = requests.get(f"https://datura.ai/api/v1/twitter/search?query=Bittensor+netuid+{netuid}",
                          headers={"Authorization": f"Bearer {datura_api_key}"}).json()

    # Analyze sentiment with Chutes.ai
    chutes_api_key = os.getenv("CHUTES_API_KEY", "default_chutes_key")
    sentiment_response = requests.post(
        "https://api.chutes.ai/sentiment",
        json={"tweets": tweets},
        headers={"Authorization": f"cpk_{chutes_api_key}"}
    )

    sentiment_score = sentiment_response.json().get("score", 0)
    return sentiment_score