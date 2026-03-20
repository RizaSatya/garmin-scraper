# Garmin Sync

Python job for syncing Garmin Connect data into PostgreSQL for Grafana dashboards.

## Environment variables

Use placeholders like these for now:

```bash
GARMIN_EMAIL=
GARMIN_PASSWORD=
GARMIN_ACCOUNT_KEY=personal
DATABASE_URL=postgresql://
TIMEZONE=Asia/Jakarta
SYNC_DAYS=7
FERNET_KEY=
```

## Run

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
garmin-sync
```
