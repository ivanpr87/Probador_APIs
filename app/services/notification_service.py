import logging
from typing import Any, Dict, Optional

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)


def should_notify_severity_transition(
    previous_severity: Optional[str],
    current_severity: Optional[str],
) -> bool:
    if (current_severity or "").upper() != "CRITICAL":
        return False

    previous = (previous_severity or "").upper()
    return previous in {"", "LOW", "MEDIUM", "HIGH"}


def send_severity_escalation_notification(
    *,
    schedule_name: str,
    url: str,
    method: str,
    current_severity: str,
    quality_score: Optional[int],
    previous_severity: Optional[str],
) -> None:
    if not settings.NOTIFICATIONS_ENABLED:
        return

    payload = _build_generic_payload(
        schedule_name=schedule_name,
        url=url,
        method=method,
        current_severity=current_severity,
        quality_score=quality_score,
        previous_severity=previous_severity,
    )

    if settings.WEBHOOK_URL:
        _post_json(settings.WEBHOOK_URL, payload)

    if settings.SLACK_WEBHOOK_URL:
        _post_json(settings.SLACK_WEBHOOK_URL, _build_slack_payload(payload))


def _build_generic_payload(
    *,
    schedule_name: str,
    url: str,
    method: str,
    current_severity: str,
    quality_score: Optional[int],
    previous_severity: Optional[str],
) -> Dict[str, Any]:
    return {
        "event": "scheduled_test_escalated",
        "schedule_name": schedule_name,
        "url": url,
        "method": method,
        "current_severity": current_severity,
        "previous_severity": previous_severity or "NONE",
        "quality_score": quality_score,
        "message": (
            f"Scheduled test '{schedule_name}' escalated to {current_severity} "
            f"for {method} {url} (previous: {previous_severity or 'NONE'})."
        ),
    }


def _build_slack_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "text": (
            f":rotating_light: API Sentinel alert\n"
            f"*Schedule:* {payload['schedule_name']}\n"
            f"*Endpoint:* {payload['method']} {payload['url']}\n"
            f"*Severity:* {payload['previous_severity']} -> {payload['current_severity']}\n"
            f"*Quality score:* {payload['quality_score'] if payload['quality_score'] is not None else 'N/A'}"
        )
    }


def _post_json(url: str, payload: Dict[str, Any]) -> None:
    try:
        response = requests.post(url, json=payload, timeout=settings.HTTP_TIMEOUT)
        response.raise_for_status()
    except Exception as exc:
        logger.error("No se pudo enviar notificación a %s: %s", url, exc)
