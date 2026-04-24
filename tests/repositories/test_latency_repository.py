from app.repositories.test_repository import fetch_history_item, save_result


class TestLatencyStatsInHistoryItem:

    def test_history_item_expone_percentiles_del_scope_manual(self, temp_db):
        url = "https://api.example.com/health"

        save_result(
            url,
            "GET",
            {
                "quality_score": 90,
                "severity": "LOW",
                "total_tests": 1,
                "results": [{"test_name": "valid_request", "response_time": 0.10}],
            },
        )
        second_id = save_result(
            url,
            "GET",
            {
                "quality_score": 80,
                "severity": "LOW",
                "total_tests": 1,
                "results": [{"test_name": "valid_request", "response_time": 0.20}],
            },
        )
        save_result(
            url,
            "GET",
            {
                "quality_score": 70,
                "severity": "MEDIUM",
                "total_tests": 1,
                "results": [{"test_name": "valid_request", "response_time": 0.30}],
            },
        )

        item = fetch_history_item(second_id)

        assert item is not None
        assert item["latency_stats"]["sample_size"] == 2
        assert item["latency_stats"]["p50"] == 150.0
        assert item["latency_stats"]["p95"] == 195.0

    def test_history_item_separa_por_schedule_id(self, temp_db):
        url = "https://api.example.com/orders"

        first_id = save_result(
            url,
            "POST",
            {
                "quality_score": 60,
                "severity": "HIGH",
                "total_tests": 1,
                "results": [{"test_name": "valid_request", "response_time": 0.10}],
            },
            source={"type": "schedule", "config_id": 1, "schedule_id": 10},
        )
        save_result(
            url,
            "POST",
            {
                "quality_score": 90,
                "severity": "LOW",
                "total_tests": 1,
                "results": [{"test_name": "valid_request", "response_time": 0.90}],
            },
            source={"type": "schedule", "config_id": 1, "schedule_id": 99},
        )
        second_id = save_result(
            url,
            "POST",
            {
                "quality_score": 75,
                "severity": "MEDIUM",
                "total_tests": 1,
                "results": [{"test_name": "valid_request", "response_time": 0.20}],
            },
            source={"type": "schedule", "config_id": 1, "schedule_id": 10},
        )

        first = fetch_history_item(first_id)
        second = fetch_history_item(second_id)

        assert first is not None
        assert second is not None
        assert first["latency_stats"]["sample_size"] == 1
        assert second["latency_stats"]["sample_size"] == 2
        assert second["latency_stats"]["p50"] == 150.0
