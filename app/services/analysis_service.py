"""
analysis_service.py — Motor de evaluación de calidad de APIs
v2.0 — Reescritura completa

Reglas de evaluación (en orden de prioridad):
  1. Código HTTP: señal de mayor prioridad (5xx → CRITICAL, 4xx → MEDIUM)
  2. Score 0-100: penalidades por fallos reales, tasa de error y latencia
  3. Severidad: derivada de score + issues (nunca LOW si hay fallos reales)
  4. Issues: estructurados, deduplicados, ordenados por severidad descendente
  5. Insights: ordenados crítico → funcional → performance
"""

from __future__ import annotations

import json
from collections import defaultdict
from statistics import mean
from typing import Any, Dict, List, Optional, Tuple

# ─── Umbrales ─────────────────────────────────────────────────────────────────

_LATENCY_WARN_S     = 0.700   # 700 ms
_LATENCY_CRITICAL_S = 1.200   # 1 200 ms

_FALSE_POSITIVE_KEYWORDS = (
    "error", "invalid", "required", "missing", "fail", "bad request",
)

_TYPE_MAP: Dict[str, type] = {
    "str": str,     "string": str,
    "int": int,     "integer": int,
    "float": float, "number": float,
    "bool": bool,   "boolean": bool,
    "list": list,   "array": list,
    "dict": dict,   "object": dict,
}

# Orden numérico de severidades
_SEV_RANK: Dict[str, int] = {
    "CRITICAL": 4,
    "HIGH":     3,
    "MEDIUM":   2,
    "LOW":      1,
}

# Catálogo HTTP: código → (type_key, EN_message, ES_message, severity)
_HTTP_CATALOGUE: Dict[int, Tuple[str, str, str, str]] = {
    400: ("HTTP_400",
          "Bad Request — the server rejected invalid input",
          "Solicitud incorrecta — el servidor rechazó la petición", "MEDIUM"),
    401: ("HTTP_401",
          "Unauthorized — authentication is required",
          "No autorizado — se requiere autenticación", "MEDIUM"),
    403: ("HTTP_403",
          "Forbidden — access to this resource is denied",
          "Prohibido — acceso denegado al recurso", "MEDIUM"),
    404: ("HTTP_404",
          "Not Found — the endpoint does not exist",
          "No encontrado — el endpoint no existe", "MEDIUM"),
    405: ("HTTP_405",
          "Method Not Allowed — wrong HTTP verb for this endpoint",
          "Método no permitido — verbo HTTP incorrecto para este endpoint", "MEDIUM"),
    408: ("HTTP_408",
          "Request Timeout — server timed out waiting for the request",
          "Tiempo de espera agotado — el servidor tardó demasiado", "HIGH"),
    409: ("HTTP_409",
          "Conflict — resource state conflict detected",
          "Conflicto — conflicto de estado del recurso detectado", "MEDIUM"),
    422: ("HTTP_422",
          "Unprocessable Entity — validation error in request body",
          "Entidad no procesable — error de validación en el cuerpo", "MEDIUM"),
    429: ("HTTP_429",
          "Too Many Requests — rate limit has been exceeded",
          "Demasiadas solicitudes — límite de tasa superado", "HIGH"),
    500: ("HTTP_500",
          "Internal Server Error — server-side failure detected",
          "Error interno del servidor — fallo detectado en el servidor", "CRITICAL"),
    502: ("HTTP_502",
          "Bad Gateway — upstream service returned an invalid response",
          "Bad Gateway — servicio upstream retornó respuesta inválida", "CRITICAL"),
    503: ("HTTP_503",
          "Service Unavailable — server is overloaded or down",
          "Servicio no disponible — servidor sobrecargado o caído", "CRITICAL"),
    504: ("HTTP_504",
          "Gateway Timeout — upstream service did not respond in time",
          "Timeout del gateway — el servicio upstream no respondió a tiempo", "CRITICAL"),
}


# ─── Helpers privados ─────────────────────────────────────────────────────────

