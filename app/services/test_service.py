from typing import Any, Dict, List

from app.models.request_models import TestRequest
from app.models.response_models import TestResponse, TestResult
from app.repositories.test_repository import save_result
from app.services.analysis_service import analyze
from app.utils.http_client import send_request


def _generate_test_cases(request: TestRequest) -> List[Dict[str, Any]]:
    url = request.url
    method = request.method
    payload = request.payload or {}

    cases: List[Dict[str, Any]] = [
        {"test_name": "valid_request",    "url": url, "method": method, "payload": payload},
        {"test_name": "missing_payload",  "url": url, "method": method, "payload": None},
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

    if payload:
        keys = list(payload.keys())
        incomplete = {k: payload[k] for k in keys[1:]}
        cases.append({"test_name": "incomplete_payload", "url": url, "method": method, "payload": incomplete})

    return cases


def run_test(request: TestRequest) -> TestResponse:
    test_cases = _generate_test_cases(request)

    raw_results: List[Dict[str, Any]] = []
    for case in test_cases:
        outcome = send_request(case["url"], case["method"], case["payload"], request.headers)
        raw_results.append({
            "test_name":     case["test_name"],
            "status_code":   outcome.get("status_code"),
            "response_time": outcome.get("response_time"),
            "error":         outcome.get("error"),
        })

    analysis = analyze(raw_results)

    response = TestResponse(
        total_tests=len(raw_results),
        results=[TestResult(**r) for r in raw_results],
        issues_detected=analysis["issues"],
        severity=analysis["severity"],
        quality_score=analysis["quality_score"],
        ai_insights=analysis["insights"],
    )

    save_result(request.url, request.method, response.model_dump())

    return response
