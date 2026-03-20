from garminconnect import Garmin


def choose_auth_mode(
    stored_token_payload: str | None,
    garmin_email: str | None,
) -> str:
    if stored_token_payload:
        return "stored_tokens"
    if garmin_email:
        return "credentials"
    raise ValueError("No Garmin authentication method available")


def bootstrap_garmin_client(
    garmin_email: str | None,
    garmin_password: str | None,
    stored_token_payload: str | None = None,
) -> tuple[Garmin, str]:
    mode = choose_auth_mode(stored_token_payload, garmin_email)
    client = Garmin(email=garmin_email, password=garmin_password)

    if mode == "stored_tokens":
        client.login(stored_token_payload)
    else:
        client.login()

    serialized_tokens = client.garth.dumps()
    return client, serialized_tokens