def _is_failure(result: Dict[str, Any]) -> bool:
    """
    Determina si un resultado es un fallo real según el contrato del test.

    Contratos esperados por test_name:
      valid_request            → 2xx  (falla si obtiene cualquier otra cosa)
      missing_payload          → 4xx  (falla si obtiene 2xx; la API no rechaza)
      invalid_types            → 4xx  (falla si obtiene 2xx; la API no valida)
      incomplete_payload       → 4xx  (ídem)
      no_query_params          → sin error de red
      custom (expected_status) → debe coincidir exactamente
      resto                    → 2xx
    """
    status   = result.get("status_code")
    error    = result.get("error")
    name     = result.get("test_name", "")
    expected = result.get("expected_status")

    if error or status is None:
        return True

    if expected is not None:
        return status != expected

    if name == "valid_request":
        return not (200 <= status < 300)

    if name in ("missing_payload", "invalid_types", "incomplete_payload"):
        # Esperamos rechazo (4xx); obtener 2xx es el fallo real
        return 200 <= status < 300

    if name == "no_query_params":
        return False  # Cualquier respuesta sin error de red es aceptable

    return not (200 <= status < 300)


def _add_issue(
    buckets: Dict[str, Dict[str, Any]],
    type_key: str,
    severity: str,
    msg_en: str,
    msg_es: str,
) -> None:
    """Agrega o incrementa un issue en el bucket, manteniendo la severidad máxima."""
    b = buckets[type_key]
    b["count"] += 1
    if _SEV_RANK.get(severity, 0) > _SEV_RANK.get(b.get("severity", "LOW"), 0):
        b["severity"] = severity
    b["msg_en"] = msg_en
    b["msg_es"] = msg_es


# ─── Detección de issues ──────────────────────────────────────────────────────

def _detect_http_issues(
    results: List[Dict[str, Any]],
    buckets: Dict[str, Dict[str, Any]],
) -> None:
    """Detecta issues basados en códigos de estado HTTP."""
    for r in results:
        status = r.get("status_code")
        name   = r.get("test_name", "")
        error  = r.get("error")

        # Error de red: sin respuesta del servidor
        if error and status is None:
            _add_issue(
                buckets, "NETWORK_ERROR", "CRITICAL",
                "Network error — no response received from server",
                "Error de red — sin respuesta del servidor",
            )
            continue

        if status is None:
            continue

        # Para valid_request: cualquier código fuera de 2xx es un issue
        if name == "valid_request" and not (200 <= status < 300):
            entry = _HTTP_CATALOGUE.get(status)
            if entry:
                _add_issue(buckets, entry[0], entry[3], entry[1], entry[2])
            elif status >= 500:
                _add_issue(
                    buckets, f"HTTP_{status}", "CRITICAL",
                    f"Server Error {status} — unexpected server-side failure",
                    f"Error {status} del servidor — fallo inesperado",
                )
            elif status >= 400:
                _add_issue(
                    buckets, f"HTTP_{status}", "MEDIUM",
                    f"Client Error {status} — the request was rejected by the server",
                    f"Error {status} de cliente — solicitud rechazada por el servidor",
                )

        # 5xx en CUALQUIER test siempre es CRITICAL (problema del servidor)
        elif status >= 500:
            entry = _HTTP_CATALOGUE.get(status)
            if entry:
                _add_issue(buckets, entry[0], "CRITICAL", entry[1], entry[2])
            else:
                _add_issue(
                    buckets, f"HTTP_{status}", "CRITICAL",
                    f"Server Error {status} on test '{name}'",
                    f"Error {status} del servidor en test '{name}'",
                )


def _detect_functional_issues(
    results: List[Dict[str, Any]],
    buckets: Dict[str, Dict[str, Any]],
) -> None:
    """Detecta issues de comportamiento funcional de la API."""
    for r in results:
        status   = r.get("status_code")
        name     = r.get("test_name", "")
        body     = (r.get("response_body") or "").lower()
        expected = r.get("expected_status")

        if status is None:
            continue

        # Payload vacío aceptado → falta validación de entrada
        if name == "missing_payload" and 200 <= status < 300:
            _add_issue(
                buckets, "MISSING_PAYLOAD_ACCEPTED", "HIGH",
                "API accepts requests without required payload — input validation is missing",
                "La API acepta solicitudes sin payload requerido — falta validación de entrada",
            )

        # Tipos inválidos aceptados → falta type-checking (grave)
        if name == "invalid_types" and 200 <= status < 300:
            _add_issue(
                buckets, "INVALID_TYPES_ACCEPTED", "CRITICAL",
                "API accepts invalid data types — type validation is missing",
                "La API acepta tipos de datos inválidos — falta validación de tipos",
            )

        # Falso positivo: HTTP 200 pero body contiene indicadores de error
        if (
            name == "valid_request"
            and 200 <= status < 300
            and any(kw in body for kw in _FALSE_POSITIVE_KEYWORDS)
        ):
            _add_issue(
                buckets, "FALSE_POSITIVE", "MEDIUM",
                "False positive: HTTP 200 but response body contains error indicators",
                "Falso positivo: HTTP 200 pero el body contiene indicadores de error",
            )

        # Custom case: expected_status mismatch
        if expected is not None and status != expected:
            _add_issue(
                buckets, f"EXPECTED_MISMATCH_{name.upper()}", "MEDIUM",
                f"Test '{name}': expected status {expected}, got {status}",
                f"Test '{name}': se esperaba status {expected}, se recibió {status}",
            )


def _detect_latency_issues(
    results: List[Dict[str, Any]],
    buckets: Dict[str, Dict[str, Any]],
) -> None:
    """Detecta issues de latencia basados en el promedio del run."""
    times = [r["response_time"] for r in results if r.get("response_time") is not None]
    if not times:
        return

    avg = mean(times)

    if avg > _LATENCY_CRITICAL_S:
        _add_issue(
            buckets, "HIGH_LATENCY_CRITICAL", "HIGH",
            f"Critical average response time: {avg * 1000:.0f} ms"
            f" (threshold: {_LATENCY_CRITICAL_S * 1000:.0f} ms)",
            f"Tiempo de respuesta promedio crítico: {avg * 1000:.0f} ms"
            f" (umbral: {_LATENCY_CRITICAL_S * 1000:.0f} ms)",
        )
    elif avg > _LATENCY_WARN_S:
        _add_issue(
            buckets, "HIGH_LATENCY_WARN", "MEDIUM",
            f"Elevated average response time: {avg * 1000:.0f} ms"
            f" (threshold: {_LATENCY_WARN_S * 1000:.0f} ms)",
            f"Tiempo de respuesta promedio elevado: {avg * 1000:.0f} ms"
            f" (umbral: {_LATENCY_WARN_S * 1000:.0f} ms)",
        )


def _detect_schema_issues(
    results: List[Dict[str, Any]],
    expected_schema: Dict[str, str],
    buckets: Dict[str, Dict[str, Any]],
) -> None:
    """Valida el body del valid_request contra el schema esperado."""
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
            _add_issue(
                buckets, f"SCHEMA_MISSING_{field.upper()}", "MEDIUM",
                f"Schema: field '{field}' is missing from the response",
                f"Schema: campo '{field}' ausente en la respuesta",
            )
            continue

        expected_type = _TYPE_MAP.get(type_str.lower())
        if expected_type and not isinstance(body[field], expected_type):
            actual = type(body[field]).__name__
            _add_issue(
                buckets, f"SCHEMA_TYPE_{field.upper()}", "LOW",
                f"Schema: field '{field}' expected {type_str}, got {actual}",
                f"Schema: campo '{field}' debería ser {type_str}, se recibió {actual}",
            )


# ─── Score ────────────────────────────────────────────────────────────────────

def _calculate_score(
    summary: Dict[str, Any],
    issues: List[Dict[str, Any]],
) -> int:
    """
    Inicia en 100 y aplica penalidades:
      - ANY 5xx o error de red    → techo máximo de 40
      - Cada test fallido          → -15
      - Tasa de fallo > 50 %      → -30 adicional; 100 % → -50
      - Cada 4xx en valid_request  → -10 (máx -40)
      - Latencia > 1 200 ms        → -10
      - Latencia > 700 ms          → -5
      - INVALID_TYPES_ACCEPTED     → -20
      - MISSING_PAYLOAD_ACCEPTED   → -10
      - FALSE_POSITIVE             → -5
    Score final clampeado a [0, 100].
    """
    score     = 100
    failed    = summary["failed"]
    fail_rate = summary["fail_rate"]
    ikeys     = {i["type"] for i in issues}

    # Techo por 5xx o error de red
    if any(k.startswith("HTTP_5") or k == "NETWORK_ERROR" for k in ikeys):
        score = min(score, 40)

    # Penalidad por tests fallidos
    score -= failed * 15

    # Penalidad por tasa de fallo
    if fail_rate >= 100:
        score -= 50
    elif fail_rate > 50:
        score -= 30

    # Penalidad por 4xx (capped)
    http_4xx = sum(1 for i in issues if i["type"].startswith("HTTP_4"))
    score -= min(http_4xx * 10, 40)

    # Penalidad por latencia
    if "HIGH_LATENCY_CRITICAL" in ikeys:
        score -= 10
    elif "HIGH_LATENCY_WARN" in ikeys:
        score -= 5

    # Penalidad por issues funcionales
    for key, penalty in (
        ("INVALID_TYPES_ACCEPTED",   20),
        ("MISSING_PAYLOAD_ACCEPTED", 10),
        ("FALSE_POSITIVE",            5),
    ):
        if key in ikeys:
            score -= penalty

    return max(0, min(100, score))


# ─── Severidad ────────────────────────────────────────────────────────────────

def _determine_severity(score: int, issues: List[Dict[str, Any]]) -> str:
    """
    CRITICAL : issue CRITICAL presente o score < 40
    HIGH     : issue HIGH presente o score < 60
    MEDIUM   : issue MEDIUM presente o score < 80
    LOW      : sin issues o score >= 80
    """
    worst = max((_SEV_RANK.get(i["severity"], 0) for i in issues), default=0)

    if worst >= _SEV_RANK["CRITICAL"] or score < 40:
        return "CRITICAL"
    if worst >= _SEV_RANK["HIGH"] or score < 60:
        return "HIGH"
    if worst >= _SEV_RANK["MEDIUM"] or score < 80:
        return "MEDIUM"
    return "LOW"


# ─── Insights (fallback local) ────────────────────────────────────────────────

def _generate_local_insights(
    issues: List[Dict[str, Any]],
    score: int,
    summary: Dict[str, Any],
    method: str,
    url: str,
) -> List[str]:
    """
    Genera insights bilingües (EN · ES) cuando Ollama no está disponible.
    Orden de prioridad: crítico → funcional → performance → schema.
    """
    insights: List[str] = []
    ikeys = {i["type"] for i in issues}

    # ── Críticos ──────────────────────────────────────────────────────────────
    if "NETWORK_ERROR" in ikeys:
        insights.append(
            "CRITICAL: The endpoint is unreachable — verify the URL and server status · "
            "CRÍTICO: El endpoint no es accesible — verificá la URL y el estado del servidor"
        )
    if any(k.startswith("HTTP_5") for k in ikeys):
        insights.append(
            "CRITICAL: Server errors detected — review application logs and error handling · "
            "CRÍTICO: Se detectaron errores del servidor — revisá los logs y el manejo de errores"
        )
    if "INVALID_TYPES_ACCEPTED" in ikeys:
        insights.append(
            "CRITICAL: The API does not validate input types — add strict type checking on all endpoints · "
            "CRÍTICO: La API no valida tipos de datos — agregá validación estricta de tipos en todos los endpoints"
        )

    # ── Funcionales ───────────────────────────────────────────────────────────
    if "HTTP_405" in ikeys:
        insights.append(
            f"The endpoint rejects {method} requests — confirm the correct HTTP method in the API docs · "
            f"El endpoint rechaza solicitudes {method} — confirmá el método HTTP correcto en la documentación"
        )
    elif any(k.startswith("HTTP_4") for k in ikeys):
        insights.append(
            "Client errors detected — verify request format, authentication and endpoint URL · "
            "Se detectaron errores de cliente — verificá el formato de solicitud, autenticación y URL"
        )
    if "MISSING_PAYLOAD_ACCEPTED" in ikeys:
        insights.append(
            "HIGH: The API accepts requests without required payload — implement input validation · "
            "ALTO: La API acepta solicitudes sin payload requerido — implementá validación de entrada"
        )
    if "FALSE_POSITIVE" in ikeys:
        insights.append(
            "HTTP 200 returned but response body contains error terms — review response normalization · "
            "Se retorna HTTP 200 pero el body contiene términos de error — revisá la normalización de respuestas"
        )

    # ── Performance ───────────────────────────────────────────────────────────
    if "HIGH_LATENCY_CRITICAL" in ikeys:
        insights.append(
            f"Response times exceed {_LATENCY_CRITICAL_S * 1000:.0f} ms — "
            "consider caching, query optimization or CDN · "
            f"Los tiempos de respuesta superan {_LATENCY_CRITICAL_S * 1000:.0f} ms — "
            "considerá caché, optimización de queries o CDN"
        )
    elif "HIGH_LATENCY_WARN" in ikeys:
        insights.append(
            f"Response times exceed {_LATENCY_WARN_S * 1000:.0f} ms — "
            "investigate slow database queries or network overhead · "
            f"Los tiempos de respuesta superan {_LATENCY_WARN_S * 1000:.0f} ms — "
            "investigá queries lentos o sobrecarga de red"
        )

    # ── Schema ────────────────────────────────────────────────────────────────
    schema_count = sum(1 for i in issues if i["type"].startswith("SCHEMA_"))
    if schema_count:
        insights.append(
            f"{schema_count} schema violation(s) detected — "
            "ensure the response contract matches the defined schema · "
            f"{schema_count} violación(es) de schema detectadas — "
            "asegurate de que el contrato de respuesta coincida con el schema definido"
        )

    # ── Sin issues ────────────────────────────────────────────────────────────
    if not insights:
        if score == 100:
            insights.append(
                "All tests passed with excellent performance — the API is behaving correctly · "
                "Todos los tests pasaron con rendimiento excelente — la API funciona correctamente"
            )
        else:
            insights.append(
                "No critical issues detected — the API is healthy · "
                "No se detectaron issues críticos — la API está saludable"
            )

    return insights


