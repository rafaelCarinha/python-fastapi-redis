from celery import Celery
from app.services.tao_staking_service import fetch_tao_dividends, stake_tao, unstake_tao
from app.services.sentiment_analysis_service import analyze_sentiment

celery_app = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)


@celery_app.task
def analyze_sentiment_and_execute(netuid: int, hotkey: str):
    sentiment_score = analyze_sentiment(netuid)
    stake_amount = 0.01 * abs(sentiment_score)

    if sentiment_score > 0:
        stake_tao(hotkey, netuid, stake_amount)
    else:
        unstake_tao(hotkey, netuid, stake_amount)

    return {"hotkey": hotkey, "netuid": netuid, "sentiment_score": sentiment_score, "stake_amount": stake_amount}