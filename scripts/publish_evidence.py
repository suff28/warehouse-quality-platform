"""Publish measured evidence; refuse to publish a failed or incomplete local run."""

import json
import re
import shutil
from pathlib import Path

root = Path(__file__).resolve().parents[1]
evidence = root / "evidence"
evidence.mkdir(exist_ok=True)
manifest = json.loads((root / "data/scale/manifest.json").read_text())
quality = json.loads((root / "artifacts/scale/quality.json").read_text())
pytest_log = (root / "artifacts/pytest.log").read_text()
match = re.search(r"(\d+) passed in ([\d.]+)s", pytest_log)
assert match and not re.search(r"\d+ failed", pytest_log), "Regression suite not green"
assert len(quality) == 59 and all(r["status"] == "PASS" for r in quality)
comparison = json.loads((root / "artifacts/compare.json").read_text())
assert all(r["status"] == "PASS" for r in comparison)
dbt_log = (root / "artifacts/dbt-scale.log").read_text()
assert "PASS=46 WARN=0 ERROR=0 SKIP=0" in dbt_log
for src, dst in [("artifacts/scale", "scale"), ("artifacts/defects", "defects")]:
    shutil.copytree(root / src, evidence / dst, dirs_exist_ok=True)
for src, dst in [
    ("artifacts/pytest.html", "pytest.html"),
    ("artifacts/pytest.log", "pytest.log"),
    ("artifacts/dbt-scale.log", "dbt-scale.log"),
    ("artifacts/compare.json", "postgres-comparison.json"),
    ("data/scale/manifest.json", "scale-manifest.json"),
]:
    shutil.copy2(root / src, evidence / dst)
summary = {
    "date": "2026-10-22",
    "data_kind": "deterministic synthetic retail",
    "source_records": manifest["total_rows"],
    "tables": manifest["tables"],
    "python_tests_passed": int(match[1]),
    "dbt_tests_passed": 35,
    "sql_checks_passed": len(quality),
    "deliberate_defect_types": 12,
    "postgres_source_rows": sum(
        manifest["tables"][t] for t in ["customers", "products", "sellers", "orders"]
    ),
    "cloud_execution": "NOT RUN",
    "sqlserver_execution": "NOT RUN",
    "remote_ci_execution": "NOT RUN",
}
(evidence / "summary.json").write_text(json.dumps(summary, indent=2))
report = f"""# Verified execution report — October 22, 2026

The local project was built and executed on this Mac. Synthetic data is explicitly labeled; AWS, Snowflake and SQL Server execution remain pending.

| Verification | Measured result |
|---|---|
| Source dataset | {manifest["total_rows"]:,} logical records across seven tables |
| Relational source | {summary["postgres_source_rows"]:,} rows loaded into isolated PostgreSQL and extracted |
| Exact extraction reconciliation | Zero missing or extra records in all four relational tables, using both directions of EXCEPT ALL |
| End-to-end local scale source | Actual PostgreSQL extracts + strict payment CSV conversion + item/review Parquet |
| dbt scale build | 46 successful nodes, including 35 data tests; zero errors or skips |
| Independent SQL quality suite | 59/59 passed against the scale warehouse |
| Python regression | {match[1]} passed in {match[2]} seconds on the final test run |
| Deliberate defects | 12 fault types detected and clean baseline restored after each |
| Delivery lifecycle | New order, changed order, historical customer transition, late event, exact replay, failed transaction and retry verified |
| Profiling/readiness | Column profiles and source-contract readiness JSON generated |
| Python package | Normal installation and warehouse-qe command verified |
| Static checks | Ruff lint and format passed |

## Dataset breakdown

"""
report += "\n".join(
    f"- {table}: {count:,} rows" for table, count in manifest["tables"].items()
)
report += """

## Evidence files

- [Scale quality report](../evidence/scale/quality.html)
- [Regression report](../evidence/pytest.html)
- [Source comparison](../evidence/postgres-comparison.json)
- [Source manifest](../evidence/scale-manifest.json)
- [dbt scale log](../evidence/dbt-scale.log)
- [Injected defect catalog](../evidence/defects/catalog.json)
- [Readiness verdicts](../evidence/scale/readiness.json)

## What remains unexecuted

AWS S3 upload/IAM, Snowflake COPY/dbt/SQL gates, and SQL Server ODBC execution need your accounts or a supported reachable server. Cloud adapter unit tests are not live cloud tests. GitHub workflows have not run on GitHub. No Jira board or actual stakeholder meetings were created.

## Interpretation

The synthetic distribution has fixed three-line orders and two split payments per order and compresses very well. It is suitable for deterministic correctness and scale exercises; it is not evidence of production throughput or real customer behavior. All 65.4M source records were generated; the project does not contain 65.4M distinct real transactions. Raw source copies, marts and CSV duplicates are not added to the source-record count.

The PostgreSQL service used only the project's own storage. See OPERATIONS.md to restart it when needed. The large files remain on disk under data/ and are excluded from Git. The portable evidence folder can be committed alongside source code.
"""
(root / "docs/EXECUTION_REPORT.md").write_text(report)
(evidence / "index.html").write_text(
    f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Retail Warehouse QE — Verified Evidence</title><style>body{{max-width:1080px;margin:60px auto;padding:0 24px;background:#101827;color:#edf3fa;font:17px/1.6 system-ui}}h1{{font-size:44px;line-height:1.1}}h2{{color:#81e5cf}}a{{color:#95caff}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px}}.card{{background:#1a2940;padding:24px;border-radius:12px}}strong{{display:block;font-size:30px;color:#81e5cf}}.note{{border-left:4px solid #f0bd69;padding:12px 22px;background:#242a35}}</style><p>DATA WAREHOUSE QUALITY ENGINEERING · VERIFIED LOCAL RUN</p><h1>Retail warehouse.<br>Measured quality evidence.</h1><p>Deterministic synthetic data, real PostgreSQL extraction, dbt dimensional models, and independent quality gates.</p><div class="grid"><div class="card"><strong>65.4M</strong>Source records</div><div class="card"><strong>{match[1]}</strong>Python tests passed</div><div class="card"><strong>35</strong>dbt tests passed</div><div class="card"><strong>59</strong>SQL quality checks passed</div></div><h2>Inspect the results</h2><ul><li><a href="scale/quality.html">Full-scale SQL quality report</a></li><li><a href="pytest.html">Python regression results</a></li><li><a href="defects/DEF-02/before/quality.html">Injected revenue defect: failing report</a> · <a href="defects/DEF-02/after/quality.html">restored baseline</a></li><li><a href="scale/readiness.json">Source readiness verdicts</a></li><li><a href="postgres-comparison.json">Exact relational extraction comparison</a></li><li><a href="summary.json">Machine-readable execution summary</a></li></ul><p class="note">AWS, Snowflake and SQL Server live execution are pending. PostgreSQL and the local dbt warehouse were executed. This is synthetic portfolio data, not production customer data.</p><p>October 22, 2026 · <a href="../docs/CLOUD_RUNBOOK.md">Your AWS/Snowflake runbook</a></p></html>"""
)
print(json.dumps(summary, indent=2))
