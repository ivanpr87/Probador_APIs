from app.api.routes.test_routes import export_report_pdf


class TestReportRoutes:

    def test_export_report_pdf_retorna_application_pdf(self):
        response = export_report_pdf({
            "quality_score": 75,
            "severity": "MEDIUM",
            "total_tests": 1,
            "summary": {"passed": 1, "failed": 0},
            "issues_detected": ["Latency elevated"],
            "ai_insights": ["Review endpoint caching"],
            "latency_stats": {"sample_size": 3, "p50": 110, "p95": 220, "p99": 240},
            "results": [
                {"test_name": "valid_request", "status_code": 200, "response_time": 0.11, "response_body": "{\"ok\":true}", "error": None},
            ],
        })

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/pdf")
        assert response.body.startswith(b"%PDF")
