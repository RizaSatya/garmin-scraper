# Garmin Grafana Sync Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python Garmin sync job that authenticates with `python-garminconnect`, stores OAuth tokens in PostgreSQL with optional Fernet encryption, ingests Garmin payloads into raw JSONB tables, and upserts Grafana-friendly analytics tables.

**Architecture:** The application is a small Python package with clear units for configuration, token persistence, Garmin API access, repositories, mappers, and orchestration. The sync entrypoint uses a rolling date window, writes raw payloads first, then projects curated rows into analytics tables with idempotent upserts.

**Tech Stack:** Python 3.12, `python-garminconnect`, `psycopg`, `cryptography` (Fernet), `pytest`, PostgreSQL, JSONB

---

## File Structure

Create these files and keep responsibilities narrow:

- `pyproject.toml`
  Project metadata, runtime dependencies, and test configuration.
- `README.md`
  Minimal setup and run instructions.
- `sql/schema.sql`
  PostgreSQL schema for token, raw payload, and curated analytics tables.
- `garmin_sync/__init__.py`
  Package marker.
- `garmin_sync/config.py`
  Environment parsing and validated config dataclass.
- `garmin_sync/crypto.py`
  Optional Fernet encryption and decryption helpers.
- `garmin_sync/db.py`
  PostgreSQL connection factory helpers.
- `garmin_sync/token_store.py`
  Load and save OAuth token bundles per account.
- `garmin_sync/garmin_client.py`
  Garmin login bootstrap and endpoint fetch wrapper.
- `garmin_sync/repositories.py`
  Raw and curated table upsert functions.
- `garmin_sync/mappers.py`
  Flatten Garmin payloads into `daily_metrics`, `sleep_summaries`, `activities`, and `training_metrics`.
- `garmin_sync/sync.py`
  Rolling-window sync orchestration.
- `garmin_sync/main.py`
  CLI entrypoint that wires config, DB, Garmin client, and sync runner.
- `tests/conftest.py`
  Shared fixtures for repository and mapper tests.
- `tests/test_config.py`
  Config validation tests.
- `tests/test_crypto.py`
  Encryption and decryption tests.
- `tests/test_token_store.py`
  Token persistence tests.
- `tests/test_repositories.py`
  Upsert behavior tests for raw and curated tables.
- `tests/test_mappers.py`
  Mapper tests using representative Garmin payload fixtures.
- `tests/test_garmin_client.py`
  Token bootstrap and login flow tests with stubs.
- `tests/test_sync.py`
  Orchestration tests covering rolling-window behavior and endpoint sequencing.
- `tests/fixtures/*.json`
  Small representative Garmin payloads for daily metrics, sleep, activities, and training.

## Chunk 1: Project Scaffold and Token Persistence

### Task 1: Create the Python project skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `garmin_sync/__init__.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write the failing config test**

```python
from garmin_sync.config import AppConfig


def test_from_env_uses_defaults_for_optional_settings(monkeypatch):
    monkeypatch.setenv("GARMIN_EMAIL", "user@example.com")
    monkeypatch.setenv("GARMIN_PASSWORD", "secret")
    monkeypatch.setenv("GARMIN_ACCOUNT_KEY", "personal")
    monkeypatch.setenv("DATABASE_URL", "postgresql://")
    monkeypatch.setenv("TIMEZONE", "Asia/Jakarta")

    config = AppConfig.from_env()

    assert config.sync_days == 7
    assert config.fernet_key is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py::test_from_env_uses_defaults_for_optional_settings -v`
Expected: FAIL with `ModuleNotFoundError` or `ImportError` for `garmin_sync.config`

- [ ] **Step 3: Write minimal project files**

```toml
[project]
name = "garmin-sync"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "garminconnect",
  "psycopg[binary]",
  "cryptography",
]

[project.optional-dependencies]
dev = ["pytest"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

```python
from dataclasses import dataclass
import os


@dataclass(frozen=True)
class AppConfig:
    garmin_email: str
    garmin_password: str
    garmin_account_key: str
    database_url: str
    timezone: str
    sync_days: int = 7
    fernet_key: str | None = None

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            garmin_email=os.environ["GARMIN_EMAIL"],
            garmin_password=os.environ["GARMIN_PASSWORD"],
            garmin_account_key=os.environ["GARMIN_ACCOUNT_KEY"],
            database_url=os.environ["DATABASE_URL"],
            timezone=os.environ["TIMEZONE"],
            sync_days=int(os.getenv("SYNC_DAYS", "7")),
            fernet_key=os.getenv("FERNET_KEY"),
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py::test_from_env_uses_defaults_for_optional_settings -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml README.md garmin_sync/__init__.py garmin_sync/config.py tests/test_config.py
git commit -m "feat: scaffold python garmin sync project"
```

### Task 2: Add optional Fernet token encryption

**Files:**
- Create: `garmin_sync/crypto.py`
- Create: `tests/test_crypto.py`

- [ ] **Step 1: Write the failing encryption test**

```python
from cryptography.fernet import Fernet
from garmin_sync.crypto import encrypt_token, decrypt_token


