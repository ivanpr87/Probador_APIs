from app.services.openapi_service import parse_openapi_spec


class TestParseOpenAPISpec:

    def test_parsea_openapi_3_con_servers_y_request_body(self):
        spec = {
            "openapi": "3.0.0",
            "servers": [{"url": "https://api.example.com/v1"}],
            "paths": {
                "/users": {
                    "post": {
                        "operationId": "createUser",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string", "example": "Ivan"},
                                            "age": {"type": "integer"},
                                        },
                                    }
                                }
                            }
                        },
                    }
                }
            },
        }

        parsed = parse_openapi_spec(spec, name_prefix="Imported")

        assert len(parsed) == 1
        assert parsed[0].name == "Imported createUser"
        assert parsed[0].url == "/users"
        assert parsed[0].method == "POST"
        assert parsed[0].base_url == "https://api.example.com/v1"
        assert parsed[0].payload == {"name": "Ivan", "age": 0}

    def test_resuelve_refs_locales(self):
        spec = {
            "openapi": "3.0.0",
            "paths": {
                "/orders": {
                    "post": {
                        "requestBody": {
                            "$ref": "#/components/requestBodies/OrderBody"
                        }
                    }
                }
            },
            "components": {
                "requestBodies": {
                    "OrderBody": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/OrderPayload"}
                            }
                        }
                    }
                },
                "schemas": {
                    "OrderPayload": {
                        "type": "object",
                        "properties": {
                            "sku": {"type": "string"},
                            "quantity": {"type": "integer", "default": 1},
                        },
                    }
                },
            },
        }

        parsed = parse_openapi_spec(spec)

        assert len(parsed) == 1
        assert parsed[0].payload == {"sku": "string", "quantity": 1}

    def test_soporta_swagger_2_basico(self):
        spec = {
            "swagger": "2.0",
            "host": "legacy.example.com",
            "basePath": "/api",
            "schemes": ["https"],
            "paths": {
                "/login": {
                    "post": {
                        "parameters": [
                            {
                                "in": "body",
                                "name": "body",
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "username": {"type": "string"},
                                        "password": {"type": "string"},
                                    },
                                },
                            }
                        ]
                    }
                }
            },
        }

        parsed = parse_openapi_spec(spec)

        assert len(parsed) == 1
        assert parsed[0].base_url == "https://legacy.example.com/api"
        assert parsed[0].payload == {"username": "string", "password": "string"}

    def test_ignora_metodos_no_soportados(self):
        spec = {
            "openapi": "3.0.0",
            "paths": {
                "/events": {
                    "trace": {},
                    "get": {},
                }
            },
        }

        parsed = parse_openapi_spec(spec)

        assert len(parsed) == 1
        assert parsed[0].method == "GET"
