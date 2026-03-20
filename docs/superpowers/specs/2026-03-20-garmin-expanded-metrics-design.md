# Garmin Expanded Metrics Ingestion Design

## Goal

Expand the Garmin sync job so it not only stores raw endpoint payloads and a few summary tables, but also writes a broad set of dedicated PostgreSQL tables for health, historical trends, advanced performance, body composition, and activity detail data exposed by `python-garminconnect`.

This expansion is intended to improve Grafana usability by making more Garmin metrics queryable without JSONB extraction.

## Scope

This design adds dedicated tables and ingestion logic for:

- daily health summary endpoints
- historical and trend endpoints
- advanced performance endpoints
- body composition endpoints
- activity detail endpoints

This design explicitly excludes:

- device tables
- gear tables
- goals, badges, and challenge tables
- wellness extras such as menstrual, pregnancy, nutrition, blood pressure, and all-day events

The existing raw payload archive remains in place and continues to capture all fetched endpoint responses.

## Design Principles

- Raw JSONB remains the source of truth for every fetched endpoint.
- Dedicated tables should be created only for metrics the user wants directly queryable.
- Each dedicated table should have a narrow, stable responsibility.
- Endpoint-specific payload shape differences must be normalized in mapper functions rather than leaking complexity into SQL.
- Missing metrics should be stored as `NULL`, not synthetic zeroes.

## Table Set

### Existing tables to keep

- `garmin_auth_tokens`
- `raw_garmin_payloads`
- `daily_metrics`
- `sleep_summaries`
- `activities`
- `training_metrics`

### Daily health tables to add

- `user_summaries`
- `stats_and_body`
- `heart_rate_daily`
- `resting_heart_rate_daily`
- `stress_daily`
- `stress_all_day`
- `steps_daily`
- `hydration_daily`
- `respiration_daily`
- `spo2_daily`
- `intensity_minutes_daily`
- `lifestyle_logging_daily`

### Historical and trend tables to add

- `daily_steps_history`
- `body_battery_daily`
- `body_battery_events`
- `floors_daily`
- `progress_summaries`
- `weekly_steps`
- `weekly_stress`
- `weekly_intensity_minutes`

### Advanced performance tables to add

- `training_readiness_morning`
- `hrv_daily`
- `max_metrics`
- `fitness_age`
- `race_predictions`
- `hill_scores`
- `endurance_scores`
- `running_tolerance`
- `lactate_threshold`
- `cycling_ftp`

### Body composition tables to add

- `body_composition_daily`
- `weigh_ins`
- `daily_weigh_ins`

### Activity detail tables to add

- `activity_splits`
- `activity_split_summaries`
- `activity_typed_splits`
- `activity_weather`
- `activity_hr_zones`
- `activity_power_zones`
- `activity_exercise_sets`
- `activity_gear_links`

## Data Modeling Strategy

### Per-day tables

Tables that represent one logical record per account per date should use:

- `account_key text not null`
- a date column such as `metric_date` or `summary_date`
- a primary key of `(account_key, <date-column>)`
- selected scalar columns plus one `payload jsonb` column when the endpoint has meaningful nested detail worth preserving alongside the flattened fields

This strategy applies to:

- `user_summaries`
- `stats_and_body`
- `resting_heart_rate_daily`
- `hydration_daily`
- `respiration_daily`
- `spo2_daily`
- `intensity_minutes_daily`
- `training_readiness_morning`
- `hrv_daily`
- `max_metrics`
- `fitness_age`
- `race_predictions`
- `hill_scores`
- `endurance_scores`
- `daily_weigh_ins`

### Per-day multi-row tables

Tables that may contain multiple records for the same account and date should include a stable per-record identifier or an ordinal key derived from the source payload.

This strategy applies to:

- `heart_rate_daily`
- `stress_daily`
- `stress_all_day`
- `steps_daily`
- `body_battery_daily`
- `body_battery_events`
- `floors_daily`
- `lifestyle_logging_daily`

These tables should use keys like:

- `(account_key, metric_date, source_id)`

where `source_id` is derived from a timestamp, event id, interval start, or sequence index depending on the payload.

### Per-range summary tables

Range-oriented endpoints should be modeled either as:

- one row per account and queried range, if the endpoint returns a single summary object
- one row per account and source date/week inside the range, if the endpoint returns an array of time-bucketed values

This applies to:

- `progress_summaries`
- `weekly_steps`
- `weekly_stress`
- `weekly_intensity_minutes`
- `running_tolerance`

### Activity-linked detail tables

Activity detail tables should use:

- `account_key text not null`
- `activity_id bigint not null`
- a record-specific identifier when multiple detail rows can exist per activity

Suggested primary keys:

