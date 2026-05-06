import json
import logging
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet

from app.core.config import settings
from app.core.database import get_connection
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


class TestConfigEncryption:
    """AF-005: auth_config encryption at rest."""

    ENCRYPTION_KEY = Fernet.generate_key().decode()

    def test_encrypt_decrypt_roundtrip(self, temp_db):
        """Save with auth_config + ENCRYPTION_KEY → read back → plaintext matches."""
        with patch.object(settings, "ENCRYPTION_KEY", self.ENCRYPTION_KEY):
            saved = save_config(SavedConfigCreate(
                name="encrypted-config",
                url="https://api.example.com/users",
                method="GET",
                auth_config={
                    "token_url": "https://auth.example.com/oauth/token",
                    "client_id": "my-client-id",
                    "client_secret": "super-secret-123",
                    "scope": "read:users",
                },
            ))

            # Read back via repository
            configs = list_configs()
            assert len(configs) == 1
            assert configs[0].auth_config is not None
            assert configs[0].auth_config.token_url == "https://auth.example.com/oauth/token"
            assert configs[0].auth_config.client_secret == "super-secret-123"

            # Verify the stored value IS ciphertext, not plaintext
            with get_connection() as conn:
                raw = conn.execute(
                    "SELECT auth_config FROM saved_configs WHERE id = ?",
                    (saved.id,)
                ).fetchone()
            assert raw["auth_config"] is not None
            assert "super-secret-123" not in raw["auth_config"]

    def test_config_sin_auth_config_no_necesita_encrypt(self, temp_db):
        """Config without auth_config works fine — no encryption needed."""
        with patch.object(settings, "ENCRYPTION_KEY", self.ENCRYPTION_KEY):
            saved = save_config(SavedConfigCreate(
                name="no-auth-config",
                url="https://api.example.com/data",
                method="GET",
            ))
            assert saved.auth_config is None

            configs = list_configs()
            assert len(configs) == 1
            assert configs[0].auth_config is None

    def test_legacy_plaintext_row_se_lee_con_warning(self, temp_db, caplog):
        """A pre-existing plaintext auth_config row is read correctly (with warning)."""
        # Insert a legacy plaintext row directly into the DB
        plaintext_json = json.dumps({
            "type": "oauth2_client_credentials",
            "token_url": "https://legacy.example.com/token",
            "client_id": "legacy-id",
            "client_secret": "legacy-secret",
            "scope": None,
        })
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO saved_configs (name, url, method, auth_config) VALUES (?, ?, ?, ?)",
                ("legacy-config", "https://api.example.com", "GET", plaintext_json),
            )

        # With ENCRYPTION_KEY set, reading should handle the plaintext gracefully
        with patch.object(settings, "ENCRYPTION_KEY", self.ENCRYPTION_KEY):
            with caplog.at_level(logging.WARNING):
                configs = list_configs()

        assert len(configs) == 1
        assert configs[0].auth_config is not None
        assert configs[0].auth_config.token_url == "https://legacy.example.com/token"
        assert configs[0].auth_config.client_id == "legacy-id"

        # A warning should have been logged about the plaintext row
        warning_logs = [r.message for r in caplog.records if r.levelno == logging.WARNING]
        assert any("plaintext" in msg.lower() or "legacy" in msg.lower()
                   for msg in warning_logs), f"No plaintext warning found in: {warning_logs}"

    def test_missing_encryption_key_fallback_plaintext(self, temp_db, caplog):
        """Without ENCRYPTION_KEY, configs are stored and read as plaintext."""
        with patch.object(settings, "ENCRYPTION_KEY", None):
            with caplog.at_level(logging.WARNING):
                saved = save_config(SavedConfigCreate(
                    name="plaintext-fallback",
                    url="https://api.example.com/data",
                    method="GET",
                    auth_config={
                        "token_url": "https://auth.example.com/token",
                        "client_id": "fallback-id",
                        "client_secret": "fallback-secret",
                    },
                ))

            # Reading back should work
            configs = list_configs()
            assert len(configs) == 1
            assert configs[0].auth_config is not None
            assert configs[0].auth_config.client_id == "fallback-id"
            assert configs[0].auth_config.client_secret == "fallback-secret"

        # A warning should have been logged about missing ENCRYPTION_KEY
        warning_logs = [r.message for r in caplog.records if r.levelno == logging.WARNING]
        assert any("encryption" in msg.lower() for msg in warning_logs), \
            f"No encryption warning found in: {warning_logs}"
