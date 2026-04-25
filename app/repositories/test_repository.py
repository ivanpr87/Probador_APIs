import json
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.core.database import get_connection


def save_result(url: str, method: str, result: dict, source: Optional[Dict[str, Any]] = None) -> int:
    payload = dict(result)
    if source:
        payload["source"] = source

    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO tests_history (url, method, result) VALUES (?, ?, ?)",
            (url, method, json.dumps(payload)),
        )
    return int(cursor.lastrowid)


def fetch_history_item_raw(item_id: int) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, url, method, result FROM tests_history WHERE id = ?",
            (item_id,),
        ).fetchone()
    if not row:
        return None
    return dict(row)


def fetch_history_page_raw(
    page: int = 1,
    limit: int = 20,
    url_filter: str = "",
    severity_filter: str = "",
) -> Tuple[int, List[dict]]:
    limit = min(limit, settings.HISTORY_LIMIT)
    offset = (page - 1) * limit

    where_clauses: List[str] = []
    params: List[str] = []

    if url_filter:
        where_clauses.append("url LIKE ?")
        params.append(f"%{url_filter}%")
    if severity_filter:
        where_clauses.append("json_extract(result, '$.severity') = ?")
        params.append(severity_filter.lower())

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    with get_connection() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) FROM tests_history {where_sql}", params
        ).fetchone()[0]
        rows = conn.execute(
            f"SELECT id, url, method, result, created_at "
            f"FROM tests_history {where_sql} ORDER BY id DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()

    return total, [dict(r) for r in rows]


def fetch_previous_comparable_result(
    url: str,
    method: str,
    source: Optional[Dict[str, Any]] = None,
    before_id: Optional[int] = None,
) -> Optional[dict]:
    source = source or {}
    query = [
        "SELECT result FROM tests_history",
        "WHERE url = ? AND method = ?",
    ]
    params: List[Any] = [url, method]

    if before_id is not None:
        query.append("AND id < ?")
        params.append(before_id)

    if source.get("schedule_id") is not None:
        query.append("AND json_extract(result, '$.source.schedule_id') = ?")
        params.append(source["schedule_id"])
    elif source.get("config_id") is not None:
        query.append("AND json_extract(result, '$.source.config_id') = ?")
        params.append(source["config_id"])
        query.append("AND json_extract(result, '$.source.schedule_id') IS NULL")
    else:
        query.append("AND json_extract(result, '$.source.config_id') IS NULL")
        query.append("AND json_extract(result, '$.source.schedule_id') IS NULL")

    query.append("ORDER BY id DESC LIMIT 1")

    with get_connection() as conn:
        row = conn.execute(" ".join(query), params).fetchone()

    if not row:
        return None
    return json.loads(row["result"])


def fetch_comparable_runs(
    url: str,
    method: str,
    source: Optional[Dict[str, Any]] = None,
    before_id: Optional[int] = None,
) -> List[dict]:
    source = source or {}
    query = [
        "SELECT result FROM tests_history",
        "WHERE url = ? AND method = ?",
    ]
    params: List[Any] = [url, method]

    if before_id is not None:
        query.append("AND id <= ?")
        params.append(before_id)

    if source.get("schedule_id") is not None:
        query.append("AND json_extract(result, '$.source.schedule_id') = ?")
        params.append(source["schedule_id"])
    elif source.get("config_id") is not None:
        query.append("AND json_extract(result, '$.source.config_id') = ?")
        params.append(source["config_id"])
        query.append("AND json_extract(result, '$.source.schedule_id') IS NULL")
    else:
        query.append("AND json_extract(result, '$.source.config_id') IS NULL")
        query.append("AND json_extract(result, '$.source.schedule_id') IS NULL")

    query.append("ORDER BY id ASC")

    with get_connection() as conn:
        rows = conn.execute(" ".join(query), params).fetchall()

    return [json.loads(r["result"]) for r in rows]
