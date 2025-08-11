# tests/conftest.py
import pytest
import duckdb
import os
from unittest.mock import MagicMock
from services import cache_config
from services.db import get_connection

@pytest.fixture(scope="session")
def duckdb_conn():
    """Provides a shared DuckDB connection for tests."""
    return get_connection()

@pytest.fixture(scope="session")
def test_db_path():
    """Returns the expected path to the DuckDB file."""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(base_dir, "data", "chinook.duckdb")

@pytest.fixture(scope="session")
def is_dev_env():
    """Returns True if running in development mode."""
    from config import IS_DEV
    return IS_DEV

@pytest.fixture(autouse=True)
def disable_cache():
    """Disable Flask-Caching decorators during tests."""
    cache_config.cache.memoize = lambda *args, **kwargs: (lambda f: f)

@pytest.fixture(scope="function")
def prepare_full_data_context(duckdb_conn):
    """Prepare DuckDB with full dataset and catalog tables."""
    from services.sql_core import get_events_shared
    from services.metadata import create_catalog_tables

    get_events_shared(duckdb_conn, [])
    create_catalog_tables(duckdb_conn)
    return duckdb_conn

@pytest.fixture(scope="function")
def prepare_empty_artist_context(duckdb_conn):
    """Prepare DuckDB with empty result for artist 'A Cor Do Som'."""
    from services.sql_core import get_events_shared
    from services.metadata import create_catalog_tables

    where_clauses = ["ar.Name = 'A Cor Do Som'"]
    get_events_shared(duckdb_conn, where_clauses)
    create_catalog_tables(duckdb_conn)
    return duckdb_conn

