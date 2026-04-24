from app.models.request_models import TestRequest as ApiTestRequest
from app.services.test_service import run_test


class TestRunTestOAuth:

    def test_inyecta_bearer_oauth_en_requests(self, mocker, mock_ai_service):
        mocker.patch("app.services.test_service.analyze", return_value={
            "issues": [],
            "severity": "LOW",
            "quality_score": 100,
            "insights": [],
            "summary": {"total_tests": 1, "passed": 1, "failed": 0, "fail_rate": 0.0},
        })
        mocker.patch("app.services.test_service.get_oauth2_headers", return_value={"Authorization": "Bearer oauth-token"})
        send_request = mocker.patch("app.services.test_service.send_request", return_value={
            "status_code": 200,
            "response_time": 0.1,
            "response_body": "{\"ok\":true}",
        })
        mocker.patch("app.services.test_service.save_result")

        request = ApiTestRequest(
            url="https://api.example.com/users",
            method="GET",
            headers={"X-Test": "1"},
            auth_config={
                "token_url": "https://auth.example.com/oauth/token",
                "client_id": "client-id",
                "client_secret": "client-secret",
            },
        )

        response = run_test(request)

        assert response.quality_score == 100
        sent_headers = send_request.call_args.args[3]
        assert sent_headers["Authorization"] == "Bearer oauth-token"
        assert sent_headers["X-Test"] == "1"
