from garmin_sync.token_store import TokenRecord, serialize_token_record


def test_serialize_token_record_marks_plaintext_state():
    record = serialize_token_record(
        account_key="personal",
        token_payload="token-data",
        fernet_key=None,
    )

    assert record == TokenRecord(
        account_key="personal",
        token_payload="token-data",
        is_encrypted=False,
    )
