import json
import logging
from typing import List, Optional

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings
from app.core.database import get_connection
from app.models.response_models import SavedConfig, SavedConfigCreate

logger = logging.getLogger(__name__)


def _get_fernet() -> Fernet | None:
    """Return a Fernet instance if ENCRYPTION_KEY is configured, else None."""
    key = settings.ENCRYPTION_KEY
    if not key:
        logger.warning(
            "ENCRYPTION_KEY is not set — auth_config will be stored as plaintext. "
            "Set the ENCRYPTION_KEY environment variable to enable encryption at rest."
        )
        return None
    return Fernet(key.encode() if isinstance(key, str) else key)


def _encrypt_auth_config(auth_config_json: str) -> str:
    """Encrypt auth_config JSON string using Fernet. Returns ciphertext as string."""
    fernet = _get_fernet()
    if fernet is None:
        return auth_config_json  # fallback to plaintext
    return fernet.encrypt(auth_config_json.encode()).decode()


def _decrypt_auth_config(stored_value: str) -> str | None:
    """Decrypt auth_config. Returns plaintext JSON string, or None on persistent error."""
    fernet = _get_fernet()
    if fernet is None:
        # No key configured — assume stored value is plaintext
        return stored_value

    try:
        return fernet.decrypt(stored_value.encode()).decode()
    except InvalidToken:
        # Legacy row: stored as plaintext, not ciphertext
        logger.warning(
            "Found plaintext auth_config in the database (not encrypted). "
            "This is a legacy row — it will be encrypted on next save. "
            "Returning plaintext value for now."
        )
        return stored_value
    except Exception:
        logger.exception("Unexpected error decrypting auth_config")
        return None


def save_config(data: SavedConfigCreate) -> SavedConfig:
    raw_auth = data.auth_config.model_dump_json() if data.auth_config else None
    encrypted_auth = _encrypt_auth_config(raw_auth) if raw_auth else None

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO saved_configs (name, url, method, payload, headers, base_url, auth_config)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.name,
                data.url,
                data.method,
                json.dumps(data.payload) if data.payload else None,
                json.dumps(data.headers) if data.headers else None,
                data.base_url or None,
                encrypted_auth,
            ),
        )
        row = conn.execute(
            "SELECT * FROM saved_configs WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()

    return _row_to_config(row)


def list_configs() -> List[SavedConfig]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM saved_configs ORDER BY created_at DESC"
        ).fetchall()
    return [_row_to_config(r) for r in rows]


def delete_config(config_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM saved_configs WHERE id = ?", (config_id,)
        )
    return cursor.rowcount > 0


def get_config_by_id(config_id: int) -> Optional[SavedConfig]:
    """AF-008: Fetch single config by id — scalar query, no list_configs() overhead."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM saved_configs WHERE id = ?", (config_id,)
        ).fetchone()
    if not row:
        return None
    return _row_to_config(row)


def config_exists(config_id: int) -> bool:
    """AF-008: Scalar check — verifica existencia de config por id en una sola query.
    Reemplaza list_configs() + any() que cargaba todas las configs."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM saved_configs WHERE id = ?", (config_id,)
        ).fetchone()
    return row is not None


def _row_to_config(row) -> SavedConfig:
    raw_auth = row["auth_config"]
    if raw_auth:
        decrypted = _decrypt_auth_config(raw_auth)
        if decrypted is None:
            auth_cfg = None
        else:
            auth_cfg = json.loads(decrypted)
    else:
        auth_cfg = None

    return SavedConfig(
        id=row["id"],
        name=row["name"],
        url=row["url"],
        method=row["method"],
        payload=json.loads(row["payload"]) if row["payload"] else None,
        headers=json.loads(row["headers"]) if row["headers"] else None,
        base_url=row["base_url"] if row["base_url"] else None,
        auth_config=auth_cfg,
        created_at=row["created_at"],
    )
