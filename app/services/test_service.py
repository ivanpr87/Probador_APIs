import requests
import time

from app.services.test_generator import generate_tests
from app.services.analyzer import analyze_results   
from app.services.ai_analyzer import ai_analyze
from app.services.ai_analyzer import calculate_score


def make_request(url, method, payload=None):
    try:
        start = time.time()

        if method == "GET":
            response = requests.get(url, timeout=5)

        elif method == "POST":
            response = requests.post(url, json=payload, timeout=5)

        else:
            return {"error": "Unsupported method"}

        duration = time.time() - start

        return {
            "status_code": response.status_code,
            "response_time": round(duration, 3)
        }

    except Exception as e:
        return {"error": str(e)}


def run_test(data: dict):
    tests = generate_tests(data)

    results = []

    for test in tests:
        response = make_request(
            test["url"],
            test["method"],
            test["payload"]
        )

        results.append({
            "test_name": test["test_name"],
            "status_code": response.get("status_code"),
            "response_time": response.get("response_time"),
            "error": response.get("error")
        })

    analysis = analyze_results(results)
    ai_data = ai_analyze(analysis, results)
    score = calculate_score(analysis)

    return {
        "total_tests": len(results),
        "results": results,
        "issues_detected": analysis,
        "severity": ai_data["severity"],
        "quality_score": score,
        "ai_insights": ai_data["insights"]
    }