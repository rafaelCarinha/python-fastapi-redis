# Docker instructions for containerizing FastAPI
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN pip install fastapi uvicorn
RUN pip install celery[redis]
RUN pip install bittensor
RUN pip install python-dotenv

COPY . .

CMD ["uvicorn", "app.main:app", "workers", "4", "--host", "0.0.0.0", "--port", "8000", "--log-level", "debug"]