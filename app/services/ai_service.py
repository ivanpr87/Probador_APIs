from typing import Any, Dict, List

import requests

from app.core.config import settings

_FALLBACK_NO_ISSUES = [
    "No se detectaron problemas en los tests ejecutados · "
    "No issues detected in the executed tests."
]

_FALLBACK_PAYLOAD = (
    "La API no valida campos requeridos. Puede aceptar solicitudes incompletas sin retornar error. "
    "Riesgo: datos corruptos o comportamiento inesperado en producción · "
    "The API does not validate required fields. It may silently accept incomplete requests. "
    "Risk: corrupt data or unexpected behavior in production."
)

_FALLBACK_TYPES = (
    "La API no valida tipos de datos. Acepta strings donde espera números y viceversa. "
    "Riesgo: errores de base de datos o fallos en producción · "
    "The API does not validate data types. It accepts strings where numbers are expected and vice versa. "
    "Risk: database errors or production failures."
)

_FALLBACK_SLOW = (
    "El tiempo de respuesta promedio es elevado. "
    "Considerar optimización de queries o caching · "
    "Average response time is high. "
    "Consider query optimization or caching."
)

_FALLBACK_FALSE_POSITIVE = (
    "La API retorna 200 con contenido de error en el body. "
    "Falso positivo: la validación existe pero no usa códigos HTTP correctos · "
    "The API returns 200 with error content in the body. "
    "False positive: validation exists but does not use correct HTTP status codes."
)


def _build_fallback(issues: List[str]) -> List[str]:
    if not issues:
        return _FALLBACK_NO_ISSUES
    seen: set = set()
    insights = []
    for issue in issues:
        il = issue.lower()
        # Cobertura ampliada para los nuevos tipos de issue del motor v2
        if any(k in il for k in ("without payload", "sin payload", "missing_payload")):
            if _FALLBACK_PAYLOAD not in seen:
                seen.add(_FALLBACK_PAYLOAD); insights.append(_FALLBACK_PAYLOAD)
        elif any(k in il for k in ("invalid data types", "tipos de datos", "invalid_types")):
            if _FALLBACK_TYPES not in seen:
                seen.add(_FALLBACK_TYPES); insights.append(_FALLBACK_TYPES)
        elif any(k in il for k in ("response time", "tiempo de respuesta", "latency")):
            if _FALLBACK_SLOW not in seen:
                seen.add(_FALLBACK_SLOW); insights.append(_FALLBACK_SLOW)
        elif any(k in il for k in ("false positive", "falso positivo")):
            if _FALLBACK_FALSE_POSITIVE not in seen:
                seen.add(_FALLBACK_FALSE_POSITIVE); insights.append(_FALLBACK_FALSE_POSITIVE)
    return insights or _FALLBACK_NO_ISSUES


def _format_results_for_prompt(results: List[Dict[str, Any]]) -> str:
    lines = []
    for r in results:
        status = r.get("status_code", "—")
        time_ms = f"{r.get('response_time', 0) * 1000:.0f}ms" if r.get("response_time") else "—"
        body = (r.get("response_body") or "")[:120].replace("\n", " ")
        error = r.get("error", "")
        line = f"  • {r['test_name']}: HTTP {status} | {time_ms}"
        if body:
            line += f" | body: {body}"
        if error:
            line += f" | error: {error}"
        lines.append(line)
    return "\n".join(lines)


def generate_ai_insights(
    results: List[Dict[str, Any]],
    issues: List[str],
    score: int,
    method: str,
    url: str,
) -> List[str]:
    issues_text = "\n".join(f"  - {i}" for i in issues) if issues else "  (ninguno)"
    results_text = _format_results_for_prompt(results)

    system_msg = (
        "Eres un experto en calidad de APIs REST. "
        "Tu tarea es analizar resultados de tests automáticos y generar insights accionables. "
        "REGLA CRÍTICA: cada insight DEBE seguir exactamente este formato en una sola línea: "
        "[ES] texto en español · [EN] text in English. "
        "Genera entre 2 y 3 insights. Sé específico y accionable. No repitas los issues — complementalos."
    )

    user_msg = (
        f"Analiza los siguientes resultados de tests para {method} {url}:\n\n"
        f"{results_text}\n\n"
        f"Score de calidad: {score}/100\n"
        f"Problemas detectados:\n{issues_text}\n\n"
        "Genera 2-3 insights accionables. Una línea por insight, formato obligatorio: "
        "[ES] insight en español · [EN] insight in English"
    )

    try:
        response = requests.post(
            f"{settings.OLLAMA_URL}/api/chat",
            json={
                "model": settings.OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                ],
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 400},
            },
            timeout=settings.OLLAMA_TIMEOUT,
        )
        response.raise_for_status()
        content = response.json()["message"]["content"].strip()
        insights = _parse_insights(content)
        return insights if insights else _build_fallback(issues)

    except Exception:
        return _build_fallback(issues)


def _parse_insights(raw: str) -> List[str]:
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    insights = []
    for line in lines:
        # Acepta líneas que arrancan con [ES] o que contienen el separador ·
        if "[ES]" in line and "·" in line and "[EN]" in line:
            insights.append(line)
        elif line.startswith("-") and "·" in line:
            insights.append(line.lstrip("- ").strip())
    return insights[:3]
