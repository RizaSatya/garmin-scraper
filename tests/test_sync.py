from datetime import date

from garmin_sync.sync import build_sync_dates, build_sync_dates_for_range, collect_sync_payloads


def test_build_sync_dates_includes_today_and_previous_days():
    dates = build_sync_dates(date(2026, 3, 20), sync_days=3)

    assert dates == ["2026-03-17", "2026-03-18", "2026-03-19", "2026-03-20"]


def test_build_sync_dates_for_range_is_inclusive():
    dates = build_sync_dates_for_range("2025-09-01", "2025-09-03")

    assert dates == ["2025-09-01", "2025-09-02", "2025-09-03"]


def test_main_returns_success_when_sync_completes(monkeypatch):
    from garmin_sync.main import main

    monkeypatch.setattr("garmin_sync.main.run_sync_job", lambda: None)

    assert main() == 0


def test_collect_sync_payloads_populates_expanded_tables():
    class FakeClient:
        def get_stats(self, cdate): return {"totalSteps": 1}
        def get_sleep_data(self, cdate): return {"sleepScore": 80}
        def get_training_readiness(self, cdate): return {"score": 50}
        def get_training_status(self, cdate): return {"status": "ok"}
        def get_hrv_data(self, cdate): return {"value": 1}
        def get_hydration_data(self, cdate): return {"value": 1}
        def get_respiration_data(self, cdate): return {"value": 1}
        def get_spo2_data(self, cdate): return {"value": 1}
        def get_body_battery(self, start, end=None): return [{"calendarDate": start, "value": 90}]
        def get_user_summary(self, cdate): return {"calendarDate": cdate, "steps": 1}
        def get_stats_and_body(self, cdate): return {"calendarDate": cdate, "body": {}}
        def get_heart_rates(self, cdate): return {"calendarDate": cdate}
        def get_rhr_day(self, cdate): return {"calendarDate": cdate, "value": 50}
        def get_stress_data(self, cdate): return {"calendarDate": cdate}
        def get_all_day_stress(self, cdate): return {"calendarDate": cdate}
        def get_steps_data(self, cdate): return [{"calendarDate": cdate, "steps": 1}]
        def get_intensity_minutes_data(self, cdate): return {"calendarDate": cdate}
        def get_lifestyle_logging_data(self, cdate): return {"calendarDate": cdate}
        def get_body_battery_events(self, cdate): return [{"calendarDate": cdate, "eventId": "e1"}]
        def get_floors(self, cdate): return {"calendarDate": cdate}
        def get_morning_training_readiness(self, cdate): return {"calendarDate": cdate}
        def get_max_metrics(self, cdate): return {"calendarDate": cdate}
        def get_fitnessage_data(self, cdate): return {"calendarDate": cdate}
        def get_body_composition(self, start, end=None): return {"calendarDate": start}
        def get_daily_weigh_ins(self, cdate): return {"calendarDate": cdate}
        def get_activities_by_date(self, start, end, sortorder="asc"): return [{"activityId": 123}]
        def get_activity(self, activity_id): return {"activityId": 123, "summaryDTO": {}, "activityTypeDTO": {}, "deviceMetaDataDTO": {}}
        def get_activity_splits(self, activity_id): return {"splits": []}
        def get_activity_split_summaries(self, activity_id): return {"summaries": []}
        def get_activity_typed_splits(self, activity_id): return {"typed": []}
        def get_activity_weather(self, activity_id): return {"weather": "sunny"}
        def get_activity_hr_in_timezones(self, activity_id): return {"zones": []}
        def get_activity_power_in_timezones(self, activity_id): return {"zones": []}
        def get_activity_exercise_sets(self, activity_id): return {"sets": []}
        def get_activity_gear(self, activity_id): return {"gear": []}
        def get_daily_steps(self, start, end): return [{"calendarDate": start, "steps": 1}]
        def get_progress_summary_between_dates(self, start, end): return {"startDate": start, "endDate": end}
        def get_weekly_steps(self, end): return [{"weekStartDate": end, "steps": 10}]
        def get_weekly_stress(self, end): return [{"weekStartDate": end, "stress": 10}]
        def get_weekly_intensity_minutes(self, start, end): return [{"weekStartDate": start, "minutes": 10}]
        def get_race_predictions(self, start, end): return {"startDate": start, "endDate": end}
        def get_hill_score(self, start, end=None): return {"startDate": start}
        def get_endurance_score(self, start, end=None): return {"startDate": start}
        def get_running_tolerance(self, start, end): return [{"calendarDate": start, "value": 1}]
        def get_lactate_threshold(self, **kwargs): return {"startDate": kwargs["start_date"]}
        def get_cycling_ftp(self): return {"ftp": 200}
        def get_weigh_ins(self, start, end): return {"startDate": start, "endDate": end}

    batch = collect_sync_payloads(FakeClient(), "personal", ["2025-09-01"])

    assert "user_summaries" in batch["expanded_tables"]
    assert "daily_steps_history" in batch["expanded_tables"]
    assert "activity_weather" in batch["expanded_tables"]


