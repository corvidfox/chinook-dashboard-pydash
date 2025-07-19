"""
db.py

Handles connection logic to the Chinook DuckDB database.
Ensures safe and read-only access with resilient path resolution,
built relative to the project root for cross-platform consistency.
"""

import duckdb
import os
from duckdb import DuckDBPyConnection

def get_connection() -> DuckDBPyConnection:
    """Establishes a read-only DuckDB connection to the Chinook dataset.

    Resolves the path to `chinook.duckdb` located in the `/data/` directory
    at the project root. Raises a `FileNotFoundError` if the database file
    is missing.

    Returns:
        DuckDBPyConnection: An active connection to the Chinook database.

    Raises:
        FileNotFoundError: If the database file is not found at the expected path.
    """
    # Step up from /services/ to project root
    base_dir = os.path.dirname(os.path.dirname(__file__))
    db_path = os.path.join(base_dir, "data", "chinook.duckdb")

    if not os.path.exists(db_path):
        raise FileNotFoundError(f"DuckDB file not found at {db_path}")

    return duckdb.connect(db_path, read_only=True)
