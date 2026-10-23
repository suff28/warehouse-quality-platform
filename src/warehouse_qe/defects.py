"""Publish reproducible failing and restored reports without modifying the baseline."""

import json
import shutil
from pathlib import Path

import duckdb

from .quality import run_checks
from .scenarios import DEFECTS


def main():
    root = Path.cwd()
    target = root / "artifacts/defects"
    target.mkdir(parents=True, exist_ok=True)
    database = target / "demo.duckdb"
    shutil.copy2(root / "data/warehouse.duckdb", database)
    catalog = []
    with duckdb.connect(str(database)) as con:
        for table in ["orders", "customers", "order_items"]:
            con.execute(f"create table raw.{table}_copy as select * from raw.{table}")
            con.execute(f"drop view raw.{table}")
            con.execute(f"alter table raw.{table}_copy rename to {table}")
        for i, (name, mutation, expected) in enumerate(DEFECTS, 1):
            con.execute("begin")
            con.execute(mutation)
            bad = run_checks(
                con, root / "config/checks.yml", target / f"DEF-{i:02}/before"
            )
            con.execute("rollback")
            good = run_checks(
                con, root / "config/checks.yml", target / f"DEF-{i:02}/after"
            )
            caught = any(r["name"] == expected and r["status"] != "PASS" for r in bad)
            restored = all(r["status"] == "PASS" for r in good)
            assert caught and restored, name
            catalog.append(
                dict(
                    id=f"DEF-{i:02}",
                    name=name,
                    mutation=mutation,
                    expected_detector=expected,
                    detected=caught,
                    restored=restored,
                    resolution="Rollback injected transaction; production remediation described in docs/DEFECT_CATALOG.md",
                )
            )
    database.unlink()
    (target / "catalog.json").write_text(json.dumps(catalog, indent=2))
    print(f"{len(catalog)} defects detected; clean baseline restored after each")


if __name__ == "__main__":
    main()
