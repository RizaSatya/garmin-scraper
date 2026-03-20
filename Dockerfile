FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY garmin_sync ./garmin_sync
COPY sql ./sql

RUN pip install --no-cache-dir .

RUN useradd --create-home --uid 10001 appuser

USER appuser

CMD ["garmin-sync"]