def test_collect_sync_payloads_emits_progress_logs(capsys):
    class FakeClient:
        def get_stats(self, cdate): return {"totalSteps": 1}
        def get_sleep_data(self, cdate): return {"sleepScore": 80}
        def get_training_readiness(self, cdate): return {"score": 50}
        def get_training_status(self, cdate): return {"status": "ok"}
        def get_hrv_data(self, cdate): return {"value": 1}
        def get_hydration_data(self, cdate): return {"value": 1}
        def get_respiration_data(self, cdate): return {"value": 1}
        def get_spo2_data(self, cdate): return {"value": 1}
        def get_body_battery(self, start, end=None): return [{"calendarDate": start, "value": 90}]
        def get_user_summary(self, cdate): return {"calendarDate": cdate}
        def get_stats_and_body(self, cdate): return {"calendarDate": cdate}
        def get_heart_rates(self, cdate): return {"calendarDate": cdate}
        def get_rhr_day(self, cdate): return {"calendarDate": cdate}
        def get_stress_data(self, cdate): return {"calendarDate": cdate}
        def get_all_day_stress(self, cdate): return {"calendarDate": cdate}
        def get_steps_data(self, cdate): return [{"calendarDate": cdate}]
        def get_intensity_minutes_data(self, cdate): return {"calendarDate": cdate}
        def get_lifestyle_logging_data(self, cdate): return {"calendarDate": cdate}
        def get_body_battery_events(self, cdate): return []
        def get_floors(self, cdate): return {"calendarDate": cdate}
        def get_morning_training_readiness(self, cdate): return {"calendarDate": cdate}
        def get_max_metrics(self, cdate): return {"calendarDate": cdate}
        def get_fitnessage_data(self, cdate): return {"calendarDate": cdate}
        def get_body_composition(self, start, end=None): return {"calendarDate": start}
        def get_daily_weigh_ins(self, cdate): return {"calendarDate": cdate}
        def get_activities_by_date(self, start, end, sortorder="asc"): return []
        def get_daily_steps(self, start, end): return []
        def get_progress_summary_between_dates(self, start, end): return {"startDate": start}
        def get_weekly_steps(self, end): return []
        def get_weekly_stress(self, end): return []
        def get_weekly_intensity_minutes(self, start, end): return []
        def get_race_predictions(self, start, end): return {"startDate": start}
        def get_hill_score(self, start, end=None): return {"startDate": start}
        def get_endurance_score(self, start, end=None): return {"startDate": start}
        def get_running_tolerance(self, start, end): return []
        def get_lactate_threshold(self, **kwargs): return {"startDate": kwargs["start_date"]}
        def get_cycling_ftp(self): return {"ftp": 200}
        def get_weigh_ins(self, start, end): return {"startDate": start}

    collect_sync_payloads(FakeClient(), "personal", ["2025-09-01"])
    output = capsys.readouterr().out

    assert "Syncing Garmin date 2025-09-01" in output
    assert "Fetched stats for 2025-09-01" in output
    assert "Fetched range endpoint daily_steps_history" in output
