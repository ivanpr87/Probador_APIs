import math
from statistics import mean
from typing import Dict, List, Optional

from app.models.response_models import LatencyStats


def extract_run_latency_ms(result: Dict) -> Optional[float]:
    results = result.get("results") or []
    if not results:
        return None

    valid_request = next((item for item in results if item.get("test_name") == "valid_request"), None)
    if valid_request and valid_request.get("response_time") is not None:
        return round(float(valid_request["response_time"]) * 1000, 2)

    values = [
        float(item["response_time"]) * 1000
        for item in results
        if item.get("response_time") is not None
    ]
    if not values:
        return None
    return round(mean(values), 2)


def calculate_percentile(sorted_values: List[float], percentile: float) -> Optional[float]:
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return round(sorted_values[0], 2)

    rank = (percentile / 100) * (len(sorted_values) - 1)
    lower = math.floor(rank)
    upper = math.ceil(rank)

    if lower == upper:
        return round(sorted_values[lower], 2)

    weight = rank - lower
    value = sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * weight
    return round(value, 2)


def build_latency_stats(latencies_ms: List[float]) -> Optional[LatencyStats]:
    clean = sorted(float(value) for value in latencies_ms if value is not None)
    if not clean:
        return None

    return LatencyStats(
        sample_size=len(clean),
        metric="valid_request_response_time",
        p50=calculate_percentile(clean, 50),
        p95=calculate_percentile(clean, 95),
        p99=calculate_percentile(clean, 99),
    )
