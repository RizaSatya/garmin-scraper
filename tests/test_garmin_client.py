from garmin_sync.garmin_client import choose_auth_mode


def test_choose_auth_mode_prefers_stored_tokens():
    mode = choose_auth_mode(
        stored_token_payload="token-data",
        garmin_email="user@example.com",
    )

    assert mode == "stored_tokens"
