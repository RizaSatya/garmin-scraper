from __future__ import annotations

from datetime import date, datetime, timedelta
from collections import defaultdict
import hashlib
import json

from garmin_sync.mappers import (
    map_payload_table_row,
    map_payload_table_rows,
    map_activity,
    map_daily_metrics,
    map_sleep_summary,
    map_training_metrics,
)


def log_progress(message: str) -> None:
    print(message, flush=True)


def build_sync_dates(today: date, sync_days: int) -> list[str]:
    start = today - timedelta(days=sync_days)
    current = start
    dates: list[str] = []
    while current <= today:
        dates.append(current.isoformat())
        current += timedelta(days=1)
    return dates


def build_sync_dates_for_range(start_date: str, end_date: str) -> list[str]:
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    current = start
    dates: list[str] = []
    while current <= end:
        dates.append(current.isoformat())
        current += timedelta(days=1)
    return dates


def safe_fetch(fetcher):
    try:
        return fetcher()
    except Exception:
        return None


def collect_sync_payloads(client, account_key: str, metric_dates: list[str]) -> dict[str, list[dict]]:
    raw_payloads: list[dict] = []
    daily_metrics: list[dict] = []
    sleep_summaries: list[dict] = []
    activities: list[dict] = []
    training_metrics: list[dict] = []
    expanded_tables: dict[str, list[dict]] = defaultdict(list)
    range_start = metric_dates[0]
    range_end = metric_dates[-1]

    def append_daily_table(table_name: str, metric_date: str, payload):
        if payload is None:
            return
        expanded_tables[table_name].append(
            map_payload_table_row(account_key, payload, metric_date=metric_date)
        )

    def append_list_table(table_name: str, payload, metric_date_fallback: str | None = None, activity_id: int | None = None):
        if payload is None:
            return
        expanded_tables[table_name].extend(
            map_payload_table_rows(
                account_key,
                payload,
                metric_date_fallback=metric_date_fallback,
                activity_id=activity_id,
            )
        )

    def append_range_table(table_name: str, payload, source_id: str = "summary"):
        if payload is None:
            return
        expanded_tables[table_name].append(
            map_payload_table_row(
                account_key,
                payload,
                range_start=range_start,
                range_end=range_end,
                source_id=source_id,
            )
        )
        log_progress(f"Mapped range table {table_name} (1 row)")

    def append_activity_table(table_name: str, activity_id: int, payload):
        if payload is None:
            return
        expanded_tables[table_name].extend(
            map_payload_table_rows(
                account_key,
                payload,
                activity_id=activity_id,
            )
        )

    for metric_date in metric_dates:
        log_progress(f"Syncing Garmin date {metric_date}")
        fetched_at = datetime.utcnow().isoformat()

        stats = client.get_stats(metric_date)
        log_progress(f"Fetched stats for {metric_date}")
        raw_payloads.append(
            build_raw_payload(account_key, "stats", metric_date, metric_date, stats, fetched_at)
        )
        daily_metrics.append(map_daily_metrics(account_key, metric_date, stats))

        sleep = client.get_sleep_data(metric_date)
        log_progress(f"Fetched sleep_data for {metric_date}")
        raw_payloads.append(
            build_raw_payload(account_key, "sleep_data", metric_date, metric_date, sleep, fetched_at)
        )
        sleep_summaries.append(map_sleep_summary(account_key, metric_date, sleep))

        for endpoint_name, table_name, fetcher, mode in (
            ("user_summary", "user_summaries", lambda: client.get_user_summary(metric_date), "daily"),
            ("stats_and_body", "stats_and_body", lambda: client.get_stats_and_body(metric_date), "daily"),
            ("heart_rates", "heart_rate_daily", lambda: client.get_heart_rates(metric_date), "daily"),
            ("rhr_day", "resting_heart_rate_daily", lambda: client.get_rhr_day(metric_date), "daily"),
            ("stress_data", "stress_daily", lambda: client.get_stress_data(metric_date), "daily"),
            ("all_day_stress", "stress_all_day", lambda: client.get_all_day_stress(metric_date), "daily"),
            ("steps_data", "steps_daily", lambda: client.get_steps_data(metric_date), "list"),
            ("hydration_data", "hydration_daily", lambda: client.get_hydration_data(metric_date), "daily"),
            ("respiration_data", "respiration_daily", lambda: client.get_respiration_data(metric_date), "daily"),
            ("spo2_data", "spo2_daily", lambda: client.get_spo2_data(metric_date), "daily"),
            ("intensity_minutes_data", "intensity_minutes_daily", lambda: client.get_intensity_minutes_data(metric_date), "daily"),
            ("lifestyle_logging_data", "lifestyle_logging_daily", lambda: client.get_lifestyle_logging_data(metric_date), "daily"),
            ("body_battery_events", "body_battery_events", lambda: client.get_body_battery_events(metric_date), "list"),
            ("floors", "floors_daily", lambda: client.get_floors(metric_date), "daily"),
            ("morning_training_readiness", "training_readiness_morning", lambda: client.get_morning_training_readiness(metric_date), "daily"),
            ("max_metrics", "max_metrics", lambda: client.get_max_metrics(metric_date), "daily"),
            ("fitnessage_data", "fitness_age", lambda: client.get_fitnessage_data(metric_date), "daily"),
            ("body_composition", "body_composition_daily", lambda: client.get_body_composition(metric_date, metric_date), "daily"),
            ("daily_weigh_ins", "daily_weigh_ins", lambda: client.get_daily_weigh_ins(metric_date), "daily"),
        ):
            payload = safe_fetch(fetcher)
            if payload is None:
                continue
            log_progress(f"Fetched {endpoint_name} for {metric_date}")
            raw_payloads.append(
                build_raw_payload(account_key, endpoint_name, metric_date, metric_date, payload, fetched_at)
            )
            if mode == "daily":
                append_daily_table(table_name, metric_date, payload)
            else:
                append_list_table(table_name, payload, metric_date_fallback=metric_date)

        training_readiness = client.get_training_readiness(metric_date)
        log_progress(f"Fetched training_readiness for {metric_date}")
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
            log_progress(f"Fetched {endpoint_name} for {metric_date}")
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
        append_daily_table("hrv_daily", metric_date, safe_fetch(lambda: client.get_hrv_data(metric_date)))

        for activity in client.get_activities_by_date(metric_date, metric_date, sortorder="asc"):
            activity_id = str(activity["activityId"])
            log_progress(f"Fetching activity detail {activity_id} for {metric_date}")
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

            for endpoint_name, table_name, fetcher in (
                ("activity_splits", "activity_splits", lambda: client.get_activity_splits(activity_id)),
                ("activity_split_summaries", "activity_split_summaries", lambda: client.get_activity_split_summaries(activity_id)),
                ("activity_typed_splits", "activity_typed_splits", lambda: client.get_activity_typed_splits(activity_id)),
                ("activity_weather", "activity_weather", lambda: client.get_activity_weather(activity_id)),
                ("activity_hr_in_timezones", "activity_hr_zones", lambda: client.get_activity_hr_in_timezones(activity_id)),
                ("activity_power_in_timezones", "activity_power_zones", lambda: client.get_activity_power_in_timezones(activity_id)),
                ("activity_exercise_sets", "activity_exercise_sets", lambda: client.get_activity_exercise_sets(activity_id)),
                ("activity_gear", "activity_gear_links", lambda: client.get_activity_gear(activity_id)),
            ):
                payload = safe_fetch(fetcher)
                if payload is None:
                    continue
                log_progress(f"Fetched {endpoint_name} for activity {activity_id}")
                raw_payloads.append(
                    build_raw_payload(
                        account_key,
                        endpoint_name,
                        metric_date,
                        activity_id,
                        payload,
                        fetched_at,
                    )
                )
                append_activity_table(table_name, int(activity_id), payload)

    fetched_at = datetime.utcnow().isoformat()
    for endpoint_name, table_name, fetcher, mode, source_id in (
        ("daily_steps", "daily_steps_history", lambda: client.get_daily_steps(range_start, range_end), "list", "summary"),
        ("body_battery", "body_battery_daily", lambda: client.get_body_battery(range_start, range_end), "list", "summary"),
        ("progress_summary_between_dates", "progress_summaries", lambda: client.get_progress_summary_between_dates(range_start, range_end), "range", "distance"),
        ("weekly_steps", "weekly_steps", lambda: client.get_weekly_steps(range_end), "list", "summary"),
        ("weekly_stress", "weekly_stress", lambda: client.get_weekly_stress(range_end), "list", "summary"),
        ("weekly_intensity_minutes", "weekly_intensity_minutes", lambda: client.get_weekly_intensity_minutes(range_start, range_end), "list", "summary"),
        ("race_predictions", "race_predictions", lambda: client.get_race_predictions(range_start, range_end), "range", "summary"),
        ("hill_score", "hill_scores", lambda: client.get_hill_score(range_start, range_end), "range", "summary"),
        ("endurance_score", "endurance_scores", lambda: client.get_endurance_score(range_start, range_end), "range", "summary"),
        ("running_tolerance", "running_tolerance", lambda: client.get_running_tolerance(range_start, range_end), "list", "summary"),
        ("lactate_threshold", "lactate_threshold", lambda: client.get_lactate_threshold(latest=False, start_date=range_start, end_date=range_end), "range", "summary"),
        ("cycling_ftp", "cycling_ftp", lambda: client.get_cycling_ftp(), "range", "summary"),
        ("weigh_ins", "weigh_ins", lambda: client.get_weigh_ins(range_start, range_end), "range", "summary"),
    ):
        payload = safe_fetch(fetcher)
        if payload is None:
            continue
        log_progress(f"Fetched range endpoint {table_name}")
        raw_payloads.append(
            build_raw_payload(account_key, endpoint_name, range_end, source_id, payload, fetched_at)
        )
        if mode == "list":
            append_list_table(table_name, payload, metric_date_fallback=range_end)
        else:
            append_range_table(table_name, payload, source_id=source_id)

    return {
        "raw_payloads": raw_payloads,
        "daily_metrics": daily_metrics,
        "sleep_summaries": sleep_summaries,
        "activities": activities,
        "training_metrics": training_metrics,
        "expanded_tables": dict(expanded_tables),
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
