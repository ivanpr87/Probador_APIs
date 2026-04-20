import json
from typing import List, Optional

from app.core.config import settings
from app.core.database import get_connection
from app.models.response_models import HistoryItem


def save_result(url: str, method: str, result: dict) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO tests_history (url, method, result) VALUES (?, ?, ?)",
            (url, method, json.dumps(result)),
        )


def fetch_history(limit: Optional[int] = None) -> List[HistoryItem]:
    limit = limit or settings.HISTORY_LIMIT
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, url, method, result, created_at "
            "FROM tests_history ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()

    history = []
    for r in rows:
        parsed = json.loads(r["result"])
        history.append(
            HistoryItem(
                id=r["id"],
                url=r["url"],
                method=r["method"],
                quality_score=parsed.get("quality_score"),
                severity=parsed.get("severity"),
                total_tests=parsed.get("total_tests"),
                created_at=r["created_at"],
            )
        )
    return history