def test_encrypt_and_decrypt_round_trip():
    key = Fernet.generate_key().decode()
    plaintext = "serialized-token-payload"

    ciphertext = encrypt_token(plaintext, key)

    assert ciphertext != plaintext
    assert decrypt_token(ciphertext, key) == plaintext
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_crypto.py::test_encrypt_and_decrypt_round_trip -v`
Expected: FAIL with `ImportError` for `garmin_sync.crypto`

- [ ] **Step 3: Write minimal crypto helpers**

```python
from cryptography.fernet import Fernet


def encrypt_token(plaintext: str, key: str) -> str:
    return Fernet(key.encode()).encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str, key: str) -> str:
    return Fernet(key.encode()).decrypt(ciphertext.encode()).decode()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_crypto.py::test_encrypt_and_decrypt_round_trip -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add garmin_sync/crypto.py tests/test_crypto.py
git commit -m "feat: add optional token encryption helpers"
```

### Task 3: Add PostgreSQL token store behavior

**Files:**
- Create: `sql/schema.sql`
- Create: `garmin_sync/db.py`
- Create: `garmin_sync/token_store.py`
- Create: `tests/test_token_store.py`

- [ ] **Step 1: Write the failing token store test**

```python
from garmin_sync.token_store import TokenRecord, serialize_token_record


