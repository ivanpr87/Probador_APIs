from app.models.response_models import OAuth2ClientCredentialsConfig
from app.services import auth_service


class TestAuthService:

    def setup_method(self):
        auth_service._TOKEN_CACHE.clear()

    def test_pide_token_y_retorna_authorization_header(self, mocker):
        response = mocker.Mock()
        response.json.return_value = {"access_token": "token-123", "expires_in": 3600}
        response.raise_for_status.return_value = None
        mock_post = mocker.patch("app.services.auth_service.requests.post", return_value=response)

        headers = auth_service.get_oauth2_headers(OAuth2ClientCredentialsConfig(
            token_url="https://auth.example.com/oauth/token",
            client_id="client-id",
            client_secret="client-secret",
            scope="read:users",
        ))

        assert headers["Authorization"] == "Bearer token-123"
        assert mock_post.call_count == 1

    def test_reutiliza_token_cacheado_si_sigue_vigente(self, mocker):
        response = mocker.Mock()
        response.json.return_value = {"access_token": "token-123", "expires_in": 3600}
        response.raise_for_status.return_value = None
        mock_post = mocker.patch("app.services.auth_service.requests.post", return_value=response)

        config = OAuth2ClientCredentialsConfig(
            token_url="https://auth.example.com/oauth/token",
            client_id="client-id",
            client_secret="client-secret",
        )

        first = auth_service.get_oauth2_headers(config)
        second = auth_service.get_oauth2_headers(config)

        assert first == second
        assert mock_post.call_count == 1

    def test_refresca_token_vencido(self, mocker):
        response = mocker.Mock()
        response.json.side_effect = [
            {"access_token": "token-old", "expires_in": 1},
            {"access_token": "token-new", "expires_in": 3600},
        ]
        response.raise_for_status.return_value = None
        mock_post = mocker.patch("app.services.auth_service.requests.post", return_value=response)
        mock_time = mocker.patch("app.services.auth_service.time.time", side_effect=[1000, 1035])

        config = OAuth2ClientCredentialsConfig(
            token_url="https://auth.example.com/oauth/token",
            client_id="client-id",
            client_secret="client-secret",
        )

        first = auth_service.get_oauth2_headers(config)
        second = auth_service.get_oauth2_headers(config)

        assert first["Authorization"] == "Bearer token-old"
        assert second["Authorization"] == "Bearer token-new"
        assert mock_post.call_count == 2
        assert mock_time.call_count >= 2
