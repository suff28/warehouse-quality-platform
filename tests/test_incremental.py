"""Exercise the real dbt incremental model and snapshot across five arrivals."""

import os
import shutil
import subprocess
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]


def test_five_batch_lifecycle(baseline, tmp_path):
    database = tmp_path / "lifecycle.duckdb"
    shutil.copy2(baseline, database)

    def execute(sql):
        with duckdb.connect(str(database)) as c:
            return c.execute(sql).fetchall()

    def build(select):
        result = subprocess.run(
            [
                str(ROOT / ".venv/bin/dbt"),
                "build",
                "--select",
                select,
                "--project-dir",
                str(ROOT / "dbt"),
                "--profiles-dir",
                str(ROOT / "dbt"),
                "--target-path",
                str(tmp_path / "target"),
                "--log-path",
                str(tmp_path / "logs"),
            ],
            env={
                **os.environ,
                "WAREHOUSE_DB": str(database),
                "DBT_SEND_ANONYMOUS_USAGE_STATS": "false",
            },
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    execute("create or replace table raw.orders as select * from raw.orders")
    execute("create or replace table raw.customers as select * from raw.customers")
    # Batch 2: one new order and one changed order, same watermark timestamp.
    execute(
        "insert into raw.orders select 1001,customer_id,purchased_at,delivered_at,'processing',timestamp '2026-01-02',2 from raw.orders where order_id=1"
    )
    execute(
        "update raw.orders set status='shipped',updated_at=timestamp '2026-01-02',batch_id=2 where order_id=1"
    )
    build("fct_orders")
    assert execute("select count(*) from analytics.fct_orders")[0][0] == 1001
    assert (
        execute("select status from analytics.fct_orders where order_id=1")[0][0]
        == "shipped"
    )
    # Batch 3: customer address transition, source event timestamp retained.
    execute(
        "update raw.customers set city='New City',updated_at=timestamp '2025-01-01',batch_id=3 where customer_id=18"
    )
    build("customer_history+")
    build("fct_order_items")
    assert (
        execute("select count(*) from analytics.dim_customer where customer_id=18")[0][
            0
        ]
        == 2
    )
    assert (
        execute(
            "select count(*) from analytics.dim_customer where customer_id=18 and valid_to is null"
        )[0][0]
        == 1
    )
    assert (
        execute(
            "select count(*) from analytics.fct_order_items f join analytics.stg_orders o on f.order_id=o.order_id join analytics.dim_customer c on c.customer_key=f.customer_key where f.customer_id=18 and ((o.purchased_at<timestamp '2025-01-01' and c.city='New City') or (o.purchased_at>=timestamp '2025-01-01' and c.city!='New City'))"
        )[0][0]
        == 0
    )
    # Batch 4: purchase date predates every previous business date.
    execute(
        "insert into raw.orders select 1002,customer_id,timestamp '2023-12-01',timestamp '2023-12-04','delivered',timestamp '2026-01-03',4 from raw.orders where order_id=1"
    )
    build("fct_orders")
    assert (
        execute("select count(*) from analytics.fct_orders where order_id=1002")[0][0]
        == 1
    )
    # Replay exact arrival; deterministic merge must preserve both count and row values.
    before = execute("select * from analytics.fct_orders order by order_id")
    build("fct_orders")
    assert execute("select * from analytics.fct_orders order by order_id") == before
    # Batch 5 fails in an ingestion transaction, then retries successfully.
    with duckdb.connect(str(database)) as c:
        c.execute("begin")
        try:
            c.execute(
                "update raw.orders set status='cancelled',batch_id=5 where order_id=2"
            )
            c.execute("select cast('bad-date' as timestamp)")
        except duckdb.Error:
            c.execute("rollback")
    assert execute("select batch_id from raw.orders where order_id=2")[0][0] == 1
    execute(
        "update raw.orders set status='cancelled',batch_id=5,updated_at=timestamp '2026-01-04' where order_id=2"
    )
    build("fct_orders")
    assert (
        execute("select status from analytics.fct_orders where order_id=2")[0][0]
        == "cancelled"
    )