def test_serialize_token_record_marks_plaintext_state():
    record = serialize_token_record(
        account_key="personal",
        token_payload="token-data",
        fernet_key=None,
    )

    assert record.account_key == "personal"
    assert record.token_payload == "token-data"
    assert record.is_encrypted is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_token_store.py::test_serialize_token_record_marks_plaintext_state -v`
Expected: FAIL with `ImportError` for `garmin_sync.token_store`

- [ ] **Step 3: Write minimal schema and token serialization**

```sql
create table if not exists garmin_auth_tokens (
    account_key text primary key,
    token_payload text not null,
    is_encrypted boolean not null default false,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
```

```python
import psycopg


def connect_db(database_url: str):
    return psycopg.connect(database_url)
```

```python
from dataclasses import dataclass
from garmin_sync.crypto import encrypt_token, decrypt_token


@dataclass(frozen=True)
class TokenRecord:
    account_key: str
    token_payload: str
    is_encrypted: bool


def serialize_token_record(account_key: str, token_payload: str, fernet_key: str | None) -> TokenRecord:
    if fernet_key:
        return TokenRecord(account_key, encrypt_token(token_payload, fernet_key), True)
    return TokenRecord(account_key, token_payload, False)


def deserialize_token_payload(token_payload: str, is_encrypted: bool, fernet_key: str | None) -> str:
    if is_encrypted:
        if not fernet_key:
            raise ValueError("FERNET_KEY is required to decrypt stored Garmin tokens")
        return decrypt_token(token_payload, fernet_key)
    return token_payload
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_token_store.py::test_serialize_token_record_marks_plaintext_state -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add sql/schema.sql garmin_sync/db.py garmin_sync/token_store.py tests/test_token_store.py
git commit -m "feat: add postgres-backed garmin token store"
```

## Chunk 2: Raw Ingestion and Curated Mappers

### Task 4: Add repository upserts for raw and curated tables

**Files:**
- Modify: `sql/schema.sql`
- Create: `garmin_sync/repositories.py`
- Create: `tests/test_repositories.py`

- [ ] **Step 1: Write the failing raw upsert test**

```python
from garmin_sync.repositories import raw_payload_upsert_sql


def test_raw_payload_upsert_targets_natural_conflict_key():
    sql = raw_payload_upsert_sql()

    assert "raw_garmin_payloads" in sql
    assert "(account_key, endpoint_name, metric_date, source_id)" in sql
    assert "on conflict" in sql.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_repositories.py::test_raw_payload_upsert_targets_natural_conflict_key -v`
Expected: FAIL with `ImportError` for `garmin_sync.repositories`

- [ ] **Step 3: Write minimal repository SQL helpers**

```python
def raw_payload_upsert_sql() -> str:
    return """
    insert into raw_garmin_payloads (
        account_key, endpoint_name, metric_date, source_id, payload, payload_hash, fetched_at, updated_at
    ) values (%(account_key)s, %(endpoint_name)s, %(metric_date)s, %(source_id)s, %(payload)s, %(payload_hash)s, %(fetched_at)s, %(updated_at)s)
    on conflict (account_key, endpoint_name, metric_date, source_id)
    do update set
        payload = excluded.payload,
        payload_hash = excluded.payload_hash,
        fetched_at = excluded.fetched_at,
        updated_at = excluded.updated_at
    """
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_repositories.py::test_raw_payload_upsert_targets_natural_conflict_key -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add sql/schema.sql garmin_sync/repositories.py tests/test_repositories.py
git commit -m "feat: add raw and curated repository upserts"
```

### Task 5: Add daily metric and sleep mappers

**Files:**
- Create: `garmin_sync/mappers.py`
- Create: `tests/test_mappers.py`
- Create: `tests/fixtures/daily_summary.json`
- Create: `tests/fixtures/daily_sleep.json`

- [ ] **Step 1: Write the failing daily mapper test**

```python
import json
from pathlib import Path

from garmin_sync.mappers import map_daily_metrics


def test_map_daily_metrics_extracts_grafana_fields():
    payload = json.loads(Path("tests/fixtures/daily_summary.json").read_text())

    row = map_daily_metrics("personal", "2026-03-20", payload)

    assert row["account_key"] == "personal"
    assert row["metric_date"] == "2026-03-20"
    assert row["steps"] == 12345
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_mappers.py::test_map_daily_metrics_extracts_grafana_fields -v`
Expected: FAIL with `ImportError` for `garmin_sync.mappers`

- [ ] **Step 3: Write minimal daily and sleep mapping**

```python
def map_daily_metrics(account_key: str, metric_date: str, payload: dict) -> dict:
    return {
        "account_key": account_key,
        "metric_date": metric_date,
        "steps": payload.get("totalSteps"),
        "distance_meters": payload.get("totalDistanceMeters"),
        "calories_total": payload.get("totalKilocalories"),
        "resting_heart_rate": payload.get("restingHeartRate"),
    }


def map_sleep_summary(account_key: str, sleep_date: str, payload: dict) -> dict:
    return {
        "account_key": account_key,
        "sleep_date": sleep_date,
        "sleep_score": payload.get("sleepScore"),
        "total_sleep_seconds": payload.get("sleepTimeSeconds"),
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_mappers.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add garmin_sync/mappers.py tests/test_mappers.py tests/fixtures/daily_summary.json tests/fixtures/daily_sleep.json
git commit -m "feat: add daily and sleep metric mappers"
```

### Task 6: Add activity and training metric mapping

**Files:**
- Modify: `garmin_sync/mappers.py`
- Modify: `tests/test_mappers.py`
- Create: `tests/fixtures/activity_detail.json`
- Create: `tests/fixtures/training_readiness.json`

- [ ] **Step 1: Write the failing activity mapper test**

```python
import json
from pathlib import Path

from garmin_sync.mappers import map_activity


def test_map_activity_extracts_dashboard_fields():
    payload = json.loads(Path("tests/fixtures/activity_detail.json").read_text())

    row = map_activity("personal", payload)

    assert row["activity_id"] == 987654321
    assert row["activity_type"] == "running"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_mappers.py::test_map_activity_extracts_dashboard_fields -v`
Expected: FAIL with `AttributeError` or `ImportError` for `map_activity`

- [ ] **Step 3: Write minimal activity and training mappers**

```python
def map_activity(account_key: str, payload: dict) -> dict:
    summary = payload.get("summaryDTO", {})
    activity_type = payload.get("activityTypeDTO", {})
    return {
        "account_key": account_key,
        "activity_id": payload["activityId"],
        "activity_name": payload.get("activityName"),
        "activity_type": activity_type.get("typeKey"),
        "duration_seconds": summary.get("duration"),
        "distance_meters": summary.get("distance"),
        "calories": summary.get("calories"),
        "summary_json": payload,
    }


def map_training_metrics(account_key: str, metric_date: str, payload: dict) -> dict:
    return {
        "account_key": account_key,
        "metric_date": metric_date,
        "training_readiness": payload.get("score"),
        "hrv_status": payload.get("hrvStatus"),
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_mappers.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add garmin_sync/mappers.py tests/test_mappers.py tests/fixtures/activity_detail.json tests/fixtures/training_readiness.json
git commit -m "feat: add activity and training metric mappers"
```

## Chunk 3: Garmin Client, Sync Orchestration, and Entry Point

### Task 7: Add Garmin client bootstrap with stored-token fallback

**Files:**
- Create: `garmin_sync/garmin_client.py`
- Create: `tests/test_garmin_client.py`

- [ ] **Step 1: Write the failing bootstrap test**

```python
from garmin_sync.garmin_client import choose_auth_mode


def test_choose_auth_mode_prefers_stored_tokens():
    mode = choose_auth_mode(stored_token_payload="token-data", garmin_email="user@example.com")

    assert mode == "stored_tokens"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_garmin_client.py::test_choose_auth_mode_prefers_stored_tokens -v`
Expected: FAIL with `ImportError` for `garmin_sync.garmin_client`

- [ ] **Step 3: Write minimal Garmin auth bootstrap**

```python
def choose_auth_mode(stored_token_payload: str | None, garmin_email: str | None) -> str:
    if stored_token_payload:
        return "stored_tokens"
    if garmin_email:
        return "credentials"
    raise ValueError("No Garmin authentication method available")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_garmin_client.py::test_choose_auth_mode_prefers_stored_tokens -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add garmin_sync/garmin_client.py tests/test_garmin_client.py
git commit -m "feat: add garmin auth bootstrap logic"
```

### Task 8: Add rolling-window sync orchestration

**Files:**
- Create: `garmin_sync/sync.py`
- Create: `tests/test_sync.py`

- [ ] **Step 1: Write the failing rolling-window test**

```python
from datetime import date

from garmin_sync.sync import build_sync_dates


def test_build_sync_dates_includes_today_and_previous_days():
    dates = build_sync_dates(date(2026, 3, 20), sync_days=3)

    assert dates == ["2026-03-17", "2026-03-18", "2026-03-19", "2026-03-20"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_sync.py::test_build_sync_dates_includes_today_and_previous_days -v`
Expected: FAIL with `ImportError` for `garmin_sync.sync`

- [ ] **Step 3: Write minimal sync helpers**

```python
from datetime import timedelta


def build_sync_dates(today, sync_days: int) -> list[str]:
    start = today - timedelta(days=sync_days)
    current = start
    dates: list[str] = []
    while current <= today:
        dates.append(current.isoformat())
        current += timedelta(days=1)
    return dates
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_sync.py::test_build_sync_dates_includes_today_and_previous_days -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add garmin_sync/sync.py tests/test_sync.py
git commit -m "feat: add rolling window garmin sync orchestration"
```

### Task 9: Add CLI entrypoint and end-to-end happy path

**Files:**
- Create: `garmin_sync/main.py`
- Modify: `README.md`
- Test: `tests/test_sync.py`

- [ ] **Step 1: Write the failing main entrypoint test**

```python
from garmin_sync.main import main


def test_main_returns_success_when_sync_completes(monkeypatch):
    monkeypatch.setattr("garmin_sync.main.run_sync_job", lambda: None)

    assert main() == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_sync.py::test_main_returns_success_when_sync_completes -v`
Expected: FAIL with `ImportError` for `garmin_sync.main`

- [ ] **Step 3: Write minimal CLI entrypoint**

```python
def run_sync_job() -> None:
    pass


def main() -> int:
    run_sync_job()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run focused tests and then the full suite**

Run: `pytest tests/test_sync.py::test_main_returns_success_when_sync_completes -v`
Expected: PASS

Run: `pytest -v`
Expected: PASS for the full suite

- [ ] **Step 5: Commit**

```bash
git add README.md garmin_sync/main.py tests/test_sync.py
git commit -m "feat: add garmin sync CLI entrypoint"
```

## Manual Review Notes

Before implementation begins, confirm:

- the current `python-garminconnect` version still exposes the endpoint methods referenced in the spec
- Garmin token serialization format can be safely reloaded from database text without relying on filesystem-only helpers
- the curated table columns match the Grafana panels you actually plan to build first

## Verification Checklist During Execution

- Run focused `pytest` commands after each red-green cycle.
- Run `pytest -v` at the end of each chunk.
- Apply `sql/schema.sql` to a local PostgreSQL instance once repository code exists.
- Perform one dry run with stubbed Garmin responses before using real credentials.
- Perform one real sync against a non-production PostgreSQL database before pointing Grafana at it.

Plan complete and saved to `docs/superpowers/plans/2026-03-20-garmin-grafana-sync-plan.md`. Ready to execute?
