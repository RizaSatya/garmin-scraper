create table if not exists garmin_auth_tokens (
    account_key text primary key,
    token_payload text not null,
    is_encrypted boolean not null default false,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists raw_garmin_payloads (
    id bigserial primary key,
    account_key text not null,
    endpoint_name text not null,
    metric_date date,
    source_id text not null,
    payload jsonb not null,
    payload_hash text not null,
    fetched_at timestamptz not null,
    updated_at timestamptz not null,
    unique (account_key, endpoint_name, metric_date, source_id)
);

create table if not exists daily_metrics (
    account_key text not null,
    metric_date date not null,
    steps integer,
    distance_meters numeric,
    calories_total integer,
    calories_active integer,
    floors_climbed integer,
    active_seconds integer,
    moderate_intensity_minutes integer,
    vigorous_intensity_minutes integer,
    resting_heart_rate integer,
    heart_rate_min integer,
    heart_rate_max integer,
    heart_rate_avg integer,
    stress_avg integer,
    stress_max integer,
    body_battery_min integer,
    body_battery_max integer,
    body_battery_last integer,
    respiration_avg numeric,
    spo2_avg numeric,
    hydration_ml integer,
    weight_kg numeric,
    updated_at timestamptz not null,
    primary key (account_key, metric_date)
);

create table if not exists sleep_summaries (
    account_key text not null,
    sleep_date date not null,
    sleep_score integer,
    total_sleep_seconds integer,
    deep_sleep_seconds integer,
    light_sleep_seconds integer,
    rem_sleep_seconds integer,
    awake_seconds integer,
    sleep_start_at timestamptz,
    sleep_end_at timestamptz,
    respiration_avg numeric,
    updated_at timestamptz not null,
    primary key (account_key, sleep_date)
);

create table if not exists activities (
    account_key text not null,
    activity_id bigint not null,
    activity_name text,
    activity_type text,
    started_at timestamptz,
    duration_seconds numeric,
    moving_duration_seconds numeric,
    elapsed_duration_seconds numeric,
    distance_meters numeric,
    calories integer,
    avg_heart_rate integer,
    max_heart_rate integer,
    avg_speed_mps numeric,
    elevation_gain_meters numeric,
    elevation_loss_meters numeric,
    training_effect_aerobic numeric,
    training_effect_anaerobic numeric,
    device_name text,
    summary_json jsonb,
    updated_at timestamptz not null,
    primary key (account_key, activity_id)
);

create table if not exists training_metrics (
    account_key text not null,
    metric_date date not null,
    training_readiness integer,
    hrv_status text,
    hrv_weekly_avg numeric,
    vo2_max numeric,
    training_status text,
    race_prediction_5k_seconds integer,
    race_prediction_10k_seconds integer,
    race_prediction_half_seconds integer,
    race_prediction_full_seconds integer,
    hill_score numeric,
    endurance_score numeric,
    updated_at timestamptz not null,
    primary key (account_key, metric_date)
);

create table if not exists user_summaries (
    account_key text not null,
    record_key text not null,
    metric_date date,
    range_start date,
    range_end date,
    activity_id bigint,
    payload jsonb not null,
    updated_at timestamptz not null,
    primary key (account_key, record_key)
);

create table if not exists stats_and_body (like user_summaries including all);
create table if not exists heart_rate_daily (like user_summaries including all);
create table if not exists resting_heart_rate_daily (like user_summaries including all);
create table if not exists stress_daily (like user_summaries including all);
create table if not exists stress_all_day (like user_summaries including all);
create table if not exists steps_daily (like user_summaries including all);
create table if not exists hydration_daily (like user_summaries including all);
create table if not exists respiration_daily (like user_summaries including all);
create table if not exists spo2_daily (like user_summaries including all);
create table if not exists intensity_minutes_daily (like user_summaries including all);
create table if not exists lifestyle_logging_daily (like user_summaries including all);
create table if not exists daily_steps_history (like user_summaries including all);
create table if not exists body_battery_daily (like user_summaries including all);
create table if not exists body_battery_events (like user_summaries including all);
create table if not exists floors_daily (like user_summaries including all);
create table if not exists progress_summaries (like user_summaries including all);
create table if not exists weekly_steps (like user_summaries including all);
create table if not exists weekly_stress (like user_summaries including all);
create table if not exists weekly_intensity_minutes (like user_summaries including all);
create table if not exists training_readiness_morning (like user_summaries including all);
create table if not exists hrv_daily (like user_summaries including all);
create table if not exists max_metrics (like user_summaries including all);
create table if not exists fitness_age (like user_summaries including all);
create table if not exists race_predictions (like user_summaries including all);
create table if not exists hill_scores (like user_summaries including all);
create table if not exists endurance_scores (like user_summaries including all);
create table if not exists running_tolerance (like user_summaries including all);
create table if not exists lactate_threshold (like user_summaries including all);
create table if not exists cycling_ftp (like user_summaries including all);
create table if not exists body_composition_daily (like user_summaries including all);
create table if not exists weigh_ins (like user_summaries including all);
create table if not exists daily_weigh_ins (like user_summaries including all);
create table if not exists activity_splits (like user_summaries including all);
create table if not exists activity_split_summaries (like user_summaries including all);
create table if not exists activity_typed_splits (like user_summaries including all);
create table if not exists activity_weather (like user_summaries including all);
create table if not exists activity_hr_zones (like user_summaries including all);
create table if not exists activity_power_zones (like user_summaries including all);
create table if not exists activity_exercise_sets (like user_summaries including all);
create table if not exists activity_gear_links (like user_summaries including all);
