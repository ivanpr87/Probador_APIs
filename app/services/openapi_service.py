from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.models.response_models import OpenAPIImportSummary, SavedConfig, SavedConfigCreate
from app.repositories.configs_repository import save_config

_SUPPORTED_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}


@dataclass
class ParsedEndpointConfig:
    name: str
    url: str
    method: str
    payload: Optional[Dict[str, Any]]
    base_url: Optional[str]


def import_openapi_spec(
    spec: Dict[str, Any],
    *,
    base_url_override: Optional[str] = None,
    name_prefix: Optional[str] = None,
) -> OpenAPIImportSummary:
    parsed = parse_openapi_spec(
        spec,
        base_url_override=base_url_override,
        name_prefix=name_prefix,
    )

    created: List[SavedConfig] = []
    skipped = 0
    errors: List[str] = []

    for item in parsed:
        try:
            created.append(
                save_config(
                    SavedConfigCreate(
                        name=item.name,
                        url=item.url,
                        method=item.method,
                        payload=item.payload,
                        base_url=item.base_url,
                    )
                )
            )
        except Exception as exc:
            if "UNIQUE constraint" in str(exc):
                skipped += 1
                continue
            errors.append(f"{item.method} {item.url}: {exc}")

    return OpenAPIImportSummary(
        created=len(created),
        skipped=skipped,
        errors=errors,
        configs=created,
    )


def parse_openapi_spec(
    spec: Dict[str, Any],
    *,
    base_url_override: Optional[str] = None,
    name_prefix: Optional[str] = None,
) -> List[ParsedEndpointConfig]:
    if not isinstance(spec, dict) or "paths" not in spec:
        raise ValueError("OpenAPI spec must be an object with a 'paths' field")

    base_url = base_url_override or _extract_base_url(spec)
    parsed: List[ParsedEndpointConfig] = []

    for path, path_item in (spec.get("paths") or {}).items():
        if not isinstance(path_item, dict):
            continue

        for method, operation in path_item.items():
            method_upper = method.upper()
            if method_upper not in _SUPPORTED_METHODS:
                continue
            if not isinstance(operation, dict):
                continue

            payload = _extract_payload(spec, operation)
            name = _build_config_name(path, method_upper, operation, name_prefix)
            parsed.append(
                ParsedEndpointConfig(
                    name=name,
                    url=path,
                    method=method_upper,
                    payload=payload,
                    base_url=base_url,
                )
            )

    return parsed


def _extract_base_url(spec: Dict[str, Any]) -> Optional[str]:
    servers = spec.get("servers")
    if isinstance(servers, list) and servers:
        first = servers[0]
        if isinstance(first, dict):
            url = first.get("url")
            if isinstance(url, str) and url:
                return url.rstrip("/")

    swagger = spec.get("swagger")
    if swagger and str(swagger).startswith("2."):
        host = spec.get("host")
        if not host:
            return None
        scheme = "https"
        schemes = spec.get("schemes")
        if isinstance(schemes, list) and schemes:
            scheme = schemes[0]
        base_path = (spec.get("basePath") or "").rstrip("/")
        return f"{scheme}://{host}{base_path}"

    return None


def _build_config_name(
    path: str,
    method: str,
    operation: Dict[str, Any],
    name_prefix: Optional[str],
) -> str:
    raw_name = operation.get("operationId") or f"{method} {path}"
    safe = str(raw_name).replace("/", " ").replace("{", "").replace("}", "")
    safe = " ".join(safe.split())
    return f"{name_prefix} {safe}".strip() if name_prefix else safe


def _extract_payload(spec: Dict[str, Any], operation: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if "requestBody" in operation:
        request_body = _resolve_ref(spec, operation.get("requestBody"))
        if not isinstance(request_body, dict):
            return None
        content = request_body.get("content") or {}
        if not isinstance(content, dict):
            return None
        json_content = content.get("application/json")
        if not isinstance(json_content, dict):
            return None
        schema = _resolve_ref(spec, json_content.get("schema"))
        return _schema_to_payload(spec, schema)

    parameters = operation.get("parameters") or []
    body_params = [
        _resolve_ref(spec, parameter)
        for parameter in parameters
        if isinstance(parameter, dict) or (isinstance(parameter, dict) and "$ref" in parameter)
    ]
    for parameter in body_params:
        if not isinstance(parameter, dict):
            continue
        if parameter.get("in") != "body":
            continue
        schema = _resolve_ref(spec, parameter.get("schema"))
        return _schema_to_payload(spec, schema)

    return None


def _schema_to_payload(spec: Dict[str, Any], schema: Any) -> Optional[Dict[str, Any]]:
    resolved = _resolve_ref(spec, schema)
    if not isinstance(resolved, dict):
        return None

    if "example" in resolved and isinstance(resolved["example"], dict):
        return resolved["example"]

    schema_type = resolved.get("type")
    if schema_type == "object" or "properties" in resolved:
        payload: Dict[str, Any] = {}
        for field_name, field_schema in (resolved.get("properties") or {}).items():
            payload[field_name] = _example_value(spec, field_schema)
        return payload or None

    return None


def _example_value(spec: Dict[str, Any], schema: Any) -> Any:
    resolved = _resolve_ref(spec, schema)
    if not isinstance(resolved, dict):
        return None

    if "example" in resolved:
        return resolved["example"]
    if "default" in resolved:
        return resolved["default"]

    schema_type = resolved.get("type")
    if schema_type == "string":
        enum = resolved.get("enum")
        return enum[0] if isinstance(enum, list) and enum else "string"
    if schema_type in {"integer", "number"}:
        return 0
    if schema_type == "boolean":
        return False
    if schema_type == "array":
        items = resolved.get("items")
        return [_example_value(spec, items)] if items else []
    if schema_type == "object" or "properties" in resolved:
        return {
            key: _example_value(spec, value)
            for key, value in (resolved.get("properties") or {}).items()
        }

    return None


def _resolve_ref(spec: Dict[str, Any], value: Any) -> Any:
    if not isinstance(value, dict):
        return value
    ref = value.get("$ref")
    if not ref:
        return value
    if not isinstance(ref, str) or not ref.startswith("#/"):
        return value

    current: Any = spec
    for part in ref[2:].split("/"):
        if not isinstance(current, dict):
            return value
        current = current.get(part)
        if current is None:
            return value
    return current
