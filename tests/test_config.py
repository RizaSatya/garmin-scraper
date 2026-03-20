from garmin_sync.config import AppConfig


def test_from_env_uses_defaults_for_optional_settings(monkeypatch):
    monkeypatch.setenv("GARMIN_EMAIL", "user@example.com")
    monkeypatch.setenv("GARMIN_PASSWORD", "secret")
    monkeypatch.setenv("GARMIN_ACCOUNT_KEY", "personal")
    monkeypatch.setenv("DATABASE_URL", "postgresql://")
    monkeypatch.setenv("TIMEZONE", "Asia/Jakarta")

    config = AppConfig.from_env()

    assert config.sync_days == 7
    assert config.fernet_key is None
