import json
from typing import List, Optional

from app.core.database import get_connection
from app.models.response_models import SavedConfig, SavedConfigCreate


def save_config(data: SavedConfigCreate) -> SavedConfig:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO saved_configs (name, url, method, payload, headers, base_url)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                data.name,
                data.url,
                data.method,
                json.dumps(data.payload) if data.payload else None,
                json.dumps(data.headers) if data.headers else None,
                data.base_url or None,
            ),
        )
        row = conn.execute(
            "SELECT * FROM saved_configs WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()

    return _row_to_config(row)


def list_configs() -> List[SavedConfig]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM saved_configs ORDER BY created_at DESC"
        ).fetchall()
    return [_row_to_config(r) for r in rows]


def delete_config(config_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM saved_configs WHERE id = ?", (config_id,)
        )
    return cursor.rowcount > 0


def _row_to_config(row) -> SavedConfig:
    return SavedConfig(
        id=row["id"],
        name=row["name"],
        url=row["url"],
        method=row["method"],
        payload=json.loads(row["payload"]) if row["payload"] else None,
        headers=json.loads(row["headers"]) if row["headers"] else None,
        base_url=row["base_url"] if row["base_url"] else None,
        created_at=row["created_at"],
    )
