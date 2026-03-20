# Garmin to PostgreSQL Sync Design

## Goal

Build a simple Python job that uses `python-garminconnect` to fetch as much Garmin Connect data as is practical, stores it in PostgreSQL, and exposes Grafana-friendly tables for dashboards.

The job is intended to run as a Kubernetes job approximately every 30 minutes. It must be safe to run repeatedly, tolerate container restarts, and preserve Garmin authentication state across runs.

## Scope

This design covers:

- OAuth authentication through `python-garminconnect` and Garth
- Database-backed token storage with optional Fernet encryption
- Raw Garmin payload ingestion into PostgreSQL
- Curated analytics tables for Grafana
- Incremental sync behavior suitable for a frequent Kubernetes job
- The first implementation slice and its testing strategy

This design does not cover:

- Kubernetes manifests or Helm charts
- Grafana dashboard JSON or panel definitions
- Multi-account tenancy beyond a single logical `account_key`
- Historical backfill beyond the configurable rolling sync window

## Recommended Approach

Use a hybrid storage model:

- Store every fetched Garmin response in raw JSONB tables so schema drift and device-specific fields do not block ingestion.
- Project high-value, query-friendly metrics into flat curated tables for Grafana.

This approach is preferred over raw-only storage because Grafana queries become much simpler and more performant. It is preferred over fully normalized schemas because Garmin data is broad, device-dependent, and changes over time.

## Architecture

The system is a single Python entrypoint with four responsibilities:

1. Load configuration and establish PostgreSQL connectivity.
2. Load Garmin OAuth tokens from PostgreSQL, decrypt if needed, and initialize the Garmin client.
3. Fetch Garmin data for a rolling date window and recent activities.
4. Persist raw payloads and upsert curated analytics tables.

The code should be organized into focused units:

- `config`: reads environment variables and validates required settings
- `token_store`: loads and saves Garmin token bundles in PostgreSQL
- `garmin_client`: wraps `python-garminconnect` login and fetch calls
- `sync`: orchestrates endpoint fetches over the rolling window
- `repositories`: performs database upserts
- `mappers`: flattens raw Garmin payloads into curated rows
- `main`: wires dependencies together and sets exit codes

Each unit should be understandable in isolation and testable without the full application.

## Authentication Design

Authentication will use the supported Garmin OAuth flow from `python-garminconnect`, which relies on Garth and supports token reuse and automatic refresh.

### Token lifecycle

- On startup, the job reads the token bundle for a configured `account_key` from PostgreSQL.
- If the token bundle exists, it is decrypted when encryption is enabled and then loaded into the Garmin client.
- If no token bundle exists, the job performs initial login using Garmin credentials from environment variables.
- After any successful login or refresh, the latest token bundle is written back to PostgreSQL.

### Token persistence

Tokens are stored in PostgreSQL instead of the container filesystem so authentication survives pod and container restarts.

### Optional encryption

If `FERNET_KEY` is configured:

- token payloads are encrypted before being written to PostgreSQL
- token payloads are decrypted after being read from PostgreSQL
- token records are marked as encrypted

If `FERNET_KEY` is not configured:

- token payloads are stored as plain text for local development or simple deployments
- the storage format remains otherwise identical

### Failure behavior

- Invalid or expired tokens should trigger a re-authentication attempt only when credentials are available.
- If neither valid stored tokens nor bootstrap credentials are available, the job exits with a fatal authentication error.
- Token records are only updated after successful authentication or refresh.

## Sync Model

The Kubernetes job runs every 30 minutes, so the sync must be incremental and idempotent.

### Rolling sync window

Each run should fetch a configurable date range ending on the current local date. The default window should be:

- today
- the previous 7 days

This rolling fetch avoids missed updates when Garmin backfills or adjusts metrics after the initial day close.

### Activity sync

Activities should be fetched for the same rolling window and upserted by Garmin activity ID. If list responses do not contain all needed fields, the job should fetch per-activity detail for each activity discovered in the window.

### Idempotency

Repeated runs must not duplicate data:

- raw payload rows are keyed by the logical source identity of the payload
- curated tables are keyed by natural business identifiers such as `(account_key, metric_date)` or `(account_key, activity_id)`
- all writes use upserts

## Garmin Endpoint Coverage

Version 1 should target the endpoint groups that best support Grafana dashboards while still capturing broad Garmin coverage.

