import logging
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.api.routes.configs_routes import create_config, import_openapi
from app.models.response_models import SavedConfigCreate


class TestConfigsRoutesErrorSanitization:

    def test_500_no_expone_detalle_interno_en_create_config(self):
        """AF-004: 500 responses must NOT expose internal error details."""
        data = SavedConfigCreate(name="test", url="https://example.com", method="GET")

        with patch(
            "app.api.routes.configs_routes.save_config",
            side_effect=RuntimeError("SENSITIVE DB DETAIL — schema mismatch"),
        ), patch.object(logging.getLogger("app.api.routes.configs_routes"), "exception") as mock_log:
            with pytest.raises(HTTPException) as exc_info:
                create_config(data)

        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Internal server error while processing config"
        assert "SENSITIVE DB DETAIL" not in exc_info.value.detail
        # The actual error must still be logged
        mock_log.assert_called_once()
        assert "Internal server error while processing config" in str(mock_log.call_args[0][0])

    def test_500_no_expone_detalle_interno_en_import_openapi(self):
        """AF-004: import_openapi 500 responses must NOT expose internal error details."""
        with patch(
            "app.api.routes.configs_routes.import_openapi_spec",
            side_effect=RuntimeError("SENSITIVE DB DETAIL — FOREIGN KEY failure"),
        ), patch.object(logging.getLogger("app.api.routes.configs_routes"), "exception") as mock_log:
            with pytest.raises(HTTPException) as exc_info:
                import_openapi(
                    type("OpenAPIImportRequest", (), {
                        "spec": {"openapi": "3.0.0"},
                        "base_url": None,
                        "name_prefix": None,
                    })()
                )

        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Internal server error while processing config"
        assert "SENSITIVE DB DETAIL" not in exc_info.value.detail
        mock_log.assert_called_once()
        assert "Internal server error while processing config" in str(mock_log.call_args[0][0])

    def test_422_unaffected_por_sanitizacion(self):
        """ValueError on import_openapi should still return 422 with the actual message."""
        with patch(
            "app.api.routes.configs_routes.import_openapi_spec",
            side_effect=ValueError("Invalid OpenAPI version"),
        ):
            with pytest.raises(HTTPException) as exc_info:
                import_openapi(
                    type("OpenAPIImportRequest", (), {
                        "spec": {"openapi": "2.0"},
                        "base_url": None,
                        "name_prefix": None,
                    })()
                )

        assert exc_info.value.status_code == 422
        assert "Invalid OpenAPI version" in str(exc_info.value.detail)

    def test_409_conflict_unaffected_por_sanitizacion(self):
        """UNIQUE constraint violations should still return 409 with the name."""
        data = SavedConfigCreate(name="duplicate", url="https://example.com", method="GET")

        with patch(
            "app.api.routes.configs_routes.save_config",
            side_effect=Exception("UNIQUE constraint failed: saved_configs.name"),
        ):
            with pytest.raises(HTTPException) as exc_info:
                create_config(data)

        assert exc_info.value.status_code == 409
        assert "duplicate" in str(exc_info.value.detail).lower()
