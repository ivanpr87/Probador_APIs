#!/usr/bin/env python3
"""
Validation suite for the evaluation engine (analysis_service.py)
Simplified version without AI service calls

Run: python test_validation_simple.py
"""

import sys
import json
from typing import Dict, List, Any, Tuple
from collections import defaultdict
from statistics import mean

# Manually import only the core logic from analysis_service
sys.path.insert(0, 'E:\\proyectos\\ai-api-testing-agent')

# ─── Import only the non-AI parts ──────────────────────────────────────────────
from app.services.analysis_service import (
    _is_failure,
    _detect_http_issues,
    _detect_functional_issues,
    _detect_latency_issues,
    _calculate_score,
    _determine_severity,
    _build_summary,
    _SEV_RANK,
)


def analyze_test(
    results: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Simplified analyze() without AI service calls"""
    
    # 1. Resumen estadístico
    summary = _build_summary(results)

    # 2. Detección de issues en buckets
    buckets: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"count": 0, "severity": "LOW", "msg_en": "", "msg_es": ""}
    )
    _detect_http_issues(results, buckets)
    _detect_functional_issues(results, buckets)
    _detect_latency_issues(results, buckets)

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

    return {
        "issues":        [i["message"] for i in structured],
        "severity":      severity,
        "quality_score": score,
        "summary":       summary,
        "structured":    structured,
    }


# ─── Test Cases ────────────────────────────────────────────────────────────────

def test_case_1() -> Tuple[List[Dict], Dict]:
    """TEST 1 — ALL SUCCESS (BASELINE)"""
    results = [
        {"test_name": "ok_1", "status_code": 200, "response_time": 0.120, "success": True},
        {"test_name": "ok_2", "status_code": 201, "response_time": 0.180, "success": True}
    ]
    expected = {
        "score_min": 90, "score_max": 100,
        "severity": "LOW",
        "failed": 0,
        "issues_empty": True,
    }
    return results, expected


def test_case_2() -> Tuple[List[Dict], Dict]:
    """TEST 2 — CLIENT ERROR (4xx)"""
    results = [
        {"test_name": "bad_request", "status_code": 400, "response_time": 0.200, "success": False, "error": None}
    ]
    expected = {
        "score_min": 60, "score_max": 80,
        "severity": "MEDIUM",
        "failed": 1,
        "issues_contains": ["HTTP_400"],
        "issues_not_empty": True,
    }
    return results, expected


def test_case_3() -> Tuple[List[Dict], Dict]:
    """TEST 3 — METHOD ERROR (100% failure rate)"""
    results = [
        {"test_name": "invalid_method_1", "status_code": 405, "response_time": 0.800, "success": False, "error": None},
        {"test_name": "invalid_method_2", "status_code": 405, "response_time": 0.820, "success": False, "error": None},
        {"test_name": "invalid_method_3", "status_code": 405, "response_time": 0.810, "success": False, "error": None}
    ]
    expected = {
        "score_min": 30, "score_max": 60,
        "score_not": 100,
        "severity": ["HIGH", "CRITICAL"],
        "failed": 3,
        "issues_contains": ["HTTP_405"],
        "issues_not_empty": True,
    }
    return results, expected


def test_case_4() -> Tuple[List[Dict], Dict]:
    """TEST 4 — SERVER FAILURE (CRITICAL)"""
    results = [
        {"test_name": "server_down", "status_code": 503, "response_time": 0.500, "success": False, "error": None}
    ]
    expected = {
        "score_min": 0, "score_max": 40,
        "severity": "CRITICAL",
        "failed": 1,
        "issues_contains": ["HTTP_503"],
    }
    return results, expected


def test_case_5() -> Tuple[List[Dict], Dict]:
    """TEST 5 — MIXED SCENARIO"""
    results = [
        {"test_name": "ok", "status_code": 200, "response_time": 0.150, "success": True},
        {"test_name": "bad", "status_code": 400, "response_time": 0.300, "success": False, "error": None},
        {"test_name": "server", "status_code": 500, "response_time": 0.900, "success": False, "error": None}
    ]
    expected = {
        "score_min": 0, "score_max": 50,
        "severity": "CRITICAL",
        "failed": 2,
        "issues_contains": ["HTTP_400", "HTTP_500"],
    }
    return results, expected


def test_case_6() -> Tuple[List[Dict], Dict]:
    """TEST 6 — PERFORMANCE ISSUE"""
    results = [
        {"test_name": "slow", "status_code": 200, "response_time": 1.500, "success": True}
    ]
    expected = {
        "score_min": 70, "score_max": 90,
        "severity": ["LOW", "MEDIUM"],
        "failed": 0,
        "issues_contains": ["HIGH_LATENCY"],
    }
    return results, expected


# ─── Validation ────────────────────────────────────────────────────────────────

def validate_test(
    test_name: str,
    output: Dict[str, Any],
    expected: Dict[str, Any],
) -> Tuple[bool, List[str]]:
    """Returns (PASS, [failures])"""

    failures = []

    # Score range
    if "score_min" in expected:
        if not (expected["score_min"] <= output["quality_score"] <= expected["score_max"]):
            failures.append(
                f"Score {output['quality_score']} NOT in range "
                f"[{expected['score_min']}, {expected['score_max']}]"
            )

    # Score NOT equal
    if "score_not" in expected:
        if output["quality_score"] == expected["score_not"]:
            failures.append(f"Score MUST NOT be {expected['score_not']}")

    # Severity
    if "severity" in expected:
        exp_sev = expected["severity"]
        if isinstance(exp_sev, list):
            if output["severity"] not in exp_sev:
                failures.append(f"Severity {output['severity']} NOT in {exp_sev}")
        else:
            if output["severity"] != exp_sev:
                failures.append(f"Severity {output['severity']} != {exp_sev}")

    # Failed count
    if "failed" in expected:
        if output["summary"]["failed"] != expected["failed"]:
            failures.append(f"Failed {output['summary']['failed']} != {expected['failed']}")

    # Issues empty
    if expected.get("issues_empty"):
        if output["issues"]:
            failures.append(f"Issues MUST be empty, got: {output['issues']}")

    # Issues not empty
    if expected.get("issues_not_empty"):
        if not output["issues"]:
            failures.append("Issues MUST NOT be empty")

    # Issues contains
    if "issues_contains" in expected:
        issue_msgs = " ".join(output["issues"])
        for term in expected["issues_contains"]:
            if term not in issue_msgs:
                failures.append(f"Issues MUST contain '{term}'")

    return len(failures) == 0, failures


# ─── Runner ────────────────────────────────────────────────────────────────────

def run_all_tests() -> None:
    tests = [
        ("TEST 1 — ALL SUCCESS", test_case_1),
        ("TEST 2 — CLIENT ERROR", test_case_2),
        ("TEST 3 — METHOD ERROR (100%)", test_case_3),
        ("TEST 4 — SERVER FAILURE", test_case_4),
        ("TEST 5 — MIXED SCENARIO", test_case_5),
        ("TEST 6 — PERFORMANCE ISSUE", test_case_6),
    ]

    results_summary = []

    print("\n" + "=" * 80)
    print("EVALUATION ENGINE VALIDATION SUITE")
    print("=" * 80)

    for test_name, test_fn in tests:
        print(f"\n{test_name}")
        print("-" * 80)

        try:
            results, expected = test_fn()

            # Run the engine
            output = analyze_test(results)

            # Validate
            passed, failures = validate_test(test_name, output, expected)

            # Report
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status}")
            print(f"  Score: {output['quality_score']:3d}  |  Severity: {output['severity']:8s}  |  "
                  f"Failed: {output['summary']['failed']}")

            if not passed:
                print(f"  Failures:")
                for f in failures:
                    print(f"    • {f}")

            if output["issues"]:
                print(f"  Issues:")
                for issue in output["issues"][:2]:
                    print(f"    • {issue[:75]}...")

            results_summary.append((test_name, passed))

        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            results_summary.append((test_name, False))

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    passed_count = sum(1 for _, p in results_summary if p)
    total_count = len(results_summary)
    print(f"Passed: {passed_count}/{total_count}\n")

    for test_name, passed in results_summary:
        status = "✅" if passed else "❌"
        print(f"  {status}  {test_name}")

    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED — Engine is production-ready!")
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed — QA gate NOT passed")


if __name__ == "__main__":
    run_all_tests()
