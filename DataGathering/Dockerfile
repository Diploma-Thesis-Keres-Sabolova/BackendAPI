FROM python:3.11-slim

WORKDIR /app

COPY DataGathering/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY DataGathering/ ./DataGathering

RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

COPY DataGathering/cron /etc/cron.d/data_gathering
RUN chmod 0644 /etc/cron.d/data_gathering
RUN crontab /etc/cron.d/data_gathering

RUN touch /var/log/data_gathering.log
RUN touch /var/log/cron.log

COPY .env /app/.env

CMD ["cron", "-f"]
