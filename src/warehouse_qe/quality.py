"""SQL-driven quality gates; queries return violating records, never success flags."""

import html
import json
import re
import time
from pathlib import Path

import yaml


def run_checks(connection, config: Path, output: Path):
    checks = yaml.safe_load(config.read_text())["checks"]
    if not checks:
        raise ValueError("Empty quality suite is not a valid pass")
    results = []
    for check in checks:
        start = time.perf_counter()
        result = {k: check[k] for k in ("id", "requirement", "name", "severity")}
        try:
            sql = check["sql"].strip().rstrip(";")
            count = connection.execute(
                f"select count(*) from ({sql}) failures"
            ).fetchone()[0]
            sample = (
                connection.execute(
                    f"select * from ({sql}) failures limit 10"
                ).fetchall()
                if count
                else []
            )
            result.update(
                status="FAIL" if count else "PASS", failed_rows=count, sample=sample
            )
        except Exception as exc:
            result.update(status="ERROR", failed_rows=None, sample=[], error=str(exc))
        result["seconds"] = round(time.perf_counter() - start, 3)
        results.append(result)
    output.mkdir(parents=True, exist_ok=True)
    (output / "quality.json").write_text(json.dumps(results, indent=2, default=str))
    rows = "".join(
        "<tr>"
        + "".join(
            f"<td>{html.escape(str(r.get(k, '')))}</td>"
            for k in [
                "id",
                "requirement",
                "name",
                "status",
                "failed_rows",
                "seconds",
                "sample",
                "error",
            ]
        )
        + "</tr>"
        for r in results
    )
    (output / "quality.html").write_text(
        """<!doctype html><html lang="en"><meta charset="utf-8"><title>Retail warehouse quality evidence</title><style>body{font:15px system-ui;background:#0c1425;color:#e6edf8;margin:32px}table{border-collapse:collapse;width:100%}td,th{border:1px solid #38455d;padding:10px;text-align:left}h1{color:#72dacb}td{max-width:450px;overflow-wrap:anywhere}</style><h1>Warehouse quality evidence</h1><p>Expected result: zero violating records for every check. Errors fail the gate. Samples are capped at ten rows.</p><table><tr><th>ID</th><th>Requirement</th><th>Check</th><th>Status</th><th>Violations</th><th>Seconds</th><th>Sample</th><th>Error</th></tr>"""
        + rows
        + "</table></html>"
    )
    readiness = {}
    for check, result in zip(checks, results):
        if "analytics." not in check["sql"]:
            for table in set(re.findall(r"raw\.([a-z_]+)", check["sql"])):
                entry = readiness.setdefault(
                    table, {"status": "READY", "checks": [], "failed_checks": []}
                )
                entry["checks"].append(result["id"])
                if result["status"] != "PASS":
                    entry["status"] = "NOT_READY"
                    entry["failed_checks"].append(result["id"])
    (output / "readiness.json").write_text(
        json.dumps(
            {
                "basis": "Declared source contracts only; optional nulls are profiled separately",
                "sources": readiness,
            },
            indent=2,
        )
    )
    return results


def profile(connection, tables, output: Path):
    import re

    report = []
    for table in tables:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*\.[A-Za-z_][A-Za-z_0-9]*", table):
            raise ValueError("Invalid table identifier")
        cursor = connection.execute(f"select * from {table} limit 0")
        columns = [c[0] for c in cursor.description]
        for col in columns:
            name = '"' + col.replace('"', '""') + '"'
            row = connection.execute(
                f"select count(*),count({name}),count(distinct {name}),min({name}),max({name}) from {table}"
            ).fetchone()
            report.append(
                dict(
                    table=table,
                    column=col,
                    rows=row[0],
                    nulls=row[0] - row[1],
                    null_pct=round(100 * (row[0] - row[1]) / max(row[0], 1), 4),
                    distinct=row[2],
                    minimum=row[3],
                    maximum=row[4],
                )
            )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "readiness": "Requires contract checks; profiling alone does not certify readiness",
                "columns": report,
            },
            indent=2,
            default=str,
        )
    )
    return report
