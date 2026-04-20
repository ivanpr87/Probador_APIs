from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    APP_NAME: str = "API Sentinel"
    APP_VERSION: str = "1.0.0"
    DB_PATH: str = "sentinel.db"
    HTTP_TIMEOUT: int = 5
    HISTORY_LIMIT: int = 50
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3:8b"
    OLLAMA_TIMEOUT: int = 30


settings = Settings()
