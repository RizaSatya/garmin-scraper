from garmin_sync.repositories import json_payload_upsert_sql, raw_payload_upsert_sql


def test_raw_payload_upsert_targets_natural_conflict_key():
    sql = raw_payload_upsert_sql()

    assert "raw_garmin_payloads" in sql
    assert "(account_key, endpoint_name, metric_date, source_id)" in sql
    assert "on conflict" in sql.lower()


def test_json_payload_upsert_targets_record_key():
    sql = json_payload_upsert_sql("user_summaries")

    assert "user_summaries" in sql
    assert "(account_key, record_key)" in sql
    assert "payload = excluded.payload" in sql
