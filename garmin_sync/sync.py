from __future__ import annotations

from datetime import date, datetime, timedelta
import hashlib
import json

from garmin_sync.mappers import (
    map_activity,
    map_daily_metrics,
    map_sleep_summary,
    map_training_metrics,
)


def build_sync_dates(today: date, sync_days: int) -> list[str]:
    start = today - timedelta(days=sync_days)
    current = start
    dates: list[str] = []
    while current <= today:
        dates.append(current.isoformat())
        current += timedelta(days=1)
    return dates


def collect_sync_payloads(client, account_key: str, metric_dates: list[str]) -> dict[str, list[dict]]:
    raw_payloads: list[dict] = []
    daily_metrics: list[dict] = []
    sleep_summaries: list[dict] = []
    activities: list[dict] = []
    training_metrics: list[dict] = []

    for metric_date in metric_dates:
        fetched_at = datetime.utcnow().isoformat()

        stats = client.get_stats(metric_date)
        raw_payloads.append(
            build_raw_payload(account_key, "stats", metric_date, metric_date, stats, fetched_at)
        )
        daily_metrics.append(map_daily_metrics(account_key, metric_date, stats))

        sleep = client.get_sleep_data(metric_date)
        raw_payloads.append(
            build_raw_payload(account_key, "sleep_data", metric_date, metric_date, sleep, fetched_at)
        )
        sleep_summaries.append(map_sleep_summary(account_key, metric_date, sleep))

        training_readiness = client.get_training_readiness(metric_date)
        raw_payloads.append(
            build_raw_payload(
                account_key,
                "training_readiness",
                metric_date,
                metric_date,
                training_readiness,
                fetched_at,
            )
        )
        training_metrics.append(
            map_training_metrics(account_key, metric_date, training_readiness)
        )

        for endpoint_name, fetcher in (
            ("training_status", lambda: client.get_training_status(metric_date)),
            ("hrv_data", lambda: client.get_hrv_data(metric_date)),
            ("hydration_data", lambda: client.get_hydration_data(metric_date)),
            ("respiration_data", lambda: client.get_respiration_data(metric_date)),
            ("spo2_data", lambda: client.get_spo2_data(metric_date)),
            ("body_battery", lambda: client.get_body_battery(metric_date, metric_date)),
        ):
            payload = fetcher()
            raw_payloads.append(
                build_raw_payload(
                    account_key,
                    endpoint_name,
                    metric_date,
                    metric_date,
                    payload,
                    fetched_at,
                )
            )

        for activity in client.get_activities_by_date(metric_date, metric_date, sortorder="asc"):
            activity_id = str(activity["activityId"])
            detail = client.get_activity(activity_id)
            raw_payloads.append(
                build_raw_payload(
                    account_key,
                    "activity_detail",
                    metric_date,
                    activity_id,
                    detail,
                    fetched_at,
                )
            )
            activities.append(map_activity(account_key, detail))

    return {
        "raw_payloads": raw_payloads,
        "daily_metrics": daily_metrics,
        "sleep_summaries": sleep_summaries,
        "activities": activities,
        "training_metrics": training_metrics,
    }


def build_raw_payload(
    account_key: str,
    endpoint_name: str,
    metric_date: str,
    source_id: str,
    payload: dict | list | None,
    fetched_at: str,
) -> dict:
    serialized = json.dumps(payload, sort_keys=True, default=str)
    return {
        "account_key": account_key,
        "endpoint_name": endpoint_name,
        "metric_date": metric_date,
        "source_id": source_id,
        "payload": payload,
        "payload_hash": hashlib.sha256(serialized.encode()).hexdigest(),
        "fetched_at": fetched_at,
        "updated_at": fetched_at,
    }
