import json
import math
from typing import List, Optional

from app.core.config import settings
from app.core.database import get_connection
from app.models.response_models import HistoryItem, HistoryPage


def save_result(url: str, method: str, result: dict) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO tests_history (url, method, result) VALUES (?, ?, ?)",
            (url, method, json.dumps(result)),
        )


def fetch_history_item(item_id: int) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT result FROM tests_history WHERE id = ?",
            (item_id,),
        ).fetchone()
    if not row:
        return None
    return json.loads(row["result"])


def fetch_history(page: int = 1, limit: int = 20) -> HistoryPage:
    limit = min(limit, settings.HISTORY_LIMIT)
    offset = (page - 1) * limit

    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM tests_history").fetchone()[0]
        rows = conn.execute(
            "SELECT id, url, method, result, created_at "
            "FROM tests_history ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()

    items = []
    for r in rows:
        parsed = json.loads(r["result"])
        items.append(
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

    return HistoryPage(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=max(1, math.ceil(total / limit)),
    )