- `activity_splits`: `(account_key, activity_id, split_index)`
- `activity_split_summaries`: `(account_key, activity_id, summary_type, split_index)`
- `activity_typed_splits`: `(account_key, activity_id, split_type, split_index)`
- `activity_weather`: `(account_key, activity_id)`
- `activity_hr_zones`: `(account_key, activity_id, zone_number)`
- `activity_power_zones`: `(account_key, activity_id, zone_number)`
- `activity_exercise_sets`: `(account_key, activity_id, exercise_set_id)`
- `activity_gear_links`: `(account_key, activity_id, gear_uuid)`

## Endpoint-to-Table Mapping

The sync runner should fetch and map these `python-garminconnect` endpoints:

### Daily health

- `get_user_summary` -> `user_summaries`
- `get_stats_and_body` -> `stats_and_body`
- `get_heart_rates` -> `heart_rate_daily`
- `get_rhr_day` or resting-heart-rate equivalent -> `resting_heart_rate_daily`
- `get_stress_data` -> `stress_daily`
- `get_all_day_stress` -> `stress_all_day`
- `get_steps_data` -> `steps_daily`
- `get_hydration_data` -> `hydration_daily`
- `get_respiration_data` -> `respiration_daily`
- `get_spo2_data` -> `spo2_daily`
- `get_intensity_minutes_data` -> `intensity_minutes_daily`
- `get_lifestyle_logging_data` -> `lifestyle_logging_daily`

### Historical and trend

- `get_daily_steps` -> `daily_steps_history`
- `get_body_battery` -> `body_battery_daily`
- `get_body_battery_events` -> `body_battery_events`
- `get_floors` -> `floors_daily`
- `get_progress_summary_between_dates` -> `progress_summaries`
- `get_weekly_steps` -> `weekly_steps`
- `get_weekly_stress` -> `weekly_stress`
- `get_weekly_intensity_minutes` -> `weekly_intensity_minutes`

### Advanced performance

- `get_morning_training_readiness` -> `training_readiness_morning`
- `get_hrv_data` -> `hrv_daily`
- `get_max_metrics` -> `max_metrics`
- `get_fitnessage_data` -> `fitness_age`
- `get_race_predictions` -> `race_predictions`
- `get_hill_score` -> `hill_scores`
- `get_endurance_score` -> `endurance_scores`
- `get_running_tolerance` -> `running_tolerance`
- `get_lactate_threshold` -> `lactate_threshold`
- `get_cycling_ftp` -> `cycling_ftp`

### Body composition

- `get_body_composition` -> `body_composition_daily`
- `get_weigh_ins` -> `weigh_ins`
- `get_daily_weigh_ins` -> `daily_weigh_ins`

### Activity detail

- `get_activity_splits` -> `activity_splits`
- `get_activity_split_summaries` -> `activity_split_summaries`
- `get_activity_typed_splits` -> `activity_typed_splits`
- `get_activity_weather` -> `activity_weather`
- `get_activity_hr_in_timezones` -> `activity_hr_zones`
- `get_activity_power_in_timezones` -> `activity_power_zones`
- `get_activity_exercise_sets` -> `activity_exercise_sets`
- `get_activity_gear` -> `activity_gear_links`

## Sync Behavior

The sync pipeline should continue to operate in two layers:

1. Fetch Garmin endpoint payloads and store them in `raw_garmin_payloads`
2. Map those payloads into dedicated tables via idempotent upserts

The default rolling sync behavior remains unchanged unless `BACKFILL_START_DATE` and `BACKFILL_END_DATE` are set.

For activity detail endpoints:

- fetch recent or backfill activities first
- then fetch detail sub-resources per activity id
- store each sub-resource both as raw payloads and in its own dedicated table

## Error Handling

- If one endpoint fails, other endpoint syncs for the same date should continue where practical.
- Mapper functions must handle both dict and list payload variants where Garmin returns inconsistent shapes.
- Empty arrays and absent payloads should not cause crashes; they should simply skip row generation.
- Failures should be logged with `endpoint_name`, `metric_date`, and `activity_id` when relevant.

## Rollout Plan

Implement in three chunks:

### Chunk 1: Daily health and historical tables

Deliver:

- schema additions
- mappers for daily health and historical endpoints
- repository upserts for new daily and time-series tables
- sync expansion for daily health and historical fetches

### Chunk 2: Advanced performance and body composition

Deliver:

- schema additions
- mappers for performance/body-composition endpoints
- upserts for those tables
- sync expansion for their fetch logic

### Chunk 3: Activity detail tables

Deliver:

- schema additions
- activity detail sub-resource mappers
- upserts for all activity-linked detail tables
- sync expansion to fetch detail sub-resources per activity

## Success Criteria

This expansion is successful when:

- the new dedicated tables are created and populated
- live Garmin payload shape differences do not crash the sync
- dashboard-relevant metrics beyond `daily_metrics` are queryable in SQL
- activity detail sub-resources are stored per activity
- the raw archive still captures every fetched payload for debugging and future expansion
