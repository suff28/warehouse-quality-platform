from pathlib import Path

import duckdb
import pytest
import yaml

from warehouse_qe.quality import profile, run_checks
from warehouse_qe.scenarios import DEFECTS

ROOT = Path(__file__).resolve().parents[1]
CHECKS = yaml.safe_load((ROOT / "config/checks.yml").read_text())["checks"]


@pytest.mark.parametrize("check", CHECKS, ids=lambda c: c["id"] + " " + c["name"])
def test_baseline_contract(db, check):
    assert db.execute(f"select count(*) from ({check['sql']}) q").fetchone()[0] == 0


@pytest.mark.parametrize("name,mutation,expected", DEFECTS, ids=[x[0] for x in DEFECTS])
def test_defects_detected_and_rollback_restores(db, tmp_path, name, mutation, expected):
    db.execute("begin")
    db.execute(mutation)
    results = run_checks(db, ROOT / "config/checks.yml", tmp_path / "before")
    match = next(r for r in results if r["name"] == expected)
    assert match["status"] in ["FAIL", "ERROR"]
    db.execute("rollback")
    fixed = run_checks(db, ROOT / "config/checks.yml", tmp_path / "after")
    assert all(r["status"] == "PASS" for r in fixed)


def test_query_errors_fail_closed(db, tmp_path):
    cfg = tmp_path / "bad.yml"
    cfg.write_text(
        yaml.safe_dump(
            {
                "checks": [
                    dict(
                        id="bad",
                        requirement="REQ-01",
                        name="bad",
                        severity="critical",
                        sql="select * from absent",
                    )
                ]
            }
        )
    )
    assert run_checks(db, cfg, tmp_path / "reports")[0]["status"] == "ERROR"


def test_empty_suite_rejected(db, tmp_path):
    cfg = tmp_path / "empty.yml"
    cfg.write_text("checks: []")
    with pytest.raises(ValueError):
        run_checks(db, cfg, tmp_path)


def test_profile_nulls(db, tmp_path):
    rows = profile(db, ["raw.reviews"], tmp_path / "profile.json")
    text = next(r for r in rows if r["column"] == "review_text")
    assert text["nulls"] > 0 and text["distinct"] == 1


def test_profile_identifier_rejected(db, tmp_path):
    with pytest.raises(ValueError):
        profile(db, ["raw.orders; drop table x"], tmp_path / "profile.json")


def test_invalid_csv_fails_type_conversion(db, tmp_path):
    csv = tmp_path / "bad.csv"
    csv.write_text("order_id,purchased_at\n1,not-a-date\n")
    with pytest.raises(duckdb.ConversionException):
        db.execute(
            f"select * from read_csv('{csv}',columns={{'order_id':'BIGINT','purchased_at':'TIMESTAMP'}},header=true)"
        ).fetchall()


def test_mapping_covers_every_mart_column(db):
    import csv
    from collections import defaultdict

    mapped = defaultdict(set)
    with (ROOT / "docs/source_to_target_mapping.csv").open() as f:
        for row in csv.DictReader(f):
            assert row["target_column"] not in mapped[row["target_table"]]
            mapped[row["target_table"]].add(row["target_column"])
    assert len(mapped) == 8
    for table, columns in mapped.items():
        actual = {
            c[0]
            for c in db.execute(f"select * from analytics.{table} limit 0").description
        }
        assert actual == columns
