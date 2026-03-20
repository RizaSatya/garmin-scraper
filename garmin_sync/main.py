from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from garmin_sync.config import AppConfig
from garmin_sync.db import connect_db
from garmin_sync.garmin_client import bootstrap_garmin_client
from garmin_sync.repositories import (
    apply_schema,
    upsert_activity,
    upsert_daily_metrics,
    upsert_raw_payload,
    upsert_sleep_summary,
    upsert_training_metrics,
)
from garmin_sync.sync import build_sync_dates, collect_sync_payloads
from garmin_sync.token_store import load_token_payload, save_token_payload


def run_sync_job(config: AppConfig | None = None) -> None:
    app_config = config or AppConfig.from_env()

    with connect_db(app_config.database_url) as conn:
        apply_schema(conn)

        stored_token_payload = load_token_payload(
            conn,
            app_config.garmin_account_key,
            app_config.fernet_key,
        )
        garmin_client, serialized_tokens = bootstrap_garmin_client(
            garmin_email=app_config.garmin_email,
            garmin_password=app_config.garmin_password,
            stored_token_payload=stored_token_payload,
        )
        save_token_payload(
            conn,
            app_config.garmin_account_key,
            serialized_tokens,
            app_config.fernet_key,
        )

        today = datetime.now(ZoneInfo(app_config.timezone)).date()
        metric_dates = build_sync_dates(today, app_config.sync_days)
        sync_batch = collect_sync_payloads(
            garmin_client,
            app_config.garmin_account_key,
            metric_dates,
        )

        for row in sync_batch["raw_payloads"]:
            upsert_raw_payload(conn, row)
        for row in sync_batch["daily_metrics"]:
            upsert_daily_metrics(conn, row)
        for row in sync_batch["sleep_summaries"]:
            upsert_sleep_summary(conn, row)
        for row in sync_batch["activities"]:
            upsert_activity(conn, row)
        for row in sync_batch["training_metrics"]:
            upsert_training_metrics(conn, row)

        conn.commit()


def main() -> int:
    run_sync_job()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
