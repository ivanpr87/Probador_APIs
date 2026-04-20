from statistics import mean
from typing import Any, Dict, List

_FALSE_POSITIVE_KEYWORDS = ("error", "invalid", "required", "missing", "fail", "bad request")

# Umbrales de response time (segundos)
_TIME_CRITICAL = 3.0
_TIME_WARN = 1.5


def _avg_response_time(results: List[Dict[str, Any]]) -> float:
    times = [r["response_time"] for r in results if r.get("response_time") is not None]
    return mean(times) if times else 0.0


def detect_issues(results: List[Dict[str, Any]]) -> List[str]:
    issues = []

    for result in results:
        test_name = result.get("test_name")
        status = result.get("status_code")
        body = (result.get("response_body") or "").lower()

        if test_name == "missing_payload" and status in (200, 201):
            issues.append(
                "La API acepta solicitudes sin payload — falta validación de campos requeridos · "
                "API accepts requests without payload — required field validation is missing"
            )

        if test_name == "invalid_types" and status in (200, 201):
            issues.append(
                "La API acepta tipos de datos inválidos — falta validación de tipos · "
                "API accepts invalid data types — type validation is missing"
            )

        if (
            test_name == "valid_request"
            and status in (200, 201)
            and any(kw in body for kw in _FALSE_POSITIVE_KEYWORDS)
        ):
            issues.append(
                "Falso positivo: la API retorna 200 pero el body contiene indicadores de error · "
                "False positive: API returns 200 but response body contains error indicators"
            )

    avg = _avg_response_time(results)
    if avg >= _TIME_CRITICAL:
        issues.append(
            f"Tiempo de respuesta crítico: {avg:.2f}s promedio (umbral: {_TIME_CRITICAL}s) · "
            f"Critical response time: {avg:.2f}s average (threshold: {_TIME_CRITICAL}s)"
        )
    elif avg >= _TIME_WARN:
        issues.append(
            f"Tiempo de respuesta elevado: {avg:.2f}s promedio (umbral recomendado: {_TIME_WARN}s) · "
            f"High response time: {avg:.2f}s average (recommended threshold: {_TIME_WARN}s)"
        )

    return issues


def calculate_score(issues: List[str], results: List[Dict[str, Any]]) -> int:
    score = 100

    for issue in issues:
        if "without payload" in issue or "sin payload" in issue:
            score -= 30
        elif "invalid data types" in issue or "tipos de datos" in issue:
            score -= 40
        elif "false positive" in issue.lower() or "falso positivo" in issue.lower():
            score -= 15
        elif "response time" in issue.lower() or "tiempo de respuesta" in issue.lower():
            avg = _avg_response_time(results)
            score -= 20 if avg >= _TIME_CRITICAL else 10

    return max(score, 0)


def determine_severity(issues: List[str]) -> str:
    if any("invalid data types" in i or "tipos de datos" in i for i in issues):
        return "critical"
    if any(
        "without payload" in i
        or "sin payload" in i
        or "critical response time" in i.lower()
        or "tiempo de respuesta crítico" in i.lower()
        for i in issues
    ):
        return "high"
    if issues:
        return "high"
    return "low"


def analyze(results: List[Dict[str, Any]], method: str = "", url: str = "") -> Dict[str, Any]:
    from app.services.ai_service import generate_ai_insights

    issues = detect_issues(results)
    score = calculate_score(issues, results)

    ai_insights = generate_ai_insights(
        results=results,
        issues=issues,
        score=score,
        method=method,
        url=url,
    )

    return {
        "issues": issues,
        "severity": determine_severity(issues),
        "quality_score": score,
        "insights": ai_insights,
    }
