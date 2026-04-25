from app.repositories.test_repository import save_result
from app.services.history_service import get_history


class TestHistoryDelta:

    def test_primer_run_no_tiene_delta(self, temp_db):
        save_result(
            "https://api.example.com/users",
            "GET",
            {"quality_score": 80, "severity": "LOW", "total_tests": 1, "results": []},
        )

        history = get_history()

        assert len(history.items) == 1
        assert history.items[0].previous_score is None
        assert history.items[0].delta_score is None
        assert history.items[0].delta_direction is None

    def test_delta_score_compara_con_run_anterior_manual(self, temp_db):
        save_result(
            "https://api.example.com/users",
            "GET",
            {"quality_score": 60, "severity": "MEDIUM", "total_tests": 1, "results": []},
        )
        save_result(
            "https://api.example.com/users",
            "GET",
            {"quality_score": 85, "severity": "LOW", "total_tests": 1, "results": []},
        )

        history = get_history()

        assert history.items[0].quality_score == 85
        assert history.items[0].previous_score == 60
        assert history.items[0].delta_score == 25
        assert history.items[0].delta_direction == "up"

    def test_delta_score_usa_schedule_id_como_identidad(self, temp_db):
        url = "https://api.example.com/orders"
        method = "POST"

        save_result(
            url,
            method,
            {"quality_score": 30, "severity": "CRITICAL", "total_tests": 4, "results": []},
            source={"type": "schedule", "config_id": 1, "schedule_id": 10},
        )
        save_result(
            url,
            method,
            {"quality_score": 90, "severity": "LOW", "total_tests": 4, "results": []},
            source={"type": "schedule", "config_id": 1, "schedule_id": 99},
        )
        save_result(
            url,
            method,
            {"quality_score": 55, "severity": "HIGH", "total_tests": 4, "results": []},
            source={"type": "schedule", "config_id": 1, "schedule_id": 10},
        )

        history = get_history()

        latest_same_schedule = history.items[0]
        assert latest_same_schedule.source is not None
        assert latest_same_schedule.source.schedule_id == 10
        assert latest_same_schedule.previous_score == 30
        assert latest_same_schedule.delta_score == 25
        assert latest_same_schedule.delta_direction == "up"

    def test_delta_score_cero_marca_same(self, temp_db):
        url = "https://api.example.com/products"

        save_result(
            url,
            "GET",
            {"quality_score": 70, "severity": "MEDIUM", "total_tests": 2, "results": []},
        )
        save_result(
            url,
            "GET",
            {"quality_score": 70, "severity": "MEDIUM", "total_tests": 2, "results": []},
        )

        history = get_history()

        assert history.items[0].delta_score == 0
        assert history.items[0].delta_direction == "same"
