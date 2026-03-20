from dataclasses import dataclass
import os
from pathlib import Path


def load_dotenv(dotenv_path: str = ".env") -> None:
    path = Path(dotenv_path)
    if not path.exists():
        return

    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def optional_env(name: str) -> str | None:
    value = os.getenv(name)
    if value == "":
        return None
    return value


@dataclass(frozen=True)
class AppConfig:
    garmin_email: str | None
    garmin_password: str | None
    garmin_account_key: str
    database_url: str
    timezone: str
    backfill_start_date: str | None = None
    backfill_end_date: str | None = None
    sync_days: int = 7
    fernet_key: str | None = None

    @classmethod
    def from_env(cls) -> "AppConfig":
        load_dotenv()
        return cls(
            garmin_email=optional_env("GARMIN_EMAIL"),
            garmin_password=optional_env("GARMIN_PASSWORD"),
            garmin_account_key=os.getenv("GARMIN_ACCOUNT_KEY", "personal"),
            database_url=os.environ["DATABASE_URL"],
            timezone=os.environ["TIMEZONE"],
            backfill_start_date=optional_env("BACKFILL_START_DATE"),
            backfill_end_date=optional_env("BACKFILL_END_DATE"),
            sync_days=int(os.getenv("SYNC_DAYS", "7")),
            fernet_key=optional_env("FERNET_KEY"),
        )
