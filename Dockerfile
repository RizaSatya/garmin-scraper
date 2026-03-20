FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY garmin_sync ./garmin_sync
COPY sql ./sql

RUN pip install --no-cache-dir .

CMD ["garmin-sync"]
