from dataclasses import dataclass
import os


@dataclass(frozen=True)
class AppConfig:
    garmin_email: str | None
    garmin_password: str | None
    garmin_account_key: str
    database_url: str
    timezone: str
    sync_days: int = 7
    fernet_key: str | None = None

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            garmin_email=os.getenv("GARMIN_EMAIL"),
            garmin_password=os.getenv("GARMIN_PASSWORD"),
            garmin_account_key=os.environ["GARMIN_ACCOUNT_KEY"],
            database_url=os.environ["DATABASE_URL"],
            timezone=os.environ["TIMEZONE"],
            sync_days=int(os.getenv("SYNC_DAYS", "7")),
            fernet_key=os.getenv("FERNET_KEY"),
        )
