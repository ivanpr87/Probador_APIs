from app.repositories.configs_repository import list_configs
from app.services.openapi_service import import_openapi_spec


class TestImportOpenAPISpec:

    def test_importa_configs_y_saltea_duplicados(self, temp_db):
        spec = {
            "openapi": "3.0.0",
            "servers": [{"url": "https://api.example.com"}],
            "paths": {
                "/users": {
                    "get": {"operationId": "listUsers"},
                    "post": {
                        "operationId": "createUser",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string", "example": "Ivan"}
                                        },
                                    }
                                }
                            }
                        },
                    },
                }
            },
        }

        first = import_openapi_spec(spec, name_prefix="Spec")
        second = import_openapi_spec(spec, name_prefix="Spec")
        configs = list_configs()

        assert first.created == 2
        assert first.skipped == 0
        assert second.created == 0
        assert second.skipped == 2
        assert len(configs) == 2
        assert configs[0].base_url == "https://api.example.com"

    def test_base_url_override_tiene_prioridad(self, temp_db):
        spec = {
            "openapi": "3.0.0",
            "servers": [{"url": "https://wrong.example.com"}],
            "paths": {
                "/health": {
                    "get": {"operationId": "healthCheck"}
                }
            },
        }

        summary = import_openapi_spec(spec, base_url_override="https://override.example.com")

        assert summary.created == 1
        assert summary.configs[0].base_url == "https://override.example.com"