### Daily and wellness endpoints

Fetch and store the daily payloads that expose:

- steps
- distance
- calories
- floors climbed
- heart rate summary
- stress summary
- body battery
- respiration
- Pulse Ox or SpO2
- intensity minutes
- hydration
- daily summary aggregates exposed by the library

### Sleep

Fetch daily sleep data and retain both the raw response and a curated summary row.

### Activities

Fetch activity list data for the rolling window and per-activity detail when needed.

### Training and performance

Fetch the advanced performance metrics that the library exposes and that are useful in dashboards:

- HRV
- training readiness
- training status
- VO2 max or equivalent fitness metrics when available
- race predictions
- hill or endurance scores when available

### Body composition

Fetch weight and body composition data when present for the account.

### Deferred endpoint groups

The first implementation does not need curated tables for goals, badges, gear, nutrition, or devices. Those can still be added later by following the same raw-plus-curated pattern.

## Database Design

### `garmin_auth_tokens`

Stores Garmin OAuth state per logical account.

Suggested columns:

- `account_key text primary key`
- `token_payload text not null`
- `is_encrypted boolean not null default false`
- `updated_at timestamptz not null`
- `created_at timestamptz not null`

Notes:

- `token_payload` stores the serialized Garmin token bundle exactly as needed to reload the client.
- The table intentionally stores one current token bundle per account, not token history.

### `raw_garmin_payloads`

Stores every fetched Garmin response as source-of-truth JSONB.

Suggested columns:

- `id bigserial primary key`
- `account_key text not null`
- `endpoint_name text not null`
- `metric_date date`
- `source_id text not null`
- `payload jsonb not null`
- `payload_hash text not null`
- `fetched_at timestamptz not null`
- `updated_at timestamptz not null`

Suggested unique key:

- `(account_key, endpoint_name, metric_date, source_id)`

Notes:

- `source_id` identifies the logical record inside an endpoint. For daily records it can be the date string. For activities it is the Garmin activity ID. For single-date summaries without a natural nested ID, it can match the metric date.
- `payload_hash` allows change detection and helps avoid unnecessary downstream updates.

### `daily_metrics`

One row per account per date with the most common Grafana metrics.

Suggested columns:

- `account_key text not null`
- `metric_date date not null`
- `steps integer`
- `distance_meters numeric`
- `calories_total integer`
- `calories_active integer`
- `floors_climbed integer`
- `active_seconds integer`
- `moderate_intensity_minutes integer`
- `vigorous_intensity_minutes integer`
- `resting_heart_rate integer`
- `heart_rate_min integer`
- `heart_rate_max integer`
- `heart_rate_avg integer`
- `stress_avg integer`
- `stress_max integer`
- `body_battery_min integer`
- `body_battery_max integer`
- `body_battery_last integer`
- `respiration_avg numeric`
- `spo2_avg numeric`
- `hydration_ml integer`
- `weight_kg numeric`
- `updated_at timestamptz not null`

Suggested primary key:

- `(account_key, metric_date)`

### `sleep_summaries`

One row per account per sleep date.

Suggested columns:

- `account_key text not null`
- `sleep_date date not null`
- `sleep_score integer`
- `total_sleep_seconds integer`
- `deep_sleep_seconds integer`
- `light_sleep_seconds integer`
- `rem_sleep_seconds integer`
- `awake_seconds integer`
- `sleep_start_at timestamptz`
- `sleep_end_at timestamptz`
- `respiration_avg numeric`
- `updated_at timestamptz not null`

Suggested primary key:

- `(account_key, sleep_date)`

### `activities`

One row per Garmin activity.

Suggested columns:

- `account_key text not null`
- `activity_id bigint not null`
- `activity_name text`
- `activity_type text`
- `started_at timestamptz`
- `duration_seconds numeric`
- `moving_duration_seconds numeric`
- `elapsed_duration_seconds numeric`
- `distance_meters numeric`
- `calories integer`
- `avg_heart_rate integer`
- `max_heart_rate integer`
- `avg_speed_mps numeric`
- `elevation_gain_meters numeric`
- `elevation_loss_meters numeric`
- `training_effect_aerobic numeric`
- `training_effect_anaerobic numeric`
- `device_name text`
- `summary_json jsonb`
- `updated_at timestamptz not null`

