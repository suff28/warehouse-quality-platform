"""Real source and cloud adapters. Never called by the local smoke workflow."""

import argparse
import hashlib
import json
import os
import re
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from .generate import TABLES


def identifier(value):
    if not re.fullmatch("[A-Za-z_][A-Za-z0-9_]*", value):
        raise ValueError(f"Unsafe identifier: {value!r}")
    return value


def source_connection(kind):
    if kind == "postgres":
        import psycopg

        return psycopg.connect(os.environ["POSTGRES_DSN"])
    import pyodbc

    return pyodbc.connect(os.environ["SQLSERVER_CONNECTION_STRING"])


def snowflake_connection():
    import snowflake.connector

    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ.get("SNOWFLAKE_PASSWORD", ""),
        authenticator=os.environ.get("SNOWFLAKE_AUTHENTICATOR", "snowflake"),
        role=os.environ.get("SNOWFLAKE_ROLE", "RETAIL_QE"),
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "RETAIL_QE_WH"),
        database=os.environ.get("SNOWFLAKE_DATABASE", "RETAIL_QE"),
        schema="RAW",
    )


def sql_type(t, kind):
    if pa.types.is_integer(t):
        return "BIGINT"
    if pa.types.is_decimal(t):
        return f"DECIMAL({t.precision},{t.scale})"
    if pa.types.is_timestamp(t):
        return {
            "sqlserver": "DATETIME2",
            "postgres": "TIMESTAMP",
            "snowflake": "TIMESTAMP_NTZ",
        }[kind]
    if pa.types.is_date(t):
        return "DATE"
    if pa.types.is_boolean(t):
        return "BOOLEAN" if kind != "sqlserver" else "BIT"
    if pa.types.is_floating(t):
        return "FLOAT"
    return "VARCHAR(500)"


def seed_source(kind, root):
    # Source tables are intentionally seeded only once; reject existing tables.
    with source_connection(kind) as con:
        cur = con.cursor()
        if kind == "postgres":
            cur.execute("CREATE SCHEMA IF NOT EXISTS retail_source")
        else:
            cur.execute(
                "IF SCHEMA_ID('retail_source') IS NULL EXEC('CREATE SCHEMA retail_source')"
            )
        for table in ["customers", "products", "sellers", "orders"]:
            files = sorted((root / table).glob("*.parquet"))
            if not files:
                raise FileNotFoundError(table)
            schema = pq.read_schema(files[0])
            columns = ",".join(
                f"{identifier(f.name)} {sql_type(f.type, kind)}" for f in schema
            )
            cur.execute(f"CREATE TABLE retail_source.{table} ({columns})")
            names = ",".join(identifier(f.name) for f in schema)
            for file in files:
                for batch in pq.ParquetFile(file).iter_batches(batch_size=10000):
                    values = list(zip(*(col.to_pylist() for col in batch.columns)))
                    if kind == "postgres":
                        with cur.copy(
                            f"COPY retail_source.{table} ({names}) FROM STDIN"
                        ) as cp:
                            for row in values:
                                cp.write_row(row)
                    else:
                        cur.fast_executemany = True
                        cur.executemany(
                            f"INSERT INTO retail_source.{table} ({names}) VALUES ({','.join('?' for _ in schema)})",
                            values,
                        )
            print(f"Seeded {kind}.{table}", flush=True)
        con.commit()


def extract(kind, root, output):
    # Quiescent/snapshot source required; no NOLOCK. Never read whole tables into pandas.
    output.mkdir(parents=True, exist_ok=True)
    with source_connection(kind) as con:
        control = con.cursor()
        control.execute(
            "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ"
            if kind == "postgres"
            else "SET TRANSACTION ISOLATION LEVEL SNAPSHOT"
        )
        for table in ["customers", "products", "sellers", "orders"]:
            cur = con.cursor(name=f"qe_{table}") if kind == "postgres" else con.cursor()
            schema = pq.read_schema(sorted((root / table).glob("*.parquet"))[0])
            cur.execute(
                f"SELECT {','.join(f.name for f in schema)} FROM retail_source.{table}"
            )
            folder = output / table
            folder.mkdir(exist_ok=True)
            if list(folder.glob("*.parquet")):
                raise FileExistsError(folder)
            part = 0
            while rows := cur.fetchmany(50000):
                arrays = [
                    pa.array([row[i] for row in rows], type=f.type)
                    for i, f in enumerate(schema)
                ]
                pq.write_table(
                    pa.Table.from_arrays(arrays, schema=schema),
                    folder / f"part-{part:06}.parquet",
                    compression="zstd",
                )
                part += 1
            cur.close()
        con.rollback()


