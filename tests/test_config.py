from garmin_sync.config import AppConfig


def test_from_env_uses_defaults_for_optional_settings(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GARMIN_EMAIL", "user@example.com")
    monkeypatch.setenv("GARMIN_PASSWORD", "secret")
    monkeypatch.setenv("GARMIN_ACCOUNT_KEY", "personal")
    monkeypatch.setenv("DATABASE_URL", "postgresql://")
    monkeypatch.setenv("TIMEZONE", "Asia/Jakarta")

    config = AppConfig.from_env()

    assert config.sync_days == 7
    assert config.fernet_key is None


def test_from_env_allows_missing_bootstrap_credentials(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("GARMIN_EMAIL", raising=False)
    monkeypatch.delenv("GARMIN_PASSWORD", raising=False)
    monkeypatch.setenv("GARMIN_ACCOUNT_KEY", "personal")
    monkeypatch.setenv("DATABASE_URL", "postgresql://")
    monkeypatch.setenv("TIMEZONE", "Asia/Jakarta")

    config = AppConfig.from_env()

    assert config.garmin_email is None
    assert config.garmin_password is None


def test_from_env_defaults_account_key_to_personal(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("GARMIN_ACCOUNT_KEY", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://")
    monkeypatch.setenv("TIMEZONE", "Asia/Jakarta")

    config = AppConfig.from_env()

    assert config.garmin_account_key == "personal"


def test_from_env_loads_repo_root_dotenv(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("GARMIN_EMAIL", raising=False)
    monkeypatch.delenv("GARMIN_PASSWORD", raising=False)
    monkeypatch.delenv("GARMIN_ACCOUNT_KEY", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("TIMEZONE", raising=False)

    (tmp_path / ".env").write_text(
        "GARMIN_EMAIL=user@example.com\n"
        "GARMIN_PASSWORD=secret\n"
        "DATABASE_URL=postgresql://localhost:5432/garmin\n"
        "TIMEZONE=Asia/Jakarta\n"
    )

    config = AppConfig.from_env()

    assert config.garmin_email == "user@example.com"
    assert config.garmin_password == "secret"
    assert config.garmin_account_key == "personal"
    assert config.database_url == "postgresql://localhost:5432/garmin"


def test_from_env_reads_optional_backfill_window(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DATABASE_URL", "postgresql://")
    monkeypatch.setenv("TIMEZONE", "Asia/Jakarta")
    monkeypatch.setenv("BACKFILL_START_DATE", "2025-09-01")
    monkeypatch.setenv("BACKFILL_END_DATE", "2025-09-30")

    config = AppConfig.from_env()

    assert config.backfill_start_date == "2025-09-01"
    assert config.backfill_end_date == "2025-09-30"
