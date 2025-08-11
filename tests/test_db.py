"""
Unit tests for services/db.py

These tests verify DuckDB connection logic, file existence checks,
and error handling for missing database files.
"""

import os
import pytest
import duckdb

def test_duckdb_connection_exists(duckdb_conn):
    """Test that a valid DuckDB connection is returned from the fixture."""
    assert duckdb_conn is not None
    assert duckdb_conn.execute("SELECT 1").fetchone()[0] == 1

def test_duckdb_file_path(test_db_path):
    """Test that the expected DuckDB file path exists on disk."""
    assert os.path.exists(test_db_path)

def test_missing_duckdb_file(monkeypatch):
    """Test that get_connection() raises FileNotFoundError if DB file is missing."""
    from services import db

    # Reset cached connection to force re-evaluation
    db._conn = None

    # Simulate missing file
    monkeypatch.setattr(os.path, "exists", lambda path: False)

    with pytest.raises(FileNotFoundError):
        db.get_connection()

def test_duckdb_connection_creation(monkeypatch):
    """Test that get_connection() creates a new DuckDB connection when needed."""
    from services import db

    # Reset cached connection
    db._conn = None

    # Simulate file exists
    monkeypatch.setattr(os.path, "exists", lambda path: True)

    # Simulate DuckDB connection
    class DummyConn:
        def execute(self, query): return [(1,)]

    monkeypatch.setattr(duckdb, "connect", lambda path, read_only: DummyConn())

    conn = db.get_connection()
    assert conn.execute("SELECT 1")[0][0] == 1

def test_missing_duckdb_file_real_logging(monkeypatch, caplog):
    """Ensure real log_msg is executed when DB file is missing."""
    from services import db

    db._conn = None

    # Patch ENABLE_LOGGING inside logging_utils
    monkeypatch.setattr("services.logging_utils.ENABLE_LOGGING", True)

    # Simulate missing file
    monkeypatch.setattr(os.path, "exists", lambda path: False)

    with caplog.at_level("ERROR"):
        with pytest.raises(FileNotFoundError):
            db.get_connection()

    assert any("DuckDB file missing" in record.message for record in caplog.records)
