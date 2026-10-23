# AWS and Snowflake project runbook

This runbook records the actual path used for this project. The seven small Parquet files were uploaded to the private AWS bucket and separately uploaded to Snowflake's internal stage. The Snowflake RAW load, dbt build, independent checks, and exact reconciliation are complete for the 65,443-row sample. **Do not repeat those uploads or rerun the 65-million-row local scale workload.**

## Current cloud state

- AWS region: us-east-1. Project bucket: private (name intentionally omitted from public docs). Uploaded under `retail-qe/run-001/`.
- Snowflake region: AWS Canada Central. Warehouse `RETAIL_QE_WH` is X-Small with 60-second auto-suspend. Database `RETAIL_QE`; schemas `RAW` and `ANALYTICS`; internal stage `RAW.LOCAL_DELIVERY`.
- Seven Snowflake RAW tables passed expected row counts: customers 2,000; orders 10,000; products 100; sellers 10; order_items 30,000; payments 20,000; reviews 3,333.
- The AWS Academy policy denied `iam:CreateRole`. Therefore direct S3-to-Snowflake integration is unavailable unless the lab administrator provisions the read role. The internal-stage load avoids that IAM requirement.

## Reproduce the completed Snowflake smoke acceptance (optional)

The project already has `.venv`, `dbt-core`, `dbt-snowflake`, and `snowflake-connector-python`. The Mac runs the small client/SQL orchestration only; the 65,443 rows are processed by the Snowflake X-Small warehouse. Do not paste credentials into chat.

This environment also includes the optional `dbt-state` plugin, which can open a separate dbt Cloud sign-in page. This project does not use dbt Cloud, so disable the optional plugin with `RUN_CACHE_DISABLED=true`. This does not disable dbt or the Snowflake adapter.

### 1. Read the Snowflake connection identifiers

In Snowsight, open a worksheet and run:

```sql
SELECT CURRENT_ACCOUNT(), CURRENT_REGION(), CURRENT_USER(), CURRENT_ROLE();
```

Use the returned account identifier and user name in the next step. The account identifier is not necessarily the full browser URL. Current role should be `ACCOUNTADMIN` in the user's trial account; do not grant additional roles just for this smoke run.

### 2. Run dbt against the small Snowflake tables

Open Terminal and run these commands, replacing only the two quoted placeholders with the values from the query. They set environment variables for this Terminal session only; they do not write a password to the project.

```bash
cd warehouse-quality-platform
source .venv/bin/activate
export DBT_TARGET=snowflake
unset DBT_ENGINE_MANAGE_STATE
export RUN_CACHE_DISABLED=true
export SNOWFLAKE_ACCOUNT='PASTE_CURRENT_ACCOUNT_HERE'
export SNOWFLAKE_USER='PASTE_CURRENT_USER_HERE'
export SNOWFLAKE_ROLE=ACCOUNTADMIN
export SNOWFLAKE_AUTHENTICATOR=snowflake
export SNOWFLAKE_DATABASE=RETAIL_QE
export SNOWFLAKE_WAREHOUSE=RETAIL_QE_WH
read -s 'SNOWFLAKE_PASSWORD?Enter your Snowflake password (input will be hidden): '
export SNOWFLAKE_PASSWORD
echo
dbt debug --project-dir dbt --profiles-dir dbt --target snowflake
dbt build --project-dir dbt --profiles-dir dbt --target snowflake
```

Enter the Snowflake user's password only at the hidden Terminal prompt; do not paste it into chat or commit it. `dbt debug` should report `All checks passed!` before building. dbt will create the staging views, mart tables and customer-history snapshot in `ANALYTICS`, then run the configured tests. The project uses tiny sample tables here; do not switch to the scale dataset.

If dbt reports that it cannot create objects in `ANALYTICS`, stop. Do not broaden grants or retry using a different account; send the exact error so we can diagnose the Snowflake account role/schema safely. If authentication fails, verify the account/user values and browser login without sharing passwords.

### 3. Run independent cloud quality and exact reconciliation

Only after `dbt build` succeeds, use the same Terminal session:

```bash
PYTHONPATH=src python -m warehouse_qe.cloud check
PYTHONPATH=src python -m warehouse_qe.cloud reconcile --data data/delivery
```

These create `artifacts/snowflake/quality.json`, `quality.html`, and `artifacts/cloud-reconciliation.json`. The reconciliation is against the small delivery only. Expected outcome: 59 quality checks pass and each of seven tables has zero mismatches. Capture the summaries/query IDs for the execution report; do not post account IDs or credentials publicly.

### 4. Suspend Snowflake compute

When checks are done, switch back to Snowsight and run:

```sql
ALTER WAREHOUSE RETAIL_QE_WH SUSPEND;
```

Auto-suspend is already configured, but suspend it explicitly after the run. Credits and billing depend on the actual account terms; a trial credit balance is not a promise that charges cannot occur. Check the Snowflake usage page and AWS Billing & Cost Management. The tiny S3 files can stay in the private bucket for the portfolio.

### 5. Record results and prepare portfolio evidence

Update `docs/EXECUTION_REPORT.md` only with measured dbt/check/reconciliation results. Selected redacted screenshots are already under `evidence/screenshots/`. Keep `data/screenshot-originals/` private; the originals contain account/user and browser information. Do not publish the `data/` directory, `.env`, credentials, or generated scale files.

## AWS direct-integration route (blocked by lab permissions)

Do not retry IAM role creation. AWS denied `iam:CreateRole`, so this route requires your AWS Academy/lab administrator to provision a tightly scoped read role. If they authorize it, use the placeholders in `infra/snowflake_setup.sql` and the [Snowflake S3 storage integration instructions](https://docs.snowflake.com/en/user-guide/data-load-s3-config-storage-integration). Do not change bucket permissions to public and do not use broad administrator policies.

## Not required for this smoke milestone

- Re-running local scale data generation, DuckDB, PostgreSQL, or the 97-test regression suite.
- Loading the 65-million-row dataset into Snowflake. Local scale results do not predict cloud performance or credit usage.
- Creating an AWS IAM role yourself in this restricted lab.

SQL Server ODBC execution and GitHub Actions remain separate optional milestones unless the course rubric explicitly requires them.
