import os
import subprocess
from pathlib import Path

import duckdb
import pytest

from warehouse_qe.generate import bootstrap, generate

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def baseline(tmp_path_factory):
    folder = tmp_path_factory.mktemp("warehouse")
    generate(folder / "source", 1000, 500)
    database = folder / "warehouse.duckdb"
    bootstrap(folder / "source", database)
    with duckdb.connect(str(database)) as con:
        from warehouse_qe.generate import TABLES

        for table in TABLES:
            con.execute(
                f"create table raw.{table}_materialized as select * from raw.{table}"
            )
            con.execute(f"drop view raw.{table}")
            con.execute(f"alter table raw.{table}_materialized rename to {table}")
    env = {
        **os.environ,
        "WAREHOUSE_DB": str(database),
        "DBT_SEND_ANONYMOUS_USAGE_STATS": "false",
    }
    result = subprocess.run(
        [
            str(ROOT / ".venv/bin/dbt"),
            "build",
            "--project-dir",
            str(ROOT / "dbt"),
            "--profiles-dir",
            str(ROOT / "dbt"),
            "--target-path",
            str(folder / "target"),
            "--log-path",
            str(folder / "logs"),
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return database


@pytest.fixture
def db(baseline, tmp_path):
    import shutil

    database = tmp_path / "test.duckdb"
    shutil.copy2(baseline, database)
    with duckdb.connect(str(database)) as con:
        yield con
