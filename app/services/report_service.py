from typing import Any, Dict

from app.core.config import settings


def build_report(data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "tool": settings.APP_NAME,
        "version": settings.APP_VERSION,
        **data,
    }
