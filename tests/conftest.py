import pytest
from pathlib import Path
from uuid import uuid4

from app.core.config import settings
from app.core.database import init_db


@pytest.fixture
def mock_ai_service(mocker):
    """Neutraliza la llamada a Ollama en analyze() para tests aislados."""
    return mocker.patch(
        'app.services.ai_service.generate_ai_insights',
        return_value=['insight_mock'],
    )


@pytest.fixture
def temp_db():
    previous_db_path = settings.DB_PATH
    tmp_dir = Path("tests") / ".tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    db_path = tmp_dir / f"test_{uuid4().hex}.db"
    settings.DB_PATH = str(db_path)
    init_db()
    try:
        yield settings.DB_PATH
    finally:
        if db_path.exists():
            db_path.unlink()
        settings.DB_PATH = previous_db_path
