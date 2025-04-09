from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime

Base = declarative_base()


class StakeHistory(Base):
    __tablename__ = "stake_history"

    id = Column(Integer, primary_key=True, index=True)
    hotkey = Column(String, nullable=False)
    netuid = Column(Integer, nullable=False)
    action = Column(String, nullable=False)  # "stake" or "unstake"
    amount = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)