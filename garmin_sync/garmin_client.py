from contextlib import contextmanager
import os

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


@contextmanager
def without_garmintokens_env():
    original = os.environ.pop("GARMINTOKENS", None)
    try:
        yield
    finally:
        if original is not None:
            os.environ["GARMINTOKENS"] = original


def hydrate_client_session(client: Garmin) -> None:
    profile = getattr(client.garth, "profile", None)
    if not profile:
        profile = client.garth.connectapi("/userprofile-service/userprofile/profile")
    if not isinstance(profile, dict) or "displayName" not in profile:
        raise ValueError("Invalid Garmin profile data from stored session")

    client.display_name = profile.get("displayName")
    client.full_name = profile.get("fullName")

    settings = client.garth.connectapi(client.garmin_connect_user_settings_url)
    if not isinstance(settings, dict) or "userData" not in settings:
        raise ValueError("Invalid Garmin user settings from stored session")
    client.unit_system = settings["userData"].get("measurementSystem")


def login_with_stored_tokens(client: Garmin, stored_token_payload: str) -> None:
    client.garth.loads(stored_token_payload)
    hydrate_client_session(client)

def bootstrap_garmin_client(
    garmin_email: str | None,
    garmin_password: str | None,
    stored_token_payload: str | None = None,
    client_factory=Garmin,
) -> tuple[Garmin, str]:
    mode = choose_auth_mode(stored_token_payload, garmin_email)
    client = client_factory(
        email=garmin_email,
        password=garmin_password,
        is_cn=False,
        return_on_mfa=True,
    )

    if mode == "stored_tokens":
        try:
            login_with_stored_tokens(client, stored_token_payload)
        except Exception:
            if not garmin_email:
                raise
            with without_garmintokens_env():
                result1, result2 = client.login()
            if result1 == "needs_mfa":
                mfa_code = input("Please enter your MFA code: ")
                client.resume_login(result2, mfa_code)
    else:
        with without_garmintokens_env():
            result1, result2 = client.login()
        if result1 == "needs_mfa":
            mfa_code = input("Please enter your MFA code: ")
            client.resume_login(result2, mfa_code)

    serialized_tokens = client.garth.dumps()
    return client, serialized_tokens
