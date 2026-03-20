def map_daily_metrics(account_key: str, metric_date: str, payload: dict) -> dict:
    return {
        "account_key": account_key,
        "metric_date": metric_date,
        "steps": payload.get("totalSteps"),
        "distance_meters": payload.get("totalDistanceMeters"),
        "calories_total": payload.get("totalKilocalories"),
        "calories_active": payload.get("activeKilocalories"),
        "floors_climbed": payload.get("floorsAscendedInMeters"),
        "active_seconds": payload.get("activeSeconds"),
        "moderate_intensity_minutes": payload.get("moderateIntensityMinutes"),
        "vigorous_intensity_minutes": payload.get("vigorousIntensityMinutes"),
        "resting_heart_rate": payload.get("restingHeartRate"),
    }


def map_sleep_summary(account_key: str, sleep_date: str, payload: dict) -> dict:
    return {
        "account_key": account_key,
        "sleep_date": sleep_date,
        "sleep_score": payload.get("sleepScore"),
        "total_sleep_seconds": payload.get("sleepTimeSeconds"),
        "deep_sleep_seconds": payload.get("deepSleepSeconds"),
        "light_sleep_seconds": payload.get("lightSleepSeconds"),
        "rem_sleep_seconds": payload.get("remSleepSeconds"),
        "awake_seconds": payload.get("awakeSleepSeconds"),
        "sleep_start_at": payload.get("sleepStartTimestampGMT"),
        "sleep_end_at": payload.get("sleepEndTimestampGMT"),
    }


def map_activity(account_key: str, payload: dict) -> dict:
    summary = payload.get("summaryDTO", {})
    activity_type = payload.get("activityTypeDTO", {})
    device = payload.get("deviceMetaDataDTO", {})
    return {
        "account_key": account_key,
        "activity_id": payload["activityId"],
        "activity_name": payload.get("activityName"),
        "activity_type": activity_type.get("typeKey"),
        "started_at": payload.get("startTimeGMT"),
        "duration_seconds": summary.get("duration"),
        "moving_duration_seconds": summary.get("movingDuration"),
        "elapsed_duration_seconds": summary.get("elapsedDuration"),
        "distance_meters": summary.get("distance"),
        "calories": summary.get("calories"),
        "avg_heart_rate": summary.get("averageHR"),
        "max_heart_rate": summary.get("maxHR"),
        "avg_speed_mps": summary.get("averageSpeed"),
        "elevation_gain_meters": summary.get("elevationGain"),
        "elevation_loss_meters": summary.get("elevationLoss"),
        "training_effect_aerobic": summary.get("aerobicTrainingEffect"),
        "training_effect_anaerobic": summary.get("anaerobicTrainingEffect"),
        "device_name": device.get("deviceDisplayName"),
        "summary_json": payload,
    }


def map_training_metrics(account_key: str, metric_date: str, payload: dict) -> dict:
    predictions = payload.get("racePredictions", {})
    return {
        "account_key": account_key,
        "metric_date": metric_date,
        "training_readiness": payload.get("score"),
        "hrv_status": payload.get("hrvStatus"),
        "vo2_max": payload.get("vo2Max"),
        "training_status": payload.get("trainingStatus"),
        "race_prediction_5k_seconds": predictions.get("racePrediction5k"),
        "race_prediction_10k_seconds": predictions.get("racePrediction10k"),
        "race_prediction_half_seconds": predictions.get("racePredictionHalfMarathon"),
        "race_prediction_full_seconds": predictions.get("racePredictionMarathon"),
        "hill_score": payload.get("hillScore"),
        "endurance_score": payload.get("enduranceScore"),
    }