def upload(root, bucket, prefix):
    import boto3

    if not prefix or ".." in prefix:
        raise ValueError("Provide a dedicated prefix")
    s3 = boto3.client("s3")
    if s3.list_objects_v2(
        Bucket=bucket, Prefix=prefix.rstrip("/") + "/", MaxKeys=1
    ).get("KeyCount", 0):
        raise FileExistsError("Delivery prefix is not empty; choose a new prefix")
    records = []
    for path in sorted(root.rglob("*.parquet")):
        key = prefix.rstrip("/") + "/" + path.relative_to(root).as_posix()
        with path.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        s3.upload_file(
            str(path),
            bucket,
            key,
            ExtraArgs={
                "ServerSideEncryption": "AES256",
                "Metadata": {"sha256": digest},
            },
        )
        head = s3.head_object(Bucket=bucket, Key=key)
        if (
            head["ContentLength"] != path.stat().st_size
            or head["Metadata"].get("sha256") != digest
        ):
            raise RuntimeError(f"Upload verification failed: {key}")
        records.append({"key": key, "bytes": path.stat().st_size, "sha256": digest})
    # Manifest last = publish marker. Consumer must use this exact immutable prefix.
    s3.put_object(
        Bucket=bucket,
        Key=prefix.rstrip("/") + "/delivery.json",
        Body=json.dumps(records).encode(),
        ServerSideEncryption="AES256",
    )
    return records


def validate_stage_listing(root, names):
    expected = {str(p.relative_to(root)) for p in root.rglob("*.parquet")}
    matched = set()
    if not any(n.endswith("/delivery.json") for n in names):
        raise ValueError("Missing completed-delivery marker")
    for name in names:
        if name.endswith(".parquet"):
            matches = [p for p in expected if name.endswith("/" + p)]
            if len(matches) != 1:
                raise ValueError("Unexpected staged Parquet file: " + name)
            matched.add(matches[0])
    if matched != expected:
        raise ValueError("Stage is missing expected Parquet files")


def load_snowflake(root):
    # Stage points at one immutable delivery prefix. Fail fast; retain Snowflake copy history.
    con = snowflake_connection()
    results = []
    try:
        with con.cursor() as cur:
            cur.execute("LIST @RAW.RETAIL_STAGE")
            validate_stage_listing(root, [row[0] for row in cur.fetchall()])
            for table in TABLES:
                files = sorted((root / table).glob("*.parquet"))
                schema = pq.read_schema(files[0])
                columns = ",".join(
                    f"{identifier(f.name)} {sql_type(f.type, 'snowflake')}"
                    for f in schema
                )
                cur.execute(f"CREATE TABLE IF NOT EXISTS RAW.{table} ({columns})")
                cur.execute(
                    f"COPY INTO RAW.{table} FROM @RAW.RETAIL_STAGE/{table}/ FILE_FORMAT=(TYPE=PARQUET USE_LOGICAL_TYPE=TRUE) MATCH_BY_COLUMN_NAME=CASE_INSENSITIVE ON_ERROR=ABORT_STATEMENT"
                )
                results.append(
                    {
                        "table": table,
                        "query_id": cur.sfqid,
                        "copy_results": cur.fetchall(),
                    }
                )
                expected = sum(pq.ParquetFile(file).metadata.num_rows for file in files)
                cur.execute(f"SELECT COUNT(*) FROM RAW.{table}")
                actual = cur.fetchone()[0]
                results[-1].update(expected_rows=expected, actual_rows=actual)
                if actual != expected:
                    raise ValueError(
                        f"{table}: loaded row count {actual} != delivery {expected}"
                    )
    except Exception as exc:
        results.append({"status": "ERROR", "error": str(exc)})
        raise
    finally:
        Path("artifacts").mkdir(exist_ok=True)
        Path("artifacts/cloud-load.json").write_text(
            json.dumps(results, indent=2, default=str)
        )
        con.close()
    return results


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "action", choices=["seed", "extract", "upload", "load", "check", "reconcile"]
    )
    p.add_argument("--source", choices=["postgres", "sqlserver"], default="postgres")
    p.add_argument("--data", type=Path, default=Path("data/smoke"))
    p.add_argument("--output", type=Path, default=Path("data/extracted"))
    p.add_argument("--bucket")
    p.add_argument("--prefix")
    a = p.parse_args()
    if a.action == "seed":
        seed_source(a.source, a.data)
    elif a.action == "extract":
        extract(a.source, a.data, a.output)
    elif a.action == "upload":
        if not a.bucket or not a.prefix:
            p.error("upload requires --bucket and --prefix")
        print(json.dumps(upload(a.data, a.bucket, a.prefix), indent=2))
    elif a.action == "load":
        result = load_snowflake(a.data)
        Path("artifacts").mkdir(exist_ok=True)
        Path("artifacts/cloud-load.json").write_text(
            json.dumps(result, indent=2, default=str)
        )
    elif a.action == "reconcile":
        from .reconcile import reconcile_snowflake

        with snowflake_connection() as con:
            results = reconcile_snowflake(con, a.data)
        Path("artifacts").mkdir(exist_ok=True)
        Path("artifacts/cloud-reconciliation.json").write_text(
            json.dumps(results, indent=2, default=str)
        )
        raise SystemExit(int(any(r["status"] != "PASS" for r in results)))
    else:
        from .quality import run_checks

        with snowflake_connection() as con:
            results = run_checks(
                con.cursor(), Path("config/checks.yml"), Path("artifacts/snowflake")
            )
            raise SystemExit(int(any(r["status"] != "PASS" for r in results)))


if __name__ == "__main__":
    main()