# ─── Resumen estadístico ──────────────────────────────────────────────────────

def _build_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total  = len(results)
    failed = sum(1 for r in results if _is_failure(r))
    passed = total - failed
    return {
        "total_tests": total,
        "passed":      passed,
        "failed":      failed,
        "fail_rate":   round((failed / total * 100), 1) if total > 0 else 0.0,
    }


# ─── Entrada principal ────────────────────────────────────────────────────────

def analyze(
    results: List[Dict[str, Any]],
    method: str = "",
    url: str = "",
    expected_schema: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Motor de evaluación principal.

    Salida (compatible con el frontend existente + campo summary nuevo):
    {
        "issues":        List[str],        # mensajes bilingües para el dashboard
        "severity":      str,              # LOW | MEDIUM | HIGH | CRITICAL
        "quality_score": int,              # 0-100
        "insights":      List[str],        # recomendaciones priorizadas
        "summary": {
            "total_tests": int,
            "passed":      int,
            "failed":      int,
            "fail_rate":   float,
        }
    }
    """
    # 1. Resumen estadístico (semántica de pass/fail por contrato de test)
    summary = _build_summary(results)

    # 2. Detección de issues en buckets para deduplicar
    buckets: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"count": 0, "severity": "LOW", "msg_en": "", "msg_es": ""}
    )
    _detect_http_issues(results, buckets)
    _detect_functional_issues(results, buckets)
    _detect_latency_issues(results, buckets)
    if expected_schema:
        _detect_schema_issues(results, expected_schema, buckets)

    # 3. Lista de issues estructurados, ordenada por severidad descendente
    structured: List[Dict[str, Any]] = sorted(
        [
            {
                "type":     key,
                "count":    data["count"],
                "severity": data["severity"],
                "message":  f"{data['msg_en']} · {data['msg_es']}",
            }
            for key, data in buckets.items()
        ],
        key=lambda x: _SEV_RANK.get(x["severity"], 0),
        reverse=True,
    )

    # 4. Score y severidad
    score    = _calculate_score(summary, structured)
    severity = _determine_severity(score, structured)

    # 5. Insights — Ollama con fallback al engine local
    try:
        from app.services.ai_service import generate_ai_insights

        ai = generate_ai_insights(
            results=results,
            issues=[i["message"] for i in structured],
            score=score,
            method=method,
            url=url,
        )
        insights = ai if ai else _generate_local_insights(structured, score, summary, method, url)
    except Exception:
        insights = _generate_local_insights(structured, score, summary, method, url)

    return {
        "issues":        [i["message"] for i in structured],
        "severity":      severity,
        "quality_score": score,
        "insights":      insights,
        "summary":       summary,
    }
