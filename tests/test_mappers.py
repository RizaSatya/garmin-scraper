import json
from pathlib import Path

from garmin_sync.mappers import (
    map_activity,
    map_daily_metrics,
    map_sleep_summary,
    map_training_metrics,
)


def test_map_daily_metrics_extracts_grafana_fields():
    payload = json.loads(Path("tests/fixtures/daily_summary.json").read_text())

    row = map_daily_metrics("personal", "2026-03-20", payload)

    assert row["account_key"] == "personal"
    assert row["metric_date"] == "2026-03-20"
    assert row["steps"] == 12345
    assert row["distance_meters"] == 9876.5
    assert row["calories_total"] == 2345
    assert row["resting_heart_rate"] == 52


def test_map_sleep_summary_extracts_sleep_totals():
    payload = json.loads(Path("tests/fixtures/daily_sleep.json").read_text())

    row = map_sleep_summary("personal", "2026-03-19", payload)

    assert row["account_key"] == "personal"
    assert row["sleep_date"] == "2026-03-19"
    assert row["sleep_score"] == 81
    assert row["total_sleep_seconds"] == 26100


def test_map_activity_extracts_dashboard_fields():
    payload = json.loads(Path("tests/fixtures/activity_detail.json").read_text())

    row = map_activity("personal", payload)

    assert row["account_key"] == "personal"
    assert row["activity_id"] == 987654321
    assert row["activity_type"] == "running"
    assert row["distance_meters"] == 10000
    assert row["device_name"] == "Forerunner 965"


def test_map_training_metrics_extracts_readiness_fields():
    payload = json.loads(Path("tests/fixtures/training_readiness.json").read_text())

    row = map_training_metrics("personal", "2026-03-20", payload)

    assert row["account_key"] == "personal"
    assert row["metric_date"] == "2026-03-20"
    assert row["training_readiness"] == 78
    assert row["hrv_status"] == "balanced"
    assert row["race_prediction_5k_seconds"] == 1240