Suggested primary key:

- `(account_key, activity_id)`

### `training_metrics`

One row per account per date for higher-level readiness and performance indicators.

Suggested columns:

- `account_key text not null`
- `metric_date date not null`
- `training_readiness integer`
- `hrv_status text`
- `hrv_weekly_avg numeric`
- `vo2_max numeric`
- `training_status text`
- `race_prediction_5k_seconds integer`
- `race_prediction_10k_seconds integer`
- `race_prediction_half_seconds integer`
- `race_prediction_full_seconds integer`
- `hill_score numeric`
- `endurance_score numeric`
- `updated_at timestamptz not null`

Suggested primary key:

- `(account_key, metric_date)`

## Data Mapping Rules

Curated tables should be populated from raw Garmin payloads through explicit mappers.

Mapping rules:

- Prefer stable numeric and timestamp fields that are useful in dashboards.
- Leave fields nullable when a metric is absent or unsupported by the device.
- Do not coerce missing values to zero.
- Preserve complex or evolving endpoint-specific details only in raw JSONB unless there is a clear dashboard need.
- Normalize times to UTC in PostgreSQL while using the configured local timezone for date-window calculations.

## Application Configuration

The script should be fully environment-driven.

Required or expected settings:

- `GARMIN_EMAIL`
- `GARMIN_PASSWORD`
- `GARMIN_ACCOUNT_KEY`
- `DATABASE_URL`
- `TIMEZONE`

Optional settings:

- `FERNET_KEY`
- `SYNC_DAYS`
- `LOG_LEVEL`

Behavior:

- `GARMIN_EMAIL` and `GARMIN_PASSWORD` are required only for initial bootstrap or recovery when no usable token exists.
- `SYNC_DAYS` defaults to `7`.
- `TIMEZONE` controls the rolling date window and should match the user’s Garmin usage context.

## Error Handling and Retry Strategy

The job should distinguish between fatal and non-fatal failures.

Fatal failures:

- PostgreSQL connection failure
- Token decryption failure
- Authentication failure with no recovery path
- Invalid required configuration

Non-fatal endpoint failures:

- individual Garmin endpoint request errors
- mapper failures for one endpoint while others succeed
- transient network failures that succeed after retry

Retry strategy:

- use bounded retries with backoff for transient Garmin and database write errors
- do not retry indefinitely inside a short-lived Kubernetes job
- fail fast on configuration and permanent authentication errors

Operational behavior:

- emit structured logs to stdout
- include endpoint name, date, and account key in error context
- continue processing independent endpoints when practical

## First Implementation Slice

The first implementation should optimize for a working end-to-end pipeline rather than exhaustive metric coverage on day one.

Recommended order:

1. Create the Python project scaffold and dependencies.
2. Implement PostgreSQL-backed token storage with optional Fernet encryption.
3. Implement Garmin client bootstrap using stored tokens with credential fallback.
4. Implement raw payload ingestion for a small daily endpoint set and activities.
5. Implement curated mappers for `daily_metrics`, `sleep_summaries`, and `activities`.
6. Add `training_metrics` once the end-to-end flow is stable.

This sequence keeps the highest-risk integration points early: authentication, persistence, and idempotent upserts.

## Testing Strategy

The implementation should use test-first development for behavior-bearing code.

Core test areas:

- token store round-trip with plain text storage
- token store round-trip with Fernet encryption
- token upsert and reload semantics per account
- raw payload repository upserts and conflict handling
- curated mapper behavior for daily metrics
- curated mapper behavior for sleep summaries
- curated mapper behavior for activities

Testing approach:

- unit tests for mappers and token encryption logic
- repository tests for SQL upsert behavior
- small orchestration tests with stubbed Garmin client responses

The tests should use representative fixture payloads and verify that repeated syncs remain idempotent.

## Success Criteria

The design is successful when:

- the script can authenticate with Garmin via `python-garminconnect`
- refreshed OAuth tokens persist in PostgreSQL across container restarts
- optional Fernet encryption protects stored tokens at rest
- repeated job runs do not duplicate rows
- raw Garmin payloads are preserved in JSONB
- Grafana-friendly tables can answer common dashboard queries without JSON extraction

## Implementation Notes

The code should stay intentionally small and explicit. The goal is a reliable personal data ingestion job, not a general-purpose ETL framework.
