"""Bounded-memory exact comparison of delivered records against Snowflake RAW."""

from itertools import zip_longest
from pathlib import Path

import duckdb
import pyarrow.parquet as pq

KEYS = {
    "customers": ["customer_id"],
    "products": ["product_id"],
    "sellers": ["seller_id"],
    "orders": ["order_id"],
    "order_items": ["order_id", "line_id"],
    "payments": ["order_id", "payment_sequence"],
    "reviews": ["review_id"],
}


def cursor_rows(cursor, size=10000):
    while rows := cursor.fetchmany(size):
        yield from (tuple(row) for row in rows)


def compare_streams(expected, actual):
    missing = object()
    mismatches = 0
    compared = 0
    samples = []
    for left, right in zip_longest(expected, actual, fillvalue=missing):
        compared += 1
        if left != right:
            mismatches += 1
            if len(samples) < 10:
                samples.append(
                    {
                        "expected": None if left is missing else left,
                        "actual": None if right is missing else right,
                    }
                )
    return {
        "status": "FAIL" if mismatches else "PASS",
        "rows_compared": compared,
        "mismatched_positions": mismatches,
        "samples": samples,
    }


def reconcile_snowflake(connection, root: Path):
    """Sorted-key stream comparison. A missing row can shift later positional samples;
    mismatch count is not a distinct defective-record count. Grain checks run separately.
    Exact equality preserves decimals, timestamps, nulls and duplicate multiplicity.
    """
    results = []
    with duckdb.connect() as local:
        local.execute("SET memory_limit='2GB'")
        for table, keys in KEYS.items():
            schema = pq.read_schema(min((root / table).glob("*.parquet")))
            columns = ",".join(field.name for field in schema)
            order = ",".join(keys)
            expected = local.execute(
                f"SELECT {columns} FROM read_parquet('{(root / table).resolve().as_posix()}/*.parquet') ORDER BY {order}"
            )
            with connection.cursor() as remote:
                remote.execute(f"SELECT {columns} FROM RAW.{table} ORDER BY {order}")
                results.append(
                    {
                        "table": table,
                        **compare_streams(cursor_rows(expected), cursor_rows(remote)),
                    }
                )
    return results
