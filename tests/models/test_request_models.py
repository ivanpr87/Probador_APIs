import pytest
from unittest.mock import patch

from app.models.request_models import TestRequest


class TestSSRFValidation:

    # ── Happy path: public IPs pass ──

    def test_ip_publica_valida_pasa_validacion(self):
        req = TestRequest(url="http://1.1.1.1/api", method="GET")
        assert req.url == "http://1.1.1.1/api"

    def test_ip_publica_google_dns_pasa(self):
        req = TestRequest(url="https://8.8.8.8/dns", method="GET")
        assert req.url == "https://8.8.8.8/dns"

    # ── Private IPv4 ranges blocked ──

    def test_loopback_127_es_bloqueada(self):
        with pytest.raises(ValueError, match="127\\.0\\.0\\.1.*private|internal|loopback|SSRF"):
            TestRequest(url="http://127.0.0.1/admin", method="GET")

    def test_localhost_loopback_ipv6_es_bloqueada(self):
        with pytest.raises(ValueError, match="private|internal|loopback|SSRF"):
            TestRequest(url="http://[::1]/admin", method="GET")

    def test_rango_10_es_bloqueado(self):
        with pytest.raises(ValueError, match="10\\.0\\.0\\.1.*private|internal|SSRF"):
            TestRequest(url="http://10.0.0.1/api", method="GET")

    def test_rango_192_168_es_bloqueado(self):
        with pytest.raises(ValueError, match="192\\.168\\.1\\.1.*private|internal|SSRF"):
            TestRequest(url="http://192.168.1.1/api", method="GET")

    def test_rango_172_16_es_bloqueado(self):
        with pytest.raises(ValueError, match="172\\.16\\.0\\.1.*private|internal|SSRF"):
            TestRequest(url="http://172.16.0.1/api", method="GET")

    def test_link_local_169_254_es_bloqueado(self):
        with pytest.raises(ValueError, match="169\\.254\\.0\\.1.*private|link.local|internal|SSRF"):
            TestRequest(url="http://169.254.0.1/api", method="GET")

    def test_unspecified_0_0_0_0_es_bloqueado(self):
        with pytest.raises(ValueError, match="0\\.0\\.0\\.0.*private|internal|SSRF|unspecified"):
            TestRequest(url="http://0.0.0.0/api", method="GET")

    # ── Hostname resolution: public hostname pass, private resolved IP blocked ──

    def test_hostname_publico_pasa_validacion(self):
        # example.com resolves to public IPs (93.184.216.34)
        req = TestRequest(url="https://example.com/api", method="GET")
        assert req.url == "https://example.com/api"

    def test_hostname_que_resuelve_a_ip_privada_es_bloqueado(self):
        with patch("socket.getaddrinfo") as mock_getaddrinfo:
            mock_getaddrinfo.return_value = [
                (2, 1, 6, "", ("10.0.0.5", 0))
            ]
            with pytest.raises(ValueError, match="10\\.0\\.0\\.5.*private|internal|SSRF"):
                TestRequest(url="http://internal.corp/admin", method="GET")

    def test_hostname_que_resuelve_a_ip_publica_pasa(self):
        with patch("socket.getaddrinfo") as mock_getaddrinfo:
            mock_getaddrinfo.return_value = [
                (2, 1, 6, "", ("93.184.216.34", 0))
            ]
            req = TestRequest(url="https://public.example.com/api", method="GET")
            assert req.url == "https://public.example.com/api"

    # ── Edge cases ──

    def test_url_sin_esquema_lanza_error_de_validacion(self):
        # URL without scheme should fail ParseResult parsing
        with pytest.raises(ValueError):
            TestRequest(url="10.0.0.1/api", method="GET")

    def test_url_invalida_lanza_error(self):
        with pytest.raises(ValueError):
            TestRequest(url="not-a-valid-url-!!!", method="GET")
