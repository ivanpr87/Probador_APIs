"""Tests for database migration hardening (AF-006) and check_same_thread doc (AF-015)."""

import sqlite3
from unittest.mock import MagicMock, patch

import pytest

from app.core.database import init_db


class TestMigrationErrorHandling:
    """AF-006: Migration except blocks catch only sqlite3.OperationalError."""

    def test_init_db_es_idempotente_sin_columnas_duplicadas(self, temp_db):
        """Calling init_db twice on the same DB should not raise."""
        # First call already happened in temp_db fixture
        # Second call should be safe — duplicate columns swallowed
        init_db()  # must not raise

    def test_operational_error_duplicado_es_ignorado(self):
        """sqlite3.OperationalError with 'duplicate column' is swallowed."""
        alter_calls = []

        def mock_execute(sql, *args):
            if "ALTER TABLE" in sql:
                alter_calls.append(sql)
                raise sqlite3.OperationalError("duplicate column name: base_url")
            return MagicMock()

        mock_conn = MagicMock()
        mock_conn.execute.side_effect = mock_execute
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)

        with patch("app.core.database.get_connection", return_value=mock_conn):
            init_db()  # must not raise

        assert len(alter_calls) > 0, "ALTER TABLE should have been attempted"

    def test_operational_error_no_relacionado_propaga(self):
        """Non-duplicate-column OperationalError must propagate."""
        alter_calls = []

        def mock_execute(sql, *args):
            if "ALTER TABLE" in sql:
                alter_calls.append(sql)
                raise sqlite3.OperationalError("disk I/O error — database is corrupt")
            if "CREATE TABLE" in sql:
                return MagicMock()
            raise AssertionError(f"should not reach other queries: {sql[:50]}")

        mock_conn = MagicMock()
        mock_conn.execute.side_effect = mock_execute
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)

        with patch("app.core.database.get_connection", return_value=mock_conn):
            with pytest.raises(sqlite3.OperationalError, match="disk I/O"):
                init_db()

    def test_otro_tipo_de_excepcion_propaga(self):
        """Non-OperationalError exceptions must propagate (not swallowed)."""
        alter_calls = []

        def mock_execute(sql, *args):
            if "ALTER TABLE" in sql:
                alter_calls.append(sql)
                raise MemoryError("out of memory during migration")
            if "CREATE TABLE" in sql:
                return MagicMock()
            raise AssertionError(f"should not reach other queries: {sql[:50]}")

        mock_conn = MagicMock()
        mock_conn.execute.side_effect = mock_execute
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)

        with patch("app.core.database.get_connection", return_value=mock_conn):
            with pytest.raises(MemoryError, match="out of memory"):
                init_db()


class TestCheckSameThreadDoc:
    """AF-015: check_same_thread=False debe estar documentado."""

    def test_check_same_thread_tiene_comentario_explicativo(self):
        """GIVEN database.py WHEN get_connection se inspecciona THEN hay un comentario explicando check_same_thread."""
        import app.core.database as db_mod
        import inspect

        source = inspect.getsource(db_mod.get_connection)

        # Debe existir un comentario que explique por que se usa check_same_thread=False
        assert "# check_same_thread=False" in source, (
            "AF-015: get_connection debe tener un comentario que documente "
            "explicitamente check_same_thread=False. Se espera algo como: "
            "'# check_same_thread=False — intentional for WAL-mode ...'"
        )
