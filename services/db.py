"""
db.py

Manages persistent connection logic to the Chinook DuckDB database.
Ensures safe and read-only access with resilient path resolution,
and maintains a single connection instance for temp table visibility across modules.
"""

import os
import duckdb
from services.logging_utils import log_msg
from duckdb import DuckDBPyConnection

# Persistent connection cache
_conn: DuckDBPyConnection | None = None

def get_connection() -> DuckDBPyConnection:
    """
    Returns a persistent, read-only DuckDB connection to the Chinook dataset.
    Ensures that temp tables remain visible across modules and callbacks.

    Resolves the path to `chinook.duckdb` located in the `/data/` directory
    at the project root. Raises a `FileNotFoundError` if the database file is
    missing or inaccessible.

    Returns:
        DuckDBPyConnection: Shared DuckDB connection instance.

    Raises:
        FileNotFoundError: If the database file is not found at the expected path.
    """

    global _conn

    if _conn is not None:
        log_msg("[DB] Reusing existing DuckDB connection.")
        return _conn

    base_dir = os.path.dirname(os.path.dirname(__file__))
    db_path = os.path.join(base_dir, "data", "chinook.duckdb")
    
    log_msg(f"[DB] Initializing DuckDB connection from: {db_path}")

    if not os.path.exists(db_path):
        log_msg(f"  [DB] DuckDB file missing at {db_path}", level="error")
        raise FileNotFoundError(f"DuckDB file not found at {db_path}")

    _conn = duckdb.connect(db_path, read_only=True)
    log_msg("     [DB] Connection opened in read-only mode")
    log_msg(f"     [DB] Connection object ID: {id(_conn)}", level="debug")

    return _conn
