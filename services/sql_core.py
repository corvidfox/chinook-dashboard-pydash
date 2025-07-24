"""
sql_core.py

Reusable SQL queries that support cross-page data features like event stream.
Includes fingerprint-aware event filtering.
"""

from typing import List, Optional, Tuple
from duckdb import DuckDBPyConnection
import hashlib
import pandas as pd
import json
from services.logging_utils import log_msg


def hash_invoice_ids(df: pd.DataFrame) -> str:
    """
    Generates a hash signature based on sorted, unique InvoiceIds.

    Parameters:
        df (pd.DataFrame): Filtered event-level data with InvoiceId column.

    Returns:
        str: MD5 hash representing the invoice set's identity.
    """
    invoice_ids = df["InvoiceId"].dropna().unique()
    sorted_ids = sorted(map(str, invoice_ids))
    serialized = ",".join(sorted_ids)
    return hashlib.md5(serialized.encode()).hexdigest()

def hash_dataframe(df: pd.DataFrame) -> str:
    """
    Produce an MD5 fingerprint of a dataframe.
    """
    payload = df.to_csv(index=False).encode("utf8")
    return hashlib.md5(payload).hexdigest()

def hash_kpi_bundle(bundle: dict) -> str:
    """
    Produce an MD5 fingerprint of a KPI‐bundle dict, 
    converting any DataFrames into JSON‐serializable dicts.
    """
    def _serialize(o):
        # If it’s a DataFrame, turn it into an “orient=split” dict:
        if isinstance(o, pd.DataFrame):
            return o.to_dict(orient="split")

        # Let the JSON module recurse into lists/dicts:
        raise TypeError(
            f"Object of type {o.__class__.__name__} is not JSON serializable"
            )

    # json.dumps will call _serialize() whenever it hits a DataFrame
    payload = json.dumps(
        bundle,
        default=_serialize,
        sort_keys=True,
    ).encode("utf8")

    return hashlib.md5(payload).hexdigest()

def get_events_shared(
    conn: DuckDBPyConnection,
    where_clauses: List[str],
    previous_hash: Optional[str] = None
) -> Tuple[Optional[pd.DataFrame], str]:
    """
    Fetches filtered invoice metadata and stores it as a temp DuckDB table
    only if the data has changed.

    Parameters:
        conn (DuckDBPyConnection): DuckDB connection object
        where_clauses (List[str]): SQL filter clauses (artist, genre, country)
        previous_hash (str, optional): Prior hash of InvoiceId set

    Returns:
        Tuple[Optional[pd.DataFrame], str]: DataFrame (or None if unchanged),
        and the new hash signature.
    """
    log_msg("[SQL CORE] Running get_events_shared()")

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    query = f"""
        SELECT
            i.CustomerId,
            DATE(i.InvoiceDate) AS dt,
            i.InvoiceId
        FROM Invoice i
        JOIN InvoiceLine il ON i.InvoiceId = il.InvoiceId
        JOIN Track t ON il.TrackId = t.TrackId
        JOIN Album al ON t.AlbumId = al.AlbumId
        JOIN Artist ar ON al.ArtistId = ar.ArtistId
        JOIN Genre g ON t.GenreId = g.GenreId
        {where_sql}
    """

    df = conn.execute(query).fetchdf()
    log_msg(f"     [SQL CORE] Raw query returned {len(df)} rows before deduplication.")

    df_cleaned = (
        df.drop_duplicates(subset=["CustomerId", "InvoiceId", "dt"])
          .sort_values(["CustomerId", "dt"])
    )

    log_msg(f"     [SQL CORE] {len(df_cleaned)} cleaned rows across {df_cleaned['InvoiceId'].nunique()} invoices")

    new_hash = hash_invoice_ids(df_cleaned)

    if new_hash == previous_hash:
        existing_tables = {row[0] for row in conn.execute("SHOW TABLES").fetchall()}
        if "filtered_invoices" in existing_tables:
            log_msg(f"     [SQL CORE] Skipping update: hash matched ({new_hash})")
            return None, new_hash

        log_msg("     [SQL CORE] Table missing — materializing filtered_invoices.")

    conn.register("df_cleaned", df_cleaned)
    conn.execute("CREATE OR REPLACE TEMP TABLE filtered_invoices AS SELECT * FROM df_cleaned")
    conn.unregister("df_cleaned")

    log_msg("     [SQL CORE] Temp table 'filtered_invoices' updated successfully")

    return df_cleaned, new_hash