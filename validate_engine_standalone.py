#!/usr/bin/env python3
"""
Standalone validation of evaluation engine (no app imports to avoid timeout)
All logic copied directly from analysis_service.py
"""

import json
from collections import defaultdict
from statistics import mean
from typing import Any, Dict, List, Optional, Tuple

# ─── Constantes ───────────────────────────────────────────────────────────────

_LATENCY_WARN_S = 0.700
_LATENCY_CRITICAL_S = 1.200

_FALSE_POSITIVE_KEYWORDS = (
    "error", "invalid", "required", "missing", "fail", "bad request",
)

_TYPE_MAP: Dict[str, type] = {
    "str": str, "string": str,
    "int": int, "integer": int,
    "float": float, "number": float,
    "bool": bool, "boolean": bool,
    "list": list, "array": list,
    "dict": dict, "object": dict,
}

_SEV_RANK: Dict[str, int] = {
    "CRITICAL": 4,
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1,
}

_HTTP_CATALOGUE: Dict[int, Tuple[str, str, str, str]] = {
    400: ("HTTP_400", "Bad Request — the server rejected invalid input",
          "Solicitud incorrecta — el servidor rechazó la petición", "MEDIUM"),
    401: ("HTTP_401", "Unauthorized — authentication is required",
          "No autorizado — se requiere autenticación", "MEDIUM"),
    403: ("HTTP_403", "Forbidden — access to this resource is denied",
          "Prohibido — acceso denegado al recurso", "MEDIUM"),
    404: ("HTTP_404", "Not Found — the endpoint does not exist",
          "No encontrado — el endpoint no existe", "MEDIUM"),
    405: ("HTTP_405", "Method Not Allowed — wrong HTTP verb for this endpoint",
          "Método no permitido — verbo HTTP incorrecto para este endpoint", "MEDIUM"),
    408: ("HTTP_408", "Request Timeout — server timed out waiting for the request",
          "Tiempo de espera agotado — el servidor tardó demasiado", "HIGH"),
    409: ("HTTP_409", "Conflict — resource state conflict detected",
          "Conflicto — conflicto de estado del recurso detectado", "MEDIUM"),
    422: ("HTTP_422", "Unprocessable Entity — validation error in request body",
          "Entidad no procesable — error de validación en el cuerpo", "MEDIUM"),
    429: ("HTTP_429", "Too Many Requests — rate limit has been exceeded",
          "Demasiadas solicitudes — límite de tasa superado", "HIGH"),
    500: ("HTTP_500", "Internal Server Error — server-side failure detected",
          "Error interno del servidor — fallo detectado en el servidor", "CRITICAL"),
    502: ("HTTP_502", "Bad Gateway — upstream service returned an invalid response",
          "Bad Gateway — servicio upstream retornó respuesta inválida", "CRITICAL"),
    503: ("HTTP_503", "Service Unavailable — server is overloaded or down",
          "Servicio no disponible — servidor sobrecargado o caído", "CRITICAL"),
    504: ("HTTP_504", "Gateway Timeout — upstream service did not respond in time",
          "Timeout del gateway — el servicio upstream no respondió a tiempo", "CRITICAL"),
}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _is_failure(result: Dict[str, Any]) -> bool:
    status = result.get("status_code")
    error = result.get("error")
    name = result.get("test_name", "")
    expected = result.get("expected_status")

    if error or status is None:
        return True

    if expected is not None:
        return status != expected

    if name == "valid_request":
        return not (200 <= status < 300)

    if name in ("missing_payload", "invalid_types", "incomplete_payload"):
        return 200 <= status < 300

    if name == "no_query_params":
        return False

    return not (200 <= status < 300)


def _add_issue(buckets: Dict[str, Dict[str, Any]], type_key: str, severity: str,
               msg_en: str, msg_es: str) -> None:
    b = buckets[type_key]
    b["count"] += 1
    if _SEV_RANK.get(severity, 0) > _SEV_RANK.get(b.get("severity", "LOW"), 0):
        b["severity"] = severity
    b["msg_en"] = msg_en
    b["msg_es"] = msg_es


def _detect_http_issues(results: List[Dict[str, Any]], buckets: Dict[str, Dict[str, Any]]) -> None:
    for r in results:
        status = r.get("status_code")
        name = r.get("test_name", "")
        error = r.get("error")

        if error and status is None:
            _add_issue(buckets, "NETWORK_ERROR", "CRITICAL",
                      "Network error — no response received from server",
                      "Error de red — sin respuesta del servidor")
            continue

        if status is None:
            continue

        if name == "valid_request" and not (200 <= status < 300):
            entry = _HTTP_CATALOGUE.get(status)
            if entry:
                _add_issue(buckets, entry[0], entry[3], entry[1], entry[2])
            elif status >= 500:
                _add_issue(buckets, f"HTTP_{status}", "CRITICAL",
                          f"Server Error {status} — unexpected server-side failure",
                          f"Error {status} del servidor — fallo inesperado")
            elif status >= 400:
                _add_issue(buckets, f"HTTP_{status}", "MEDIUM",
                          f"Client Error {status} — the request was rejected by the server",
                          f"Error {status} de cliente — solicitud rechazada por el servidor")

        elif status >= 500:
            entry = _HTTP_CATALOGUE.get(status)
            if entry:
                _add_issue(buckets, entry[0], "CRITICAL", entry[1], entry[2])
            else:
                _add_issue(buckets, f"HTTP_{status}", "CRITICAL",
                          f"Server Error {status} on test '{name}'",
                          f"Error {status} del servidor en test '{name}'")


def _detect_functional_issues(results: List[Dict[str, Any]], buckets: Dict[str, Dict[str, Any]]) -> None:
    for r in results:
        status = r.get("status_code")
        name = r.get("test_name", "")
        body = (r.get("response_body") or "").lower()
        expected = r.get("expected_status")

        if status is None:
            continue

        if name == "missing_payload" and 200 <= status < 300:
            _add_issue(buckets, "MISSING_PAYLOAD_ACCEPTED", "HIGH",
                      "API accepts requests without required payload — input validation is missing",
                      "La API acepta solicitudes sin payload requerido — falta validación de entrada")

        if name == "invalid_types" and 200 <= status < 300:
            _add_issue(buckets, "INVALID_TYPES_ACCEPTED", "CRITICAL",
                      "API accepts invalid data types — type validation is missing",
                      "La API acepta tipos de datos inválidos — falta validación de tipos")

        if (name == "valid_request" and 200 <= status < 300 and
            any(kw in body for kw in _FALSE_POSITIVE_KEYWORDS)):
            _add_issue(buckets, "FALSE_POSITIVE", "MEDIUM",
                      "False positive: HTTP 200 but response body contains error indicators",
                      "Falso positivo: HTTP 200 pero el body contiene indicadores de error")

        if expected is not None and status != expected:
            _add_issue(buckets, f"EXPECTED_MISMATCH_{name.upper()}", "MEDIUM",
                      f"Test '{name}': expected status {expected}, got {status}",
                      f"Test '{name}': se esperaba status {expected}, se recibió {status}")


def _detect_latency_issues(results: List[Dict[str, Any]], buckets: Dict[str, Dict[str, Any]]) -> None:
    times = [r["response_time"] for r in results if r.get("response_time") is not None]
    if not times:
        return

    avg = mean(times)

    if avg > _LATENCY_CRITICAL_S:
        _add_issue(buckets, "HIGH_LATENCY_CRITICAL", "HIGH",
                  f"Critical average response time: {avg * 1000:.0f} ms (threshold: {_LATENCY_CRITICAL_S * 1000:.0f} ms)",
                  f"Tiempo de respuesta promedio crítico: {avg * 1000:.0f} ms (umbral: {_LATENCY_CRITICAL_S * 1000:.0f} ms)")
    elif avg > _LATENCY_WARN_S:
        _add_issue(buckets, "HIGH_LATENCY_WARN", "MEDIUM",
                  f"Elevated average response time: {avg * 1000:.0f} ms (threshold: {_LATENCY_WARN_S * 1000:.0f} ms)",
                  f"Tiempo de respuesta promedio elevado: {avg * 1000:.0f} ms (umbral: {_LATENCY_WARN_S * 1000:.0f} ms)")


def _detect_schema_issues(results: List[Dict[str, Any]], expected_schema: Dict[str, str],
                         buckets: Dict[str, Dict[str, Any]]) -> None:
    if not expected_schema:
        return

    valid = next((r for r in results if r.get("test_name") == "valid_request"), None)
    if not valid or not valid.get("response_body"):
        return

    try:
        body = json.loads(valid["response_body"])
    except (json.JSONDecodeError, TypeError):
        return

    if not isinstance(body, dict):
        return

    for field, type_str in expected_schema.items():
        if field not in body:
            _add_issue(buckets, f"SCHEMA_MISSING_{field.upper()}", "MEDIUM",
                      f"Schema: field '{field}' is missing from the response",
                      f"Schema: campo '{field}' ausente en la respuesta")
            continue

        expected_type = _TYPE_MAP.get(type_str.lower())
        if expected_type and not isinstance(body[field], expected_type):
            actual = type(body[field]).__name__
            _add_issue(buckets, f"SCHEMA_TYPE_{field.upper()}", "LOW",
                      f"Schema: field '{field}' expected {type_str}, got {actual}",
                      f"Schema: campo '{field}' debería ser {type_str}, se recibió {actual}")


def _calculate_score(summary: Dict[str, Any], issues: List[Dict[str, Any]]) -> int:
    score = 100
    failed = summary["failed"]
    fail_rate = summary["fail_rate"]
    ikeys = {i["type"] for i in issues}

    if any(k.startswith("HTTP_5") or k == "NETWORK_ERROR" for k in ikeys):
        score = min(score, 40)

    score -= failed * 15

    if fail_rate >= 100:
        score -= 50
    elif fail_rate > 50:
        score -= 30

    http_4xx = sum(1 for i in issues if i["type"].startswith("HTTP_4"))
    score -= min(http_4xx * 10, 40)

    if "HIGH_LATENCY_CRITICAL" in ikeys:
        score -= 10
    elif "HIGH_LATENCY_WARN" in ikeys:
        score -= 5

    for key, penalty in (("INVALID_TYPES_ACCEPTED", 20), ("MISSING_PAYLOAD_ACCEPTED", 10), ("FALSE_POSITIVE", 5)):
        if key in ikeys:
            score -= penalty

    return max(0, min(100, score))


def _determine_severity(score: int, issues: List[Dict[str, Any]]) -> str:
    worst = max((_SEV_RANK.get(i["severity"], 0) for i in issues), default=0)

    if worst >= _SEV_RANK["CRITICAL"] or score < 40:
        return "CRITICAL"
    if worst >= _SEV_RANK["HIGH"] or score < 60:
        return "HIGH"
    if worst >= _SEV_RANK["MEDIUM"] or score < 80:
        return "MEDIUM"
    return "LOW"


def _build_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(results)
    failed = sum(1 for r in results if _is_failure(r))
    passed = total - failed
    return {
        "total_tests": total,
        "passed": passed,
        "failed": failed,
        "fail_rate": round((failed / total * 100), 1) if total > 0 else 0.0,
    }


def analyze(results: List[Dict[str, Any]], method: str = "", url: str = "",
           expected_schema: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    summary = _build_summary(results)

    buckets: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"count": 0, "severity": "LOW", "msg_en": "", "msg_es": ""}
    )
    _detect_http_issues(results, buckets)
    _detect_functional_issues(results, buckets)
    _detect_latency_issues(results, buckets)
    if expected_schema:
        _detect_schema_issues(results, expected_schema, buckets)

    structured: List[Dict[str, Any]] = sorted(
        [{"type": key, "count": data["count"], "severity": data["severity"],
          "message": f"{data['msg_en']} · {data['msg_es']}"} for key, data in buckets.items()],
        key=lambda x: _SEV_RANK.get(x["severity"], 0),
        reverse=True,
    )

    score = _calculate_score(summary, structured)
    severity = _determine_severity(score, structured)

    return {
        "issues": [i["message"] for i in structured],
        "severity": severity,
        "quality_score": score,
        "summary": summary,
    }


# ─── Test Cases ───────────────────────────────────────────────────────────────

TEST_1 = {
    "name": "TEST 1: Baseline (all tests pass, no issues)",
    "results": [
        {"test_name": "valid_request", "status_code": 200, "response_time": 0.15, "error": None, "response_body": '{"status": "ok"}'},
        {"test_name": "no_query_params", "status_code": 200, "response_time": 0.12, "error": None, "response_body": '{}'},
    ],
    "expected": {
        "quality_score": (90, 100),
        "severity": "LOW",
        "failed_count": 0,
        "issues_empty": True,
    }
}

TEST_2 = {
    "name": "TEST 2: 4xx error detected",
    "results": [
        {"test_name": "valid_request", "status_code": 200, "response_time": 0.15, "error": None, "response_body": '{}'},
        {"test_name": "missing_payload", "status_code": 400, "response_time": 0.08, "error": None, "response_body": '{}'},
    ],
    "expected": {
        "quality_score": (60, 80),
        "severity": "MEDIUM",
        "failed_count": 1,
        "has_http_400": True,
    }
}

TEST_3 = {
    "name": "TEST 3: 100% failure rate (must NOT be 100)",
    "results": [
        {"test_name": "valid_request", "status_code": 405, "response_time": 0.15, "error": None, "response_body": '{}'},
        {"test_name": "missing_payload", "status_code": 405, "response_time": 0.08, "error": None, "response_body": '{}'},
    ],
    "expected": {
        "quality_score": (30, 60),
        "severity": ("HIGH", "CRITICAL"),
        "quality_score_not_100": True,
        "failed_count": 2,
        "has_http_405": True,
    }
}

