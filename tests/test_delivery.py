import duckdb
import pyarrow as pa
import pytest

from warehouse_qe.cloud import identifier, sql_type
from warehouse_qe.delivery import assemble, compare
from warehouse_qe.generate import generate


@pytest.mark.parametrize("bad", ["orders;drop table x", "a.b", "x--", "", "x y"])
def test_identifiers_reject_sql(bad):
    with pytest.raises(ValueError):
        identifier(bad)


@pytest.mark.parametrize(
    "kind,expected",
    [
        ("postgres", "TIMESTAMP"),
        ("sqlserver", "DATETIME2"),
        ("snowflake", "TIMESTAMP_NTZ"),
    ],
)
def test_timestamp_type_mapping(kind, expected):
    assert sql_type(pa.timestamp("us"), kind) == expected


def test_delivery_csv_and_provenance(tmp_path):
    source = tmp_path / "source"
    generate(source, 100)
    records = assemble(source, source, tmp_path / "delivery")
    assert {r["source"] for r in records} == {
        "relational-extract",
        "csv",
        "parquet-file",
    }
    c = duckdb.connect()
    a = source / "payments/*.parquet"
    b = tmp_path / "delivery/payments/*.parquet"
    assert (
        c.execute(
            f"select count(*) from (select * from read_parquet('{a}') except all select * from read_parquet('{b}')) q"
        ).fetchone()[0]
        == 0
    )
    with pytest.raises(FileExistsError):
        assemble(source, source, tmp_path / "delivery")
    c.close()


def test_generator_refuses_overwrite(tmp_path):
    generate(tmp_path / "source", 100)
    with pytest.raises(FileExistsError):
        generate(tmp_path / "source", 100)


def test_exact_comparison_detects_same_count_corruption(tmp_path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    generate(a, 100)
    generate(b, 100)
    file = next((b / "orders").glob("*.parquet"))
    c = duckdb.connect()
    c.execute(
        f"create table modified as select * replace('shipped' as status) from read_parquet('{file}')"
    )
    file.unlink()
    c.execute(f"copy modified to '{file}' (format parquet)")
    c.close()
    result = next(r for r in compare(a, b) if r["table"] == "orders")
    assert (
        result["status"] == "FAIL"
        and result["missing"] == 100
        and result["extra"] == 100
    )


def test_stage_manifest_guard(tmp_path):
    from warehouse_qe.cloud import validate_stage_listing

    (tmp_path / "orders").mkdir()
    (tmp_path / "orders/a.parquet").touch()
    validate_stage_listing(
        tmp_path, ["s3://b/p/orders/a.parquet", "s3://b/p/delivery.json"]
    )
    with pytest.raises(ValueError):
        validate_stage_listing(tmp_path, ["s3://b/p/orders/a.parquet"])
    with pytest.raises(ValueError):
        validate_stage_listing(tmp_path, ["s3://b/p/delivery.json"])
    with pytest.raises(ValueError):
        validate_stage_listing(
            tmp_path, ["s3://b/p/delivery.json", "s3://b/p/extra.parquet"]
        )


@pytest.mark.parametrize(
    "left,right,expected",
    [
        ([(1, None), (2, "x")], [(1, None), (2, "x")], 0),
        ([(1, None)], [(1, "")], 1),
        ([(1, "x"), (1, "x")], [(1, "x")], 1),
        ([], [(1, "x")], 1),
        ([(1, "x")], [], 1),
    ],
)
def test_stream_reconciliation(left, right, expected):
    from warehouse_qe.reconcile import compare_streams

    result = compare_streams(iter(left), iter(right))
    assert result["mismatched_positions"] == expected
    assert result["status"] == ("FAIL" if expected else "PASS")


def test_s3_rejects_existing_prefix(monkeypatch, tmp_path):
    import boto3

    from warehouse_qe.cloud import upload

    class Occupied:
        def list_objects_v2(self, **kwargs):
            return {"KeyCount": 1}

    monkeypatch.setattr(boto3, "client", lambda *_: Occupied())
    with pytest.raises(FileExistsError):
        upload(tmp_path, "test-bucket", "retail-qe/run-001")


def test_failed_copy_preserves_audit(monkeypatch, tmp_path):
    import json

    from warehouse_qe import cloud

    source = tmp_path / "source"
    generate(source, 100)

    class Cursor:
        sfqid = "simulated-query-id"

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def execute(self, sql):
            if sql.startswith("COPY"):
                raise RuntimeError("injected copy failure")
            return self

        def fetchall(self):
            return [
                ("s3://bucket/run/" + str(f.relative_to(source)),)
                for f in source.rglob("*.parquet")
            ] + [("s3://bucket/run/delivery.json",)]

    class Connection:
        def cursor(self):
            return Cursor()

        def close(self):
            pass

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cloud, "snowflake_connection", lambda: Connection())
    with pytest.raises(RuntimeError, match="injected copy failure"):
        cloud.load_snowflake(source)
    audit = json.loads((tmp_path / "artifacts/cloud-load.json").read_text())
    assert audit[-1]["status"] == "ERROR"
