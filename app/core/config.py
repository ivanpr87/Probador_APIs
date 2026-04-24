import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self):
        self.APP_NAME: str       = os.getenv('APP_NAME', 'API Sentinel')
        self.APP_VERSION: str    = os.getenv('APP_VERSION', '1.0.0')
        self.DB_PATH: str        = os.getenv('DB_PATH', 'sentinel.db')
        self.HTTP_TIMEOUT: int   = int(os.getenv('HTTP_TIMEOUT', '5'))
        self.HISTORY_LIMIT: int  = int(os.getenv('HISTORY_LIMIT', '50'))
        self.OLLAMA_URL: str     = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        self.OLLAMA_MODEL: str   = os.getenv('OLLAMA_MODEL', 'qwen3:8b')
        self.OLLAMA_TIMEOUT: int = int(os.getenv('OLLAMA_TIMEOUT', '30'))
        self.NOTIFICATIONS_ENABLED: bool = os.getenv('NOTIFICATIONS_ENABLED', 'false').lower() == 'true'
        self.WEBHOOK_URL: str = os.getenv('WEBHOOK_URL', '')
        self.SLACK_WEBHOOK_URL: str = os.getenv('SLACK_WEBHOOK_URL', '')


settings = Settings()
