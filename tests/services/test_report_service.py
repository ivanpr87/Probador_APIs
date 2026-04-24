from app.services.report_service import build_pdf_report, build_report


class TestReportService:

    def test_build_report_mantiene_metadata_base(self):
        report = build_report({"quality_score": 88, "severity": "LOW"})

        assert report["tool"] == "API Sentinel"
        assert report["version"]
        assert report["quality_score"] == 88

    def test_build_pdf_report_retorna_pdf_valido(self):
        pdf = build_pdf_report({
            "quality_score": 88,
            "severity": "LOW",
            "total_tests": 2,
            "summary": {"passed": 2, "failed": 0},
            "issues_detected": [],
            "ai_insights": ["Looks good"],
            "latency_stats": {"sample_size": 2, "p50": 120, "p95": 200, "p99": 220},
            "results": [
                {"test_name": "valid_request", "status_code": 200, "response_time": 0.12, "response_body": "{\"ok\":true}", "error": None},
            ],
        })

        assert isinstance(pdf, bytes)
        assert pdf.startswith(b"%PDF")
        assert len(pdf) > 1000
