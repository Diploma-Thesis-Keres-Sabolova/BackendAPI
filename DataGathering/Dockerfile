FROM python:3.11-slim

WORKDIR /app

COPY DataGathering/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY DataGathering/ ./DataGathering

CMD ["python", "DataGathering/app.py"]
