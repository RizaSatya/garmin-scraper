from garmin_sync.repositories import raw_payload_upsert_sql


def test_raw_payload_upsert_targets_natural_conflict_key():
    sql = raw_payload_upsert_sql()

    assert "raw_garmin_payloads" in sql
    assert "(account_key, endpoint_name, metric_date, source_id)" in sql
    assert "on conflict" in sql.lower()
