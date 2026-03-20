from datetime import date

from garmin_sync.sync import build_sync_dates


def test_build_sync_dates_includes_today_and_previous_days():
    dates = build_sync_dates(date(2026, 3, 20), sync_days=3)

    assert dates == ["2026-03-17", "2026-03-18", "2026-03-19", "2026-03-20"]


def test_main_returns_success_when_sync_completes(monkeypatch):
    from garmin_sync.main import main

    monkeypatch.setattr("garmin_sync.main.run_sync_job", lambda: None)

    assert main() == 0
