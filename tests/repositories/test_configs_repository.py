from app.models.response_models import SavedConfigCreate
from app.repositories.configs_repository import list_configs, save_config


class TestConfigsRepository:

    def test_persiste_auth_config_en_saved_config(self, temp_db):
        saved = save_config(SavedConfigCreate(
            name="oauth config",
            url="/users",
            method="GET",
            base_url="https://api.example.com",
            auth_config={
                "token_url": "https://auth.example.com/oauth/token",
                "client_id": "client-id",
                "client_secret": "client-secret",
                "scope": "read:users",
            },
        ))

        configs = list_configs()

        assert saved.auth_config is not None
        assert configs[0].auth_config is not None
        assert configs[0].auth_config.token_url == "https://auth.example.com/oauth/token"
        assert configs[0].auth_config.scope == "read:users"
