from app.repositories.test_repository import (
    fetch_history,
    fetch_previous_scores_batch,
    save_result,
)


class TestFetchPreviousScoresBatch:
    """AF-007: Batch query instead of N+1 per-row queries."""

    def test_retorna_dict_vacio_sin_row_ids(self, temp_db):
        """GIVEN lista vacia de row_ids WHEN batch THEN dict vacio."""
        result = fetch_previous_scores_batch([])
        assert result == {}

    def test_retorna_previous_score_para_cada_row_id(self, temp_db):
        """GIVEN 2 filas mismo url+method WHEN batch con ambos ids THEN el segundo obtiene prev_score del primero."""
        url = "https://api.example.com/users"
        method = "GET"

        id1 = save_result(url, method, {"quality_score": 50, "severity": "HIGH", "total_tests": 2, "results": []})
        id2 = save_result(url, method, {"quality_score": 80, "severity": "LOW", "total_tests": 3, "results": []})

        result = fetch_previous_scores_batch([id1, id2])

        # id1: no tiene previo
        assert id1 not in result
        # id2: prev_score = 50 (del id1)
        assert result[id2] == 50

    def test_excluye_filas_con_id_mayor_o_igual(self, temp_db):
        """GIVEN 1 fila WHEN batch con su id THEN no encuentra previo (LEFT JOIN sin resultados)."""
        url = "https://api.example.com/items"
        method = "POST"

        id1 = save_result(url, method, {"quality_score": 60, "severity": "MEDIUM", "total_tests": 2, "results": []})

        result = fetch_previous_scores_batch([id1])
        assert id1 not in result

    def test_devuelve_max_score_previo_por_url_method(self, temp_db):
        """GIVEN 3 filas mismo par WHEN batch THEN cada una obtiene el MAX score de filas anteriores."""
        url = "https://api.example.com/a"
        method = "GET"

        id1 = save_result(url, method, {"quality_score": 30, "severity": "HIGH", "total_tests": 2, "results": []})
        id2 = save_result(url, method, {"quality_score": 70, "severity": "MEDIUM", "total_tests": 1, "results": []})
        id3 = save_result(url, method, {"quality_score": 50, "severity": "MEDIUM", "total_tests": 2, "results": []})

        result = fetch_previous_scores_batch([id1, id2, id3])

        # id1: sin previo
        assert id1 not in result
        # id2: MAX previo = 30 (solo id1)
        assert result[id2] == 30
        # id3: MAX previo = MAX(30, 70) = 70
        assert result[id3] == 70

    def test_urls_distintas_no_interfieren(self, temp_db):
        """GIVEN pares (url,method) distintos WHEN batch THEN cada fila solo ve su propio par."""
        url_a = "https://api.example.com/a"
        url_b = "https://api.example.com/b"

        id_a1 = save_result(url_a, "GET", {"quality_score": 10, "severity": "CRITICAL", "total_tests": 1, "results": []})
        id_b1 = save_result(url_b, "POST", {"quality_score": 99, "severity": "LOW", "total_tests": 1, "results": []})
        id_a2 = save_result(url_a, "GET", {"quality_score": 20, "severity": "HIGH", "total_tests": 1, "results": []})
        id_b2 = save_result(url_b, "POST", {"quality_score": 80, "severity": "MEDIUM", "total_tests": 1, "results": []})

        result = fetch_previous_scores_batch([id_a1, id_b1, id_a2, id_b2])

        # Primeros no tienen previo
        assert id_a1 not in result
        assert id_b1 not in result
        # a2: prev = 10 (de id_a1, no contamina con id_b1)
        assert result[id_a2] == 10
        # b2: prev = 99 (de id_b1, no contamina con id_a1)
        assert result[id_b2] == 99


class TestHistoryDelta:

    def test_primer_run_no_tiene_delta(self, temp_db):
        save_result(
            "https://api.example.com/users",
            "GET",
            {"quality_score": 80, "severity": "LOW", "total_tests": 1, "results": []},
        )

        history = fetch_history()

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

        history = fetch_history()

        assert history.items[0].quality_score == 85
        assert history.items[0].previous_score == 60
        assert history.items[0].delta_score == 25
        assert history.items[0].delta_direction == "up"

    def test_delta_score_usa_schedule_id_como_identidad(self, temp_db):
        """GIVEN 3 runs con distintos schedule_id WHEN fetch_history THEN
        el batch AF-007 ignora source y compara por (url, method) globalmente."""
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

        history = fetch_history()

        # items ordenados por id DESC: id=3, id=2, id=1
        # id=3 (score=55): prev = MAX(30, 90) = 90 → delta = -35 → "down"
        latest = history.items[0]
        assert latest.source is not None
        assert latest.source.schedule_id == 10
        assert latest.previous_score == 90  # AF-007: ignora source, ve el MAX previo global
        assert latest.delta_score == -35
        assert latest.delta_direction == "down"

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

        history = fetch_history()

        assert history.items[0].delta_score == 0
        assert history.items[0].delta_direction == "same"
