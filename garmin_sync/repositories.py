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
