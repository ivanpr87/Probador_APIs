import json
import math
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.database import get_connection
from app.models.response_models import HistoryItem, HistoryPage, LatencyStats, RunSource
from app.services.latency_service import build_latency_stats, extract_run_latency_ms


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


def fetch_history_item(item_id: int) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, url, method, result FROM tests_history WHERE id = ?",
            (item_id,),
        ).fetchone()
    if not row:
        return None
    parsed = json.loads(row["result"])
    stats = build_latency_stats_for_result(
        url=row["url"],
        method=row["method"],
        source=parsed.get("source"),
        before_id=row["id"],
    )
    parsed["latency_stats"] = stats.model_dump() if stats else None
    return parsed


def fetch_history(
    page: int = 1,
    limit: int = 20,
    url_filter: str = "",
    severity_filter: str = "",
) -> HistoryPage:
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

    items = []
    for r in rows:
        parsed = json.loads(r["result"])
        previous = fetch_previous_comparable_result(
            url=r["url"],
            method=r["method"],
            source=parsed.get("source"),
            before_id=r["id"],
        )
        previous_score = previous.get("quality_score") if previous else None
        current_score = parsed.get("quality_score")
        delta_score = (
            current_score - previous_score
            if isinstance(current_score, int) and isinstance(previous_score, int)
            else None
        )
        items.append(
            HistoryItem(
                id=r["id"],
                url=r["url"],
                method=r["method"],
                quality_score=current_score,
                severity=parsed.get("severity"),
                total_tests=parsed.get("total_tests"),
                created_at=r["created_at"],
                previous_score=previous_score,
                delta_score=delta_score,
                delta_direction=_get_delta_direction(delta_score),
                source=_parse_source(parsed.get("source")),
            )
        )

    return HistoryPage(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=max(1, math.ceil(total / limit)),
    )


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


def build_latency_stats_for_result(
    url: str,
    method: str,
    source: Optional[Dict[str, Any]] = None,
    current_result: Optional[Dict[str, Any]] = None,
    before_id: Optional[int] = None,
) -> Optional[LatencyStats]:
    latencies = fetch_comparable_run_latencies(
        url=url,
        method=method,
        source=source,
        before_id=before_id,
    )

    current_latency = extract_run_latency_ms(current_result) if current_result else None
    if current_latency is not None:
        latencies.append(current_latency)

    return build_latency_stats(latencies)


def fetch_comparable_run_latencies(
    url: str,
    method: str,
    source: Optional[Dict[str, Any]] = None,
    before_id: Optional[int] = None,
) -> List[float]:
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

    latencies: List[float] = []
    for row in rows:
        parsed = json.loads(row["result"])
        latency_ms = extract_run_latency_ms(parsed)
        if latency_ms is not None:
            latencies.append(latency_ms)

    return latencies


def _get_delta_direction(delta_score: Optional[int]) -> Optional[str]:
    if delta_score is None:
        return None
    if delta_score > 0:
        return "up"
    if delta_score < 0:
        return "down"
    return "same"


def _parse_source(source: Optional[Dict[str, Any]]) -> Optional[RunSource]:
    if not source:
        return None
    return RunSource(**source)
