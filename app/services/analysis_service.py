from typing import Any, Dict, List


def detect_issues(results: List[Dict[str, Any]]) -> List[str]:
    issues = []
    for result in results:
        test_name = result.get("test_name")
        status = result.get("status_code")

        if test_name == "missing_payload" and status in (200, 201):
            issues.append("API accepts requests without payload (validation missing)")

        if test_name == "invalid_types" and status in (200, 201):
            issues.append("API accepts invalid data types (type validation missing)")

    return issues


def calculate_score(issues: List[str]) -> int:
    score = 100
    for issue in issues:
        if "without payload" in issue:
            score -= 30
        elif "invalid data types" in issue:
            score -= 40
    return max(score, 0)


def determine_severity(issues: List[str]) -> str:
    if any("invalid data types" in i for i in issues):
        return "critical"
    if any("without payload" in i for i in issues):
        return "high"
    return "low"


def generate_insights(issues: List[str]) -> List[str]:
    if not issues:
        return ["No issues detected in the executed tests."]

    insights = []
    if any("without payload" in i for i in issues):
        insights.append(
            "The API does not validate required fields. It may accept incomplete requests silently."
        )
    if any("invalid data types" in i for i in issues):
        insights.append(
            "The API does not validate data types. Risk of database errors or production failures."
        )
    return insights


def analyze(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    issues = detect_issues(results)
    return {
        "issues": issues,
        "severity": determine_severity(issues),
        "quality_score": calculate_score(issues),
        "insights": generate_insights(issues),
    }
