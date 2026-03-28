import os

from garmin_sync.garmin_client import (
    bootstrap_garmin_client,
    choose_auth_mode,
    login_with_stored_tokens,
)


def test_choose_auth_mode_prefers_stored_tokens():
    mode = choose_auth_mode(
        stored_token_payload="token-data",
        garmin_email="user@example.com",
    )

    assert mode == "stored_tokens"


def test_bootstrap_credentials_ignores_ambient_garmintokens(monkeypatch):
    login_calls: list[str | None] = []

    class FakeGarth:
        def dumps(self) -> str:
            return "serialized-token-payload"

    class FakeGarmin:
        def __init__(self, email=None, password=None, is_cn=False, return_on_mfa=False):
            self.email = email
            self.password = password
            self.is_cn = is_cn
            self.return_on_mfa = return_on_mfa
            self.garth = FakeGarth()

        def login(self, tokenstore=None):
            login_calls.append(tokenstore)
            return None, None

    monkeypatch.setenv("GARMINTOKENS", "/tmp/stale-token-dir")

    _, serialized = bootstrap_garmin_client(
        garmin_email="user@example.com",
        garmin_password="secret",
        stored_token_payload=None,
        client_factory=FakeGarmin,
    )

    assert login_calls == [None]
    assert serialized == "serialized-token-payload"
    assert os.getenv("GARMINTOKENS") == "/tmp/stale-token-dir"


def test_bootstrap_credentials_handles_mfa_resume(monkeypatch):
    resume_calls: list[tuple[dict, str]] = []

    class FakeGarth:
        def dumps(self) -> str:
            return "serialized-token-payload"

    class FakeGarmin:
        def __init__(self, email=None, password=None, is_cn=False, return_on_mfa=False):
            self.garth = FakeGarth()
            self.return_on_mfa = return_on_mfa

        def login(self, tokenstore=None):
            return "needs_mfa", {"ticket": "abc"}

        def resume_login(self, client_state, mfa_code):
            resume_calls.append((client_state, mfa_code))
            return None, None

    monkeypatch.setattr("builtins.input", lambda _: "123456")

    _, serialized = bootstrap_garmin_client(
        garmin_email="user@example.com",
        garmin_password="secret",
        stored_token_payload=None,
        client_factory=FakeGarmin,
    )

    assert resume_calls == [({"ticket": "abc"}, "123456")]
    assert serialized == "serialized-token-payload"


def test_login_with_stored_tokens_hydrates_session():
    class FakeGarth:
        def __init__(self):
            self.profile = None
            self.loaded_payload = None

        def loads(self, payload):
            self.loaded_payload = payload

        def connectapi(self, path):
            if path == "/userprofile-service/userprofile/profile":
                return {"displayName": "runner", "fullName": "Road Runner"}
            if path == "/userprofile-service/userprofile/user-settings":
                return {"userData": {"measurementSystem": "metric"}}
            raise AssertionError(path)

    class FakeGarmin:
        def __init__(self):
            self.garth = FakeGarth()
            self.garmin_connect_user_settings_url = "/userprofile-service/userprofile/user-settings"
            self.display_name = None
            self.full_name = None
            self.unit_system = None

    client = FakeGarmin()

    login_with_stored_tokens(client, "stored-token-payload")

    assert client.garth.loaded_payload == "stored-token-payload"
    assert client.display_name == "runner"
    assert client.full_name == "Road Runner"
    assert client.unit_system == "metric"


def test_bootstrap_stored_tokens_skips_credential_login():
    login_calls = []

    class FakeGarth:
        def __init__(self):
            self.profile = {"displayName": "runner", "fullName": "Road Runner"}

        def loads(self, payload):
            login_calls.append(("loads", payload))

        def dumps(self) -> str:
            return "serialized-token-payload"

        def connectapi(self, path):
            if path == "/userprofile-service/userprofile/user-settings":
                return {"userData": {"measurementSystem": "metric"}}
            raise AssertionError(path)

    class FakeGarmin:
        def __init__(self, email=None, password=None, is_cn=False, return_on_mfa=False):
            self.garth = FakeGarth()
            self.garmin_connect_user_settings_url = "/userprofile-service/userprofile/user-settings"
            self.display_name = None
            self.full_name = None
            self.unit_system = None

        def login(self, tokenstore=None):
            login_calls.append(("login", tokenstore))
            return None, None

    _, serialized = bootstrap_garmin_client(
        garmin_email="user@example.com",
        garmin_password="secret",
        stored_token_payload="stored-token-payload",
        client_factory=FakeGarmin,
    )

    assert login_calls == [("loads", "stored-token-payload")]
    assert serialized == "serialized-token-payload"


def test_bootstrap_falls_back_to_credentials_when_stored_tokens_fail():
    login_calls = []

    class FakeGarth:
        def loads(self, payload):
            login_calls.append(("loads", payload))
            raise ValueError("expired")

        def dumps(self) -> str:
            return "serialized-token-payload"

    class FakeGarmin:
        def __init__(self, email=None, password=None, is_cn=False, return_on_mfa=False):
            self.garth = FakeGarth()

        def login(self, tokenstore=None):
            login_calls.append(("login", tokenstore))
            return None, None

    _, serialized = bootstrap_garmin_client(
        garmin_email="user@example.com",
        garmin_password="secret",
        stored_token_payload="stored-token-payload",
        client_factory=FakeGarmin,
    )

    assert login_calls == [("loads", "stored-token-payload"), ("login", None)]
    assert serialized == "serialized-token-payload"
