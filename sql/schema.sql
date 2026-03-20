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
