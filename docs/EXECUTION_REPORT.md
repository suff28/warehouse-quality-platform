# Verified execution report — October 22, 2026

This portfolio project has passed its local engineering checks and its small Snowflake acceptance run. The large synthetic test ran earlier on this Mac; it did not need to be repeated for cloud acceptance. The Snowflake smoke dataset contains 65,443 rows across seven tables.

## Verified results

| Area | Result | Evidence / limit |
|---|---|---|
| Local scale dataset | 65,434,333 synthetic records across seven tables | Generated test data, not real customer data |
| PostgreSQL extraction | 12,101,000 rows extracted; exact comparison found no missing/extra rows in four relational tables | `evidence/postgres-comparison.json` |
| Local dbt scale build | 46 nodes succeeded, including 35 data tests | `evidence/dbt-scale.log`; DuckDB target only |
| Independent local quality suite | 59/59 checks passed | `evidence/scale/quality.html` |
| Python regression | 97 passed | `evidence/pytest.html` |
| Deliberate defect detection | 12 injected defect types detected | `evidence/defects/catalog.json` |
| AWS S3 upload | Seven small Parquet files and `delivery.json` uploaded to the private project bucket | `evidence/screenshots/aws-s3-sample-upload.png` (redacted proof; seven files, zero failures) |
| Snowflake environment | `RETAIL_QE_WH`, database `RETAIL_QE`, schemas `RAW` and `ANALYTICS`, and internal stage `LOCAL_DELIVERY` created | Snowflake trial in `AWS_CA_CENTRAL_1`; X-Small warehouse configured to auto-suspend after 60 seconds |
| Snowflake raw load | 7/7 Parquet files loaded; all seven row counts matched (65,443 total) | `evidence/screenshots/snowflake-raw-row-counts.png` (redacted public copy) |
| Snowflake dbt build | 46/46 nodes passed: 10 models, 1 snapshot, and 35 data tests | `evidence/snowflake/dbt-run-results.json`; X-Small warehouse, small sample |
| Snowflake independent quality | 59/59 checks passed | `evidence/snowflake/quality.html` and `quality.json` |
| Snowflake exact reconciliation | 7/7 tables passed with zero mismatched rows across 65,443 records | `evidence/snowflake/cloud-reconciliation.json` |

## Operational status

`RETAIL_QE_WH` was suspended after the cloud checks; the Snowsight warehouse page showed it suspended. The public screenshot shows the warehouse status only. Credit balances and billing depend on the account terms; review the cloud provider billing page directly for current charges.

## Blocked or optional work

- Direct AWS S3-to-Snowflake integration is blocked in this AWS Academy account: AWS denied `iam:CreateRole`, so the required Snowflake read role was not created. Do not retry or work around that restriction without the lab administrator. The Snowflake smoke load used an internal stage instead.
- Full 65.4-million-row Snowflake execution has not been run and is not required for the portfolio smoke acceptance. The earlier local scale results do not predict Snowflake credits or performance.
- SQL Server ODBC execution and GitHub Actions execution remain unverified. The GitHub Actions workflows are included but have not been remotely run. SQL Server ODBC execution remains unverified.

## Dataset breakdown

- customers: 2,000,000 rows
- products: 100,000 rows
- sellers: 1,000 rows
- orders: 10,000,000 rows
- order_items: 30,000,000 rows
- payments: 20,000,000 rows
- reviews: 3,333,333 rows

## Evidence files

- [AWS S3 sample upload](../evidence/screenshots/aws-s3-sample-upload.png)
- [Snowflake RAW row-count validation](../evidence/screenshots/snowflake-raw-row-counts.png)
- [Snowflake dbt build pass](../evidence/screenshots/snowflake-dbt-build-pass.png)
- [Suspended Snowflake warehouses](../evidence/screenshots/snowflake-warehouses-suspended.png)

- [Scale quality report](../evidence/scale/quality.html)
- [Regression report](../evidence/pytest.html)
- [Source comparison](../evidence/postgres-comparison.json)
- [Source manifest](../evidence/scale-manifest.json)
- [dbt scale log](../evidence/dbt-scale.log)
- [Injected defect catalog](../evidence/defects/catalog.json)
- [Readiness verdicts](../evidence/scale/readiness.json)
- [Snowflake dbt results](../evidence/snowflake/dbt-run-results.json)
- [Snowflake quality report](../evidence/snowflake/quality.html)
- [Snowflake exact reconciliation](../evidence/snowflake/cloud-reconciliation.json)
- [Screenshot evidence register](../evidence/screenshots/README.md)

The synthetic distribution has fixed three-line orders and two split payments per order and compresses well. It is useful for repeatable correctness and scale testing, not proof of production throughput or real customer behavior. All source-record counts refer to generated logical source rows; raw copies and marts are excluded.
