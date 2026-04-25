import json
import math
from typing import Any, Dict, Optional

from app.models.response_models import HistoryItem, HistoryPage, RunSource
from app.repositories.test_repository import (
    fetch_history_page_raw,
    fetch_history_item_raw,
    fetch_previous_comparable_result,
)
from app.services.latency_service import build_latency_stats_for_result


def get_history(
    page: int = 1,
    limit: int = 20,
    url_filter: str = "",
    severity_filter: str = "",
) -> HistoryPage:
    total, rows = fetch_history_page_raw(
        page=page, limit=limit, url_filter=url_filter, severity_filter=severity_filter
    )

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


def get_history_item(item_id: int) -> Optional[dict]:
    row = fetch_history_item_raw(item_id)
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
