import time
from typing import Dict, Tuple

import requests

from app.core.config import settings
from app.models.response_models import OAuth2ClientCredentialsConfig

_TOKEN_CACHE: Dict[Tuple[str, str, str, str], Dict[str, object]] = {}
_EXPIRY_SAFETY_WINDOW_S = 30


def get_oauth2_headers(auth_config: OAuth2ClientCredentialsConfig) -> Dict[str, str]:
    access_token = _get_access_token(auth_config)
    return {"Authorization": f"Bearer {access_token}"}


def _get_access_token(auth_config: OAuth2ClientCredentialsConfig) -> str:
    cache_key = (
        auth_config.token_url,
        auth_config.client_id,
        auth_config.scope or "",
        auth_config.audience or "",
    )
    now = time.time()
    cached = _TOKEN_CACHE.get(cache_key)
    if cached and float(cached.get("expires_at", 0)) > now + _EXPIRY_SAFETY_WINDOW_S:
        return str(cached["access_token"])

    response = requests.post(
        auth_config.token_url,
        data={
            "grant_type": "client_credentials",
            "client_id": auth_config.client_id,
            "client_secret": auth_config.client_secret,
            **({"scope": auth_config.scope} if auth_config.scope else {}),
            **({"audience": auth_config.audience} if auth_config.audience else {}),
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=settings.HTTP_TIMEOUT,
    )
    response.raise_for_status()

    payload = response.json()
    access_token = payload.get("access_token")
    if not access_token:
        raise RuntimeError("OAuth2 token response did not include access_token")

    expires_in = int(payload.get("expires_in", 3600))
    _TOKEN_CACHE[cache_key] = {
        "access_token": access_token,
        "expires_at": now + expires_in,
    }
    return str(access_token)
