# Garmin Expanded Metrics Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand the Garmin sync job so it stores broad health, historical, performance, body composition, and activity-detail metrics in dedicated PostgreSQL tables.

**Architecture:** Keep `raw_garmin_payloads` as the full archive, but add payload-first dedicated tables keyed by date, date plus source id, range, or activity id. Use generic mapping and generic JSON upserts for the new tables so we can cover many `python-garminconnect` endpoints without hand-writing dozens of bespoke repository functions.

**Tech Stack:** Python 3.11, `python-garminconnect`, `psycopg`, PostgreSQL JSONB, `pytest`

---

## Chunk 1: Expanded Schema and Generic JSON Upserts

### Task 1: Add the expanded table schema

**Files:**
- Modify: `sql/schema.sql`
- Test: `tests/test_repositories.py`

- [ ] **Step 1: Write the failing repository test for generic JSON tables**
- [ ] **Step 2: Run `PYTHONPATH=. .venv/bin/pytest tests/test_repositories.py -v` and verify it fails**
- [ ] **Step 3: Add the new health, historical, performance, body-composition, and activity-detail tables using payload-first schemas**
- [ ] **Step 4: Add generic upsert helpers for daily, series, range, and activity-detail payload tables**
- [ ] **Step 5: Run `PYTHONPATH=. .venv/bin/pytest tests/test_repositories.py -v` and verify it passes**

## Chunk 2: Generic Mappers for Expanded Endpoints

### Task 2: Add payload-first mappers for new endpoint groups

**Files:**
- Modify: `garmin_sync/mappers.py`
- Modify: `tests/test_mappers.py`

- [ ] **Step 1: Write failing tests for daily payload rows, list payload rows, range payload rows, and activity-detail payload rows**
- [ ] **Step 2: Run `PYTHONPATH=. .venv/bin/pytest tests/test_mappers.py -v` and verify the new tests fail**
- [ ] **Step 3: Implement generic helpers for extracting metric dates, source ids, and normalized payload rows**
- [ ] **Step 4: Run `PYTHONPATH=. .venv/bin/pytest tests/test_mappers.py -v` and verify all mapper tests pass**

## Chunk 3: Sync Expansion for Demo-Mapped Endpoints

### Task 3: Fetch and route the new Garmin endpoints

**Files:**
- Modify: `garmin_sync/sync.py`
- Modify: `garmin_sync/main.py`
- Modify: `tests/test_sync.py`

- [ ] **Step 1: Write failing tests for expanded sync batch structure**
- [ ] **Step 2: Run `PYTHONPATH=. .venv/bin/pytest tests/test_sync.py -v` and verify the new tests fail**
- [ ] **Step 3: Expand `collect_sync_payloads()` to fetch the approved endpoint set and map them into the new dedicated table batches**
- [ ] **Step 4: Update the main sync runner to upsert the new table batches**
- [ ] **Step 5: Run `PYTHONPATH=. .venv/bin/pytest tests/test_sync.py -v` and verify sync tests pass**

## Chunk 4: Documentation and Verification

### Task 4: Document and verify the expanded metrics coverage

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Document the new table coverage and the backfill flow briefly in the README**
- [ ] **Step 2: Run `PYTHONPATH=. .venv/bin/pytest -v` and verify the full suite passes**
- [ ] **Step 3: Smoke-test `garmin-sync` against the user’s backfill window if they want a live verification pass**
