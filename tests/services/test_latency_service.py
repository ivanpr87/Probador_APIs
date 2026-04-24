from app.services.latency_service import (
    build_latency_stats,
    calculate_percentile,
    extract_run_latency_ms,
)


class TestExtractRunLatencyMs:

    def test_prefiere_valid_request(self):
        result = {
            "results": [
                {"test_name": "missing_payload", "response_time": 0.9},
                {"test_name": "valid_request", "response_time": 0.2},
            ]
        }

        assert extract_run_latency_ms(result) == 200.0

    def test_hace_fallback_a_promedio(self):
        result = {
            "results": [
                {"test_name": "custom_1", "response_time": 0.2},
                {"test_name": "custom_2", "response_time": 0.4},
            ]
        }

        assert extract_run_latency_ms(result) == 300.0


class TestCalculatePercentile:

    def test_percentil_unico_valor(self):
        assert calculate_percentile([120.0], 95) == 120.0

    def test_percentil_interpolado(self):
        values = [100.0, 200.0, 300.0, 400.0]
        assert calculate_percentile(values, 50) == 250.0
        assert calculate_percentile(values, 95) == 385.0


class TestBuildLatencyStats:

    def test_calcula_p50_p95_p99(self):
        stats = build_latency_stats([100.0, 200.0, 300.0, 400.0, 500.0])

        assert stats is not None
        assert stats.sample_size == 5
        assert stats.p50 == 300.0
        assert stats.p95 == 480.0
        assert stats.p99 == 496.0
