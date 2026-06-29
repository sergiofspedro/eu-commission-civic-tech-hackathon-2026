FROM python:3.11-slim
WORKDIR /app
COPY voice-bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["gunicorn", "--bind", "0.0.0.0:8200", "--workers", "1", "--threads", "4", "app:app"]
