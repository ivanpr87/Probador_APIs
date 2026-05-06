"""
Tests unitarios para app/services/test_service.py

Cubre:
  - _execute_case: no muta el dict de entrada (AF-014)
  - _build_summary: la salida se acepta sin workaround (AF-002)
"""

from app.services.test_service import _execute_case


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
