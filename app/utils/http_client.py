import time
from typing import Any, Dict, Optional

import requests

from app.core.config import settings


def send_request(
    url: str,
    method: str,
    payload: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    try:
        start = time.time()
        req_headers = headers or {}

        if method == "GET":
            response = requests.get(url, headers=req_headers, timeout=settings.HTTP_TIMEOUT)
        elif method == "POST":
            response = requests.post(url, json=payload, headers=req_headers, timeout=settings.HTTP_TIMEOUT)
        else:
            return {"error": f"Unsupported HTTP method: {method}"}

        return {
            "status_code": response.status_code,
            "response_time": round(time.time() - start, 3),
        }

    except requests.exceptions.Timeout:
        return {"error": f"Request timed out after {settings.HTTP_TIMEOUT}s"}
    except requests.exceptions.ConnectionError:
        return {"error": "Connection failed — check the URL and network"}
    except Exception as e:
        return {"error": str(e)}
