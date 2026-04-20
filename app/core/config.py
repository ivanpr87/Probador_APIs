from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    APP_NAME: str = "API Sentinel"
    APP_VERSION: str = "1.0.0"
    DB_PATH: str = "sentinel.db"
    HTTP_TIMEOUT: int = 5
    HISTORY_LIMIT: int = 50


settings = Settings()