TEST_4 = {
    "name": "TEST 4: 5xx error (MUST be CRITICAL)",
    "results": [
        {"test_name": "valid_request", "status_code": 503, "response_time": 0.15, "error": None, "response_body": '{}'},
    ],
    "expected": {
        "quality_score": (0, 40),
        "severity": "CRITICAL",
        "failed_count": 1,
        "has_http_503": True,
    }
}

TEST_5 = {
    "name": "TEST 5: Mixed 4xx + 5xx",
    "results": [
        {"test_name": "valid_request", "status_code": 400, "response_time": 0.15, "error": None, "response_body": '{}'},
        {"test_name": "missing_payload", "status_code": 500, "response_time": 0.08, "error": None, "response_body": '{}'},
    ],
    "expected": {
        "quality_score": (0, 50),
        "severity": "CRITICAL",
        "failed_count": 2,
        "has_http_400": True,
        "has_http_500": True,
    }
}

TEST_6 = {
    "name": "TEST 6: High latency (performance issue)",
    "results": [
        {"test_name": "valid_request", "status_code": 200, "response_time": 0.8, "error": None, "response_body": '{}'},
        {"test_name": "no_query_params", "status_code": 200, "response_time": 0.9, "error": None, "response_body": '{}'},
    ],
    "expected": {
        "quality_score": (70, 90),
        "severity": ("LOW", "MEDIUM"),
        "failed_count": 0,
        "has_high_latency": True,
    }
}


# ─── Validation ───────────────────────────────────────────────────────────────

def validate_test(test_case: Dict[str, Any]) -> Tuple[bool, str]:
    test_name = test_case["name"]
    results = test_case["results"]
    expected = test_case["expected"]

    output = analyze(results)
    score = output["quality_score"]
    severity = output["severity"]
    summary = output["summary"]
    issues = output["issues"]

    errors = []

    # Score range check
    min_score, max_score = expected["quality_score"]
    if not (min_score <= score <= max_score):
        errors.append(f"Score {score} outside expected range [{min_score}, {max_score}]")

    # Severity check
    if isinstance(expected["severity"], tuple):
        if severity not in expected["severity"]:
            errors.append(f"Severity {severity} not in {expected['severity']}")
    else:
        if severity != expected["severity"]:
            errors.append(f"Severity {severity} != {expected['severity']}")

    # Failed count
    if expected.get("failed_count") is not None and summary["failed"] != expected["failed_count"]:
        errors.append(f"Failed count {summary['failed']} != {expected['failed_count']}")

    # Issues empty check
    if expected.get("issues_empty") and issues:
        errors.append(f"Expected no issues but got: {issues}")

    # HTTP code checks
    issues_str = " ".join(issues)
    if expected.get("has_http_400") and "HTTP_400" not in issues_str:
        errors.append("Expected HTTP_400 issue not found")
    if expected.get("has_http_405") and "HTTP_405" not in issues_str:
        errors.append("Expected HTTP_405 issue not found")
    if expected.get("has_http_503") and "HTTP_503" not in issues_str:
        errors.append("Expected HTTP_503 issue not found")
    if expected.get("has_http_500") and "HTTP_500" not in issues_str:
        errors.append("Expected HTTP_500 issue not found")

    # Special checks
    if expected.get("quality_score_not_100") and score == 100:
        errors.append(f"Score must NOT be 100 on 100% failure (got 100)")

    if expected.get("has_high_latency") and "HIGH_LATENCY" not in issues_str:
        errors.append("Expected HIGH_LATENCY issue not found")

    if errors:
        return False, "\n  ".join(["FAIL: " + test_name] + errors)
    else:
        return True, f"PASS: {test_name}"


# ─── Run All Tests ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [TEST_1, TEST_2, TEST_3, TEST_4, TEST_5, TEST_6]
    results = []

    print("\n" + "=" * 80)
    print("VALIDATION SUITE — Evaluation Engine v2.0")
    print("=" * 80 + "\n")

    for test_case in tests:
        passed, message = validate_test(test_case)
        results.append(passed)
        print(message)

    print("\n" + "=" * 80)
    passed_count = sum(results)
    total_count = len(results)
    print(f"SUMMARY: {passed_count}/{total_count} tests passed")
    print("=" * 80 + "\n")

    exit(0 if all(results) else 1)
