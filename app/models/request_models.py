import ipaddress
import logging
import socket
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, field_validator

from app.models.response_models import OAuth2ClientCredentialsConfig

logger = logging.getLogger(__name__)


class CustomTestCase(BaseModel):
    name: str
    payload: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    expected_status: Optional[int] = None


class TestRequest(BaseModel):
    url: str
    method: str
    payload: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    auth_config: Optional[OAuth2ClientCredentialsConfig] = None
    expected_schema: Optional[Dict[str, str]] = None
    custom_cases: Optional[List[CustomTestCase]] = None

    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        allowed = {"GET", "POST", "PUT", "PATCH", "DELETE"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"Method must be one of: {allowed}")
        return upper

    @field_validator("url")
    @classmethod
    def validate_url_no_ssrf(cls, v: str) -> str:
        """Block private/internal IPs to prevent SSRF attacks."""
        parsed = urlparse(v)
        if not parsed.hostname:
            raise ValueError(f"Invalid URL: could not extract hostname from '{v}'")

        # Try parsing as literal IP first (fast path)
        try:
            ip = ipaddress.ip_address(parsed.hostname)
        except ValueError:
            # Not a literal IP — resolve hostname via DNS
            ip = _resolve_hostname(parsed.hostname)

        if ip is None:
            # DNS resolution failed or timed out — allow (best-effort)
            logger.warning("Could not resolve hostname '%s' for SSRF check; allowing", parsed.hostname)
            return v

        _reject_if_blocked(ip)
        return v


class OpenAPIImportRequest(BaseModel):
    spec: Dict[str, Any]
    base_url: Optional[str] = None
    name_prefix: Optional[str] = None


# ── SSRF validation helpers ──

def _resolve_hostname(hostname: str):
    """Resolve hostname to IP with 2s timeout. Returns None on failure."""
    try:
        socket.setdefaulttimeout(2)
        addrinfo = socket.getaddrinfo(hostname, None)
    except (socket.gaierror, socket.timeout, OSError):
        return None
    finally:
        socket.setdefaulttimeout(None)

    for _, _, _, _, sockaddr in addrinfo:
        ip_str = sockaddr[0]
        try:
            return ipaddress.ip_address(ip_str)
        except ValueError:
            continue
    return None


_BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]


def _reject_if_blocked(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> None:
    """Raise ValueError if IP is in a blocked (private/internal) range."""
    for net in _BLOCKED_NETWORKS:
        if ip in net:
            raise ValueError(
                f"SSRF check failed: IP address '{ip}' belongs to a private, "
                f"loopback, link-local, or reserved range. Access to internal "
                f"addresses is blocked."
            )
    # Also check via ipaddress built-in flags (belts-and-suspenders)
    if ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_unspecified:
        raise ValueError(
            f"SSRF check failed: IP address '{ip}' is classified as "
            f"loopback/private/link-local/unspecified."
        )
