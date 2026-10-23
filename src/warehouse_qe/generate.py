"""Deterministic, vectorized, bounded-memory retail data. No real personal data."""

import hashlib
import json
import time
from pathlib import Path

import duckdb

TABLES = (
    "customers",
    "products",
    "sellers",
    "orders",
    "order_items",
    "payments",
    "reviews",
)


def generate(root: Path, orders: int, chunk: int = 1_000_000):
    if orders < 100 or chunk < 100:
        raise ValueError("orders and chunk must be >= 100")
    root.mkdir(parents=True, exist_ok=True)
    if (root / "manifest.json").exists():
        raise FileExistsError("Dataset already exists; use a new output directory")
    con = duckdb.connect()
    con.execute("SET memory_limit='2GB'")
    customers, products, sellers = (
        max(100, orders // 5),
        max(50, orders // 100),
        max(10, orders // 10000),
    )
    definitions = {
        "customers": (
            customers,
            "select i customer_id, 'Customer-' || i customer_name, 'City-' || (i % 200) city, CASE WHEN i%3=0 THEN 'SP' WHEN i%3=1 THEN 'RJ' ELSE 'MG' END state, timestamp '2023-01-01' updated_at, 1 batch_id from range({lo}, {hi}) t(i)",
        ),
        "products": (
            products,
            "select i product_id, 'Category-' || (i % 30) category, cast(10 + (i%10000)/100.0 as decimal(18,2)) list_price from range({lo}, {hi}) t(i)",
        ),
        "sellers": (
            sellers,
            "select i seller_id, 'Seller-' || i seller_name, 'SP' state from range({lo}, {hi}) t(i)",
        ),
        "orders": (
            orders,
            f"select i order_id, 1+((i*17)%{customers}) customer_id, timestamp '2024-01-01' + (i%730)*interval '1 day' purchased_at, timestamp '2024-01-01' + (i%730+3)*interval '1 day' delivered_at, case when i%20=0 then 'cancelled' else 'delivered' end status, timestamp '2026-01-01' updated_at, 1 batch_id from range({{lo}}, {{hi}}) t(i)",
        ),
        "order_items": (
            orders,
            f"select i order_id, j line_id, 1+((i+j*13)%{products}) product_id, 1+((i+j)%{sellers}) seller_id, cast(1+(i+j)%3 as integer) quantity, cast(10+((i*7+j)%10000)/100.0 as decimal(18,2)) unit_price, cast((i+j)%5 as decimal(18,2)) discount_amount, cast(2+(i%100)/100.0 as decimal(18,2)) freight_amount, 1 batch_id from range({{lo}}, {{hi}}) t(i) cross join range(1,4) u(j)",
        ),
        "payments": (
            orders,
            "select i order_id, j payment_sequence, 'credit_card' payment_method, cast(total_amount/2 as decimal(18,2)) payment_amount, 1 batch_id from (select i, sum(cast((1+(i+k)%3)*(10+((i*7+k)%10000)/100.0)-(i+k)%5 + 2+(i%100)/100.0 as decimal(18,2))) total_amount from range({lo},{hi}) t(i) cross join range(1,4) u(k) group by i) x cross join range(1,3) p(j)",
        ),
        "reviews": (
            orders,
            "select i review_id, i order_id, 1+(i%5) score, case when i%10=0 then NULL else 'Synthetic review' end review_text, 1 batch_id from range({lo},{hi}) t(i) where i%3=0",
        ),
    }
    started = time.time()
    manifest = {
        "kind": "synthetic-retail",
        "seed": "deterministic-v1",
        "orders": orders,
        "tables": {},
        "files": [],
    }
    for table, (count, query) in definitions.items():
        folder = root / table
        folder.mkdir(exist_ok=True)
        if list(folder.glob("*")):
            raise FileExistsError(f"{folder} is not empty")
        total = 0
        for lo in range(1, count + 1, chunk):
            hi = min(count + 1, lo + chunk)
            target = folder / f"part-{lo:012d}.parquet"
            sql = query.format(lo=lo, hi=hi)
            con.execute(
                f"COPY ({sql}) TO '{target.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)"
            )
            n = con.execute(
                f"select count(*) from read_parquet('{target.as_posix()}')"
            ).fetchone()[0]
            total += n
            digest = hashlib.file_digest(target.open("rb"), "sha256").hexdigest()
            manifest["files"].append(
                {
                    "path": str(target.relative_to(root)),
                    "rows": n,
                    "bytes": target.stat().st_size,
                    "sha256": digest,
                }
            )
        manifest["tables"][table] = total
        print(f"{table}: {total:,} rows", flush=True)
    # A genuine CSV delivery source in addition to columnar large-table data.
    csv = root / "payments_csv"
    csv.mkdir(exist_ok=True)
    con.execute(
        f"COPY (select * from read_parquet('{root.as_posix()}/payments/*.parquet')) TO '{csv.as_posix()}/payments.csv' (HEADER, DELIMITER ',')"
    )
    manifest["total_rows"] = sum(manifest["tables"].values())
    manifest["seconds"] = round(time.time() - started, 2)
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2))
    con.close()
    return manifest


def bootstrap(root: Path, database: Path):
    con = duckdb.connect(str(database))
    con.execute("SET memory_limit='3GB'")
    con.execute("create schema if not exists raw")
    for table in TABLES:
        con.execute(
            f"create or replace view raw.{table} as select * from read_parquet('{root.resolve().as_posix()}/{table}/*.parquet')"
        )
    con.close()
