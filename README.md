# Garmin Sync

Python job for syncing Garmin Connect data into PostgreSQL for Grafana dashboards.

## Environment variables

The script will automatically read a file named `.env` from the project root.

Use placeholders like these for now:

```bash
GARMIN_EMAIL=
GARMIN_PASSWORD=
GARMIN_ACCOUNT_KEY=personal  # optional, defaults to personal
DATABASE_URL=postgresql://
TIMEZONE=Asia/Jakarta
SYNC_DAYS=7
BACKFILL_START_DATE=
BACKFILL_END_DATE=
FERNET_KEY=
```

For a one-off September 2025 backfill, set:

```bash
BACKFILL_START_DATE=2025-09-01
BACKFILL_END_DATE=2025-09-30
```

If those two vars are set, the script uses that exact inclusive date range instead of the normal rolling `SYNC_DAYS` window.

## Run

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
garmin-sync
```

## Database setup

If you want to apply the checked-in schema file directly:

```bash
psql "$DATABASE_URL" -f sql/schema.sql
```
