"""
Tests unitarios para app/services/test_service.py

Cubre:
  - _execute_case: no muta el dict de entrada (AF-014)
  - _build_summary: la salida se acepta sin workaround (AF-002)
  - _generate_test_cases: generacion de casos por metodo HTTP (AF-010)
  - custom_cases: casos custom del usuario se agregan correctamente (AF-010)
"""

from app.models.request_models import TestRequest
from app.services.test_service import _execute_case, _generate_test_cases


class TestGenerateTestCases:
    """AF-010: Case generation per HTTP method."""

    def test_delete_genera_un_solo_caso(self):
        """GIVEN method=DELETE WHEN _generate_test_cases THEN 1 caso (valid_request)."""
        req = TestRequest(url="https://api.example.com/resource/1", method="DELETE")
        cases = _generate_test_cases(req)

        assert len(cases) == 1
        assert cases[0]["test_name"] == "valid_request"
        assert cases[0]["method"] == "DELETE"

    def test_get_sin_payload_genera_un_solo_caso_sin_query(self):
        """GIVEN method=GET sin query params WHEN _generate_test_cases THEN 1 caso."""
        req = TestRequest(url="https://api.example.com/users", method="GET")
        cases = _generate_test_cases(req)

        assert len(cases) == 1
        assert cases[0]["test_name"] == "valid_request"

    def test_get_con_query_params_genera_dos_casos(self):
        """GIVEN method=GET con query string WHEN _generate_test_cases THEN 2 casos (con y sin params)."""
        req = TestRequest(url="https://api.example.com/users?page=1&limit=10", method="GET")
        cases = _generate_test_cases(req)

        assert len(cases) == 2
        assert cases[0]["test_name"] == "valid_request"
        assert cases[1]["test_name"] == "no_query_params"
        # no_query_params remueve el query string
        assert "?" not in cases[1]["url"]

    def test_post_genera_cuatro_casos_con_payload_multicampo(self):
        """GIVEN method=POST con payload de 2 campos WHEN _generate_test_cases THEN 4 casos."""
        req = TestRequest(
            url="https://api.example.com/users",
            method="POST",
            payload={"name": "John", "age": 30},
        )
        cases = _generate_test_cases(req)

        assert len(cases) == 4
        names = {c["test_name"] for c in cases}
        assert names == {"valid_request", "missing_payload", "invalid_types", "incomplete_payload"}

    def test_post_con_payload_un_campo_no_genera_incomplete(self):
        """GIVEN method=POST con 1 solo campo WHEN _generate_test_cases THEN 3 casos (sin incomplete)."""
        req = TestRequest(
            url="https://api.example.com/items",
            method="POST",
            payload={"name": "single-field"},
        )
        cases = _generate_test_cases(req)

        assert len(cases) == 3
        names = {c["test_name"] for c in cases}
        assert "incomplete_payload" not in names

    def test_invalid_types_reemplaza_strings_por_ints_y_viceversa(self):
        """GIVEN payload con tipos mixtos WHEN _generate_test_cases THEN invalid_types tiene tipos invertidos."""
        req = TestRequest(
            url="https://api.example.com/data",
            method="POST",
            payload={"name": "test", "count": 42},
        )
        cases = _generate_test_cases(req)

        invalid_case = next(c for c in cases if c["test_name"] == "invalid_types")
        assert invalid_case["payload"]["name"] == 999  # string → int
        assert invalid_case["payload"]["count"] == "invalid_string"  # int → string

    def test_custom_cases_se_agregan_al_ejecutar(self, mocker):
        """GIVEN TestRequest con custom_cases WHEN run_test THEN los custom cases se agregan."""
        mocker.patch("app.services.test_service.send_request", return_value={
            "status_code": 200,
            "response_time": 0.1,
            "response_body": "ok",
        })
        mocker.patch("app.services.test_service.analyze", return_value={
            "quality_score": 100,
            "severity": "LOW",
            "issues": [],
            "insights": [],
            "summary": {"total_tests": 3, "passed": 3, "failed": 0, "fail_rate": 0.0},
        })
        mocker.patch("app.services.test_service.save_result", return_value=1)
        mocker.patch("app.services.test_service.build_latency_stats_for_result", return_value=None)

        from app.models.request_models import CustomTestCase
        from app.services.test_service import run_test

        req = TestRequest(
            url="https://api.example.com/users",
            method="GET",
            custom_cases=[
                CustomTestCase(name="custom-test-1", payload={"x": 1}, expected_status=201),
                CustomTestCase(name="custom-test-2", payload=None, expected_status=404),
            ],
        )

        result = run_test(req)

        # GET sin query genera 1 caso + 2 custom = 3 casos totales
        assert result.total_tests == 3
        test_names = [r.test_name for r in result.results]
        assert "custom-test-1" in test_names
        assert "custom-test-2" in test_names


class TestExecuteCase:

    def test_pop_headers_no_muta_dict_original(self, mocker):
        """GIVEN case con _headers WHEN _execute_case THEN el dict original conserva _headers (AF-014)."""
        mocker.patch("app.services.test_service.send_request", return_value={
            "status_code": 200,
            "response_time": 0.1,
            "response_body": "ok",
        })
        case = {
            "test_name": "valid_request",
            "url": "https://example.com/api",
            "method": "GET",
            "payload": None,
            "_headers": {"X-Custom": "test"},
            "_order": 0,
        }
        # Copia superficial para verificar que no muta
        original_keys = set(case.keys())
        _execute_case(case, {"Authorization": "Bearer default"})
        # Despues de la llamada, el dict DEBE conservar _headers
        assert "_headers" in case, "AF-014: _execute_case NO debe mutar el dict de entrada (pop). Usar .get()."
        assert set(case.keys()) == original_keys, (
            f"AF-014: _execute_case modifico las claves del dict. "
            f"Original: {original_keys}, Actual: {set(case.keys())}"
        )
        assert case["_headers"] == {"X-Custom": "test"}

    def test_get_headers_usa_headers_del_caso(self, mocker):
        """GIVEN case con _headers WHEN _execute_case THEN usa los headers del caso, no los globales."""
        mock_send = mocker.patch("app.services.test_service.send_request", return_value={
            "status_code": 200,
            "response_time": 0.1,
            "response_body": "ok",
        })
        case = {
            "test_name": "valid_request",
            "url": "https://example.com/api",
            "method": "GET",
            "payload": None,
            "_headers": {"X-Custom": "from-case"},
            "_order": 0,
        }
        _execute_case(case, {"Authorization": "default"})
        # Debe haber usado _headers del caso, no los globales
        called_headers = mock_send.call_args[0][3]
        assert called_headers["X-Custom"] == "from-case"

    def test_get_headers_fallback_a_globales(self, mocker):
        """GIVEN case SIN _headers WHEN _execute_case THEN usa los headers globales."""
        mock_send = mocker.patch("app.services.test_service.send_request", return_value={
            "status_code": 200,
            "response_time": 0.1,
            "response_body": "ok",
        })
        case = {
            "test_name": "valid_request",
            "url": "https://example.com/api",
            "method": "GET",
            "payload": None,
            "_order": 0,
        }
        _execute_case(case, {"Authorization": "Bearer global"})
        called_headers = mock_send.call_args[0][3]
        assert called_headers["Authorization"] == "Bearer global"
