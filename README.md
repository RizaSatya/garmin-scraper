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

## Docker image

Replace `your-registry/garmin-sync:latest` with the image name you actually publish.

```bash
docker build -t your-registry/garmin-sync:latest .
docker push your-registry/garmin-sync:latest
```

## Kubernetes

This manifest expects a Kubernetes cluster that supports `CronJob.spec.timeZone`.
Create the secret and apply the manifest in the same namespace where you want the CronJob to run.

Create the secret:

```bash
kubectl create secret generic garmin-sync-secrets \
  --from-literal=GARMIN_EMAIL=... \
  --from-literal=GARMIN_PASSWORD=... \
  --from-literal=DATABASE_URL=... \
  --from-literal=FERNET_KEY=...
```

Apply the CronJob:

```bash
kubectl apply -f k8s/garmin-sync-cronjob.yaml
```
