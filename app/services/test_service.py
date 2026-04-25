from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from app.models.request_models import TestRequest
from app.models.response_models import TestResponse, TestResult, TestSummary
from app.repositories.test_repository import save_result
from app.services.latency_service import build_latency_stats_for_result
from app.services.auth_service import get_oauth2_headers
from app.services.analysis_service import analyze
from app.utils.http_client import send_request


def _generate_test_cases(request: TestRequest) -> List[Dict[str, Any]]:
    url = request.url
    method = request.method
    payload = request.payload or {}

    # DELETE: solo valid_request (el body es opcional y no se valida igual)
    if method == "DELETE":
        return [
            {"test_name": "valid_request", "url": url, "method": method, "payload": payload or None},
        ]

    # GET sin payload: solo valid_request + stripped query params si los hay
    if method == "GET" and not payload:
        cases: List[Dict[str, Any]] = [
            {"test_name": "valid_request", "url": url, "method": method, "payload": None},
        ]
        parsed = urlparse(url)
        if parsed.query:
            base_url = url.split("?")[0]
            cases.append({
                "test_name": "no_query_params",
                "url": base_url,
                "method": method,
                "payload": None,
            })
        return cases

    # POST / PUT / PATCH (o GET con payload): suite completa
    cases = [
        {"test_name": "valid_request",   "url": url, "method": method, "payload": payload},
        {"test_name": "missing_payload", "url": url, "method": method, "payload": None},
    ]

    invalid_payload: Dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(value, int):
            invalid_payload[key] = "invalid_string"
        elif isinstance(value, str):
            invalid_payload[key] = 999
        else:
            invalid_payload[key] = None
    cases.append({"test_name": "invalid_types", "url": url, "method": method, "payload": invalid_payload})

    if len(payload) > 1:
        keys = list(payload.keys())
        incomplete = {k: payload[k] for k in keys[1:]}
        cases.append({"test_name": "incomplete_payload", "url": url, "method": method, "payload": incomplete})

    return cases


def _execute_case(case: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    # Por-caso: usar headers específicos del caso si existen, sino los globales
    effective_headers = case.pop("_headers", headers)
    outcome = send_request(case["url"], case["method"], case["payload"], effective_headers)
    return {
        "test_name":       case["test_name"],
        "status_code":     outcome.get("status_code"),
        "response_time":   outcome.get("response_time"),
        "response_body":   outcome.get("response_body"),
        "error":           outcome.get("error"),
        "expected_status": case.get("expected_status"),
        "_order":          case["_order"],
    }


def run_test(request: TestRequest, source: Optional[Dict[str, Any]] = None) -> TestResponse:
    base_headers = _resolve_base_headers(request)
    test_cases = _generate_test_cases(request)

    # Agregar casos custom del usuario (ejecutados en paralelo junto a los auto-generados)
    for custom in (request.custom_cases or []):
        merged_headers = {**base_headers, **(custom.headers or {})}
        test_cases.append({
            "test_name":       custom.name,
            "url":             request.url,
            "method":          request.method,
            "payload":         custom.payload,
            "expected_status": custom.expected_status,
            "_headers":        merged_headers,
        })

    # Inyectar índice de orden para reordenar después de ejecución paralela
    for i, case in enumerate(test_cases):
        case["_order"] = i

    raw_results: List[Dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=min(len(test_cases), 4)) as executor:
        futures = {
            executor.submit(_execute_case, case, base_headers): case
            for case in test_cases
        }
        for future in as_completed(futures):
            raw_results.append(future.result())

    # Restaurar orden original de los casos
    raw_results.sort(key=lambda r: r.pop("_order"))

    analysis = analyze(
        raw_results,
        method=request.method,
        url=request.url,
        expected_schema=request.expected_schema,
    )

    # Import TestSummary eliminado porque ya está a nivel de módulo

    summary_data = analysis.get("summary", {})
    if summary_data and "total" in summary_data:
        summary_data["total_tests"] = summary_data.pop("total")
    response = TestResponse(
        total_tests=len(raw_results),
        results=[TestResult(**r) for r in raw_results],
        issues_detected=analysis["issues"],
        severity=analysis["severity"],
        quality_score=analysis["quality_score"],
        ai_insights=analysis["insights"],
        summary=TestSummary(**summary_data) if summary_data else None,
        source=source,
        latency_stats=build_latency_stats_for_result(
            url=request.url,
            method=request.method,
            source=source,
            current_result={"results": raw_results},
        ),
    )

    save_result(request.url, request.method, response.model_dump(), source=source)

    return response


def _resolve_base_headers(request: TestRequest) -> Dict[str, str]:
    headers = dict(request.headers or {})
    if request.auth_config:
        oauth_headers = get_oauth2_headers(request.auth_config)
        headers = {**headers, **oauth_headers}
    return headers
