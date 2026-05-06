"""
Tests unitarios para app/utils/http_client.py — send_request()

Cubre:
  - Soportar GET, POST, PUT, PATCH, DELETE
  - Devolver shape de respuesta consistente para todos los metodos
  - Manejo de errores: timeout, ConnectionError
"""

from unittest.mock import ANY, MagicMock

import pytest
import requests

from app.utils.http_client import send_request


def _mock_response(status_code=200, text='{"ok": true}'):
    """Fabrica un mock de requests.Response."""
    mock = MagicMock(spec=requests.Response)
    mock.status_code = status_code
    mock.text = text
    mock.headers = {"Content-Type": "application/json"}
    return mock


class TestSendRequestAllMethods:

    def test_get_retorna_respuesta_valida(self, mocker):
        """GIVEN un endpoint HTTP WHEN se envia GET THEN retorna status_code + response_time + response_body."""
        mock_req = mocker.patch(
            "app.utils.http_client.requests.request",
            return_value=_mock_response(200)
        )
        result = send_request("https://example.com/api", "GET")
        assert result["status_code"] == 200
        assert result["response_time"] is not None
        assert result["response_body"] == '{"ok": true}'
        assert "error" not in result
        mock_req.assert_called_once_with("GET", "https://example.com/api", json=ANY, timeout=ANY, headers=ANY)

    def test_post_con_payload_retorna_respuesta_valida(self, mocker):
        """GIVEN un endpoint HTTP WHEN se envia POST con payload THEN se pasa json=payload."""
        mock_req = mocker.patch(
            "app.utils.http_client.requests.request",
            return_value=_mock_response(201)
        )
        result = send_request("https://example.com/api", "POST", payload={"name": "test"})
        assert result["status_code"] == 201
        assert "error" not in result
        mock_req.assert_called_once_with(
            "POST", "https://example.com/api", json={"name": "test"}, timeout=ANY, headers=ANY
        )

    def test_put_retorna_respuesta_valida(self, mocker):
        """GIVEN un endpoint HTTP WHEN se envia PUT THEN retorna respuesta valida (no 'Unsupported')."""
        mock_req = mocker.patch(
            "app.utils.http_client.requests.request",
            return_value=_mock_response(200)
        )
        result = send_request("https://example.com/api", "PUT", payload={"id": 1})
        assert result["status_code"] == 200
        assert "error" not in result
        mock_req.assert_called_once_with(
            "PUT", "https://example.com/api", json={"id": 1}, timeout=ANY, headers=ANY
        )

    def test_patch_retorna_respuesta_valida(self, mocker):
        """GIVEN un endpoint HTTP WHEN se envia PATCH THEN retorna respuesta valida."""
        mock_req = mocker.patch(
            "app.utils.http_client.requests.request",
            return_value=_mock_response(200)
        )
        result = send_request("https://example.com/api", "PATCH", payload={"status": "active"})
        assert result["status_code"] == 200
        assert "error" not in result
        mock_req.assert_called_once_with(
            "PATCH", "https://example.com/api", json={"status": "active"}, timeout=ANY, headers=ANY
        )

    def test_delete_retorna_respuesta_valida(self, mocker):
        """GIVEN un endpoint HTTP WHEN se envia DELETE THEN retorna respuesta valida."""
        mock_req = mocker.patch(
            "app.utils.http_client.requests.request",
            return_value=_mock_response(204, text="")
        )
        result = send_request("https://example.com/api", "DELETE")
        assert result["status_code"] == 204
        assert "error" not in result
        mock_req.assert_called_once_with(
            "DELETE", "https://example.com/api", json=ANY, timeout=ANY, headers=ANY
        )

    def test_respuesta_4xx_no_es_error_de_libreria(self, mocker):
        """GIVEN un endpoint HTTP WHEN responde 404 THEN send_request lo captura como status_code normal."""
        mocker.patch(
            "app.utils.http_client.requests.request",
            return_value=_mock_response(404, text="Not Found")
        )
        result = send_request("https://example.com/api", "GET")
        assert result["status_code"] == 404
        assert "error" not in result

    def test_respuesta_5xx_no_es_error_de_libreria(self, mocker):
        """GIVEN un endpoint HTTP WHEN responde 500 THEN send_request lo captura como status_code normal."""
        mocker.patch(
            "app.utils.http_client.requests.request",
            return_value=_mock_response(500, text="Internal Error")
        )
        result = send_request("https://example.com/api", "GET")
        assert result["status_code"] == 500
        assert "error" not in result

    def test_respuesta_body_truncado_a_500_chars(self, mocker):
        """GIVEN un endpoint HTTP WHEN el body es mayor a 500 chars THEN se trunca."""
        long_body = "x" * 1000
        mocker.patch(
            "app.utils.http_client.requests.request",
            return_value=_mock_response(200, text=long_body)
        )
        result = send_request("https://example.com/api", "GET")
        assert len(result["response_body"]) == 500

    def test_headers_se_pasan_correctamente(self, mocker):
        """GIVEN headers personalizados WHEN se envia la request THEN se pasan a requests.request."""
        mock_req = mocker.patch(
            "app.utils.http_client.requests.request",
            return_value=_mock_response(200)
        )
        send_request(
            "https://example.com/api", "GET",
            headers={"Authorization": "Bearer token"}
        )
        mock_req.assert_called_once_with(
            "GET", "https://example.com/api", json=ANY,
            timeout=ANY, headers={"Authorization": "Bearer token"}
        )


class TestSendRequestErrors:

    def test_timeout_retorna_error(self, mocker):
        """GIVEN un endpoint lento WHEN timeout THEN retorna dict con clave 'error'."""
        mocker.patch(
            "app.utils.http_client.requests.request",
            side_effect=requests.exceptions.Timeout
        )
        result = send_request("https://example.com/api", "GET")
        assert "error" in result
        assert "timed out" in result["error"].lower()

    def test_connection_error_retorna_error(self, mocker):
        """GIVEN un endpoint inalcanzable WHEN ConnectionError THEN retorna dict con clave 'error'."""
        mocker.patch(
            "app.utils.http_client.requests.request",
            side_effect=requests.exceptions.ConnectionError
        )
        result = send_request("https://example.com/api", "POST")
        assert "error" in result
        assert "connection" in result["error"].lower()
