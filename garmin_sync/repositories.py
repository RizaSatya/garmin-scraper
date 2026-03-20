from pathlib import Path

from psycopg.types.json import Jsonb


def raw_payload_upsert_sql() -> str:
    return """
    insert into raw_garmin_payloads (
        account_key,
        endpoint_name,
        metric_date,
        source_id,
        payload,
        payload_hash,
        fetched_at,
        updated_at
    ) values (
        %(account_key)s,
        %(endpoint_name)s,
        %(metric_date)s,
        %(source_id)s,
        %(payload)s,
        %(payload_hash)s,
        %(fetched_at)s,
        %(updated_at)s
    )
    on conflict (account_key, endpoint_name, metric_date, source_id)
    do update set
        payload = excluded.payload,
        payload_hash = excluded.payload_hash,
        fetched_at = excluded.fetched_at,
        updated_at = excluded.updated_at
    """


def apply_schema(conn, schema_path: str = "sql/schema.sql") -> None:
    conn.execute(Path(schema_path).read_text())


def upsert_raw_payload(conn, row: dict) -> None:
    conn.execute(
        raw_payload_upsert_sql(),
        {
            **row,
            "payload": Jsonb(row["payload"]),
        },
    )


def upsert_daily_metrics(conn, row: dict) -> None:
    conn.execute(
        """
        insert into daily_metrics (
            account_key, metric_date, steps, distance_meters, calories_total, calories_active,
            floors_climbed, active_seconds, moderate_intensity_minutes, vigorous_intensity_minutes,
            resting_heart_rate, updated_at
        ) values (
            %(account_key)s, %(metric_date)s, %(steps)s, %(distance_meters)s, %(calories_total)s,
            %(calories_active)s, %(floors_climbed)s, %(active_seconds)s, %(moderate_intensity_minutes)s,
            %(vigorous_intensity_minutes)s, %(resting_heart_rate)s, now()
        )
        on conflict (account_key, metric_date)
        do update set
            steps = excluded.steps,
            distance_meters = excluded.distance_meters,
            calories_total = excluded.calories_total,
            calories_active = excluded.calories_active,
            floors_climbed = excluded.floors_climbed,
            active_seconds = excluded.active_seconds,
            moderate_intensity_minutes = excluded.moderate_intensity_minutes,
            vigorous_intensity_minutes = excluded.vigorous_intensity_minutes,
            resting_heart_rate = excluded.resting_heart_rate,
            updated_at = now()
        """,
        row,
    )


def upsert_sleep_summary(conn, row: dict) -> None:
    conn.execute(
        """
        insert into sleep_summaries (
            account_key, sleep_date, sleep_score, total_sleep_seconds, deep_sleep_seconds,
            light_sleep_seconds, rem_sleep_seconds, awake_seconds, sleep_start_at, sleep_end_at, updated_at
        ) values (
            %(account_key)s, %(sleep_date)s, %(sleep_score)s, %(total_sleep_seconds)s,
            %(deep_sleep_seconds)s, %(light_sleep_seconds)s, %(rem_sleep_seconds)s,
            %(awake_seconds)s, %(sleep_start_at)s, %(sleep_end_at)s, now()
        )
        on conflict (account_key, sleep_date)
        do update set
            sleep_score = excluded.sleep_score,
            total_sleep_seconds = excluded.total_sleep_seconds,
            deep_sleep_seconds = excluded.deep_sleep_seconds,
            light_sleep_seconds = excluded.light_sleep_seconds,
            rem_sleep_seconds = excluded.rem_sleep_seconds,
            awake_seconds = excluded.awake_seconds,
            sleep_start_at = excluded.sleep_start_at,
            sleep_end_at = excluded.sleep_end_at,
            updated_at = now()
        """,
        row,
    )


def upsert_activity(conn, row: dict) -> None:
    conn.execute(
        """
        insert into activities (
            account_key, activity_id, activity_name, activity_type, started_at, duration_seconds,
            moving_duration_seconds, elapsed_duration_seconds, distance_meters, calories,
            avg_heart_rate, max_heart_rate, avg_speed_mps, elevation_gain_meters,
            elevation_loss_meters, training_effect_aerobic, training_effect_anaerobic,
            device_name, summary_json, updated_at
        ) values (
            %(account_key)s, %(activity_id)s, %(activity_name)s, %(activity_type)s, %(started_at)s,
            %(duration_seconds)s, %(moving_duration_seconds)s, %(elapsed_duration_seconds)s,
            %(distance_meters)s, %(calories)s, %(avg_heart_rate)s, %(max_heart_rate)s,
            %(avg_speed_mps)s, %(elevation_gain_meters)s, %(elevation_loss_meters)s,
            %(training_effect_aerobic)s, %(training_effect_anaerobic)s, %(device_name)s,
            %(summary_json)s, now()
        )
        on conflict (account_key, activity_id)
        do update set
            activity_name = excluded.activity_name,
            activity_type = excluded.activity_type,
            started_at = excluded.started_at,
            duration_seconds = excluded.duration_seconds,
            moving_duration_seconds = excluded.moving_duration_seconds,
            elapsed_duration_seconds = excluded.elapsed_duration_seconds,
            distance_meters = excluded.distance_meters,
            calories = excluded.calories,
            avg_heart_rate = excluded.avg_heart_rate,
            max_heart_rate = excluded.max_heart_rate,
            avg_speed_mps = excluded.avg_speed_mps,
            elevation_gain_meters = excluded.elevation_gain_meters,
            elevation_loss_meters = excluded.elevation_loss_meters,
            training_effect_aerobic = excluded.training_effect_aerobic,
            training_effect_anaerobic = excluded.training_effect_anaerobic,
            device_name = excluded.device_name,
            summary_json = excluded.summary_json,
            updated_at = now()
        """,
        {
            **row,
            "summary_json": Jsonb(row["summary_json"]),
        },
    )


def upsert_training_metrics(conn, row: dict) -> None:
    conn.execute(
        """
        insert into training_metrics (
            account_key, metric_date, training_readiness, hrv_status, vo2_max, training_status,
            race_prediction_5k_seconds, race_prediction_10k_seconds, race_prediction_half_seconds,
            race_prediction_full_seconds, hill_score, endurance_score, updated_at
        ) values (
            %(account_key)s, %(metric_date)s, %(training_readiness)s, %(hrv_status)s, %(vo2_max)s,
            %(training_status)s, %(race_prediction_5k_seconds)s, %(race_prediction_10k_seconds)s,
            %(race_prediction_half_seconds)s, %(race_prediction_full_seconds)s, %(hill_score)s,
            %(endurance_score)s, now()
        )
        on conflict (account_key, metric_date)
        do update set
            training_readiness = excluded.training_readiness,
            hrv_status = excluded.hrv_status,
            vo2_max = excluded.vo2_max,
            training_status = excluded.training_status,
            race_prediction_5k_seconds = excluded.race_prediction_5k_seconds,
            race_prediction_10k_seconds = excluded.race_prediction_10k_seconds,
            race_prediction_half_seconds = excluded.race_prediction_half_seconds,
            race_prediction_full_seconds = excluded.race_prediction_full_seconds,
            hill_score = excluded.hill_score,
            endurance_score = excluded.endurance_score,
            updated_at = now()
        """,
        row,
    )
