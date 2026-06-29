FROM python:3.11-slim
WORKDIR /app
COPY telegram-bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "bot.py"]
