# Simulated Agile delivery and QE communication

This is a self-directed portfolio backlog. No team meetings or stakeholder signoffs are claimed.

| Sprint | Story | Acceptance criteria |
|---|---|---|
| 1 | As a QE, I can profile delivered sources and assess readiness. | Typed source contracts, profile report, invalid-input rejection. |
| 1 | As a developer, I can reproduce large datasets without real customer data. | Deterministic generation, manifest, bounded-memory chunks. |
| 2 | As a business user, I can trust daily sales totals. | Defined amount rules, star schema, independent reconciliation. |
| 2 | As an analyst, I can see customer history at purchase time. | Snapshot intervals, historical attribution tests. |
| 3 | As a QE, I can rerun automated regression after a change. | One-command pytest, dbt gates, failing exit codes and reports. |
| 3 | As operations, I can recover a failed delivery and replay arrivals. | Late-arrival, rollback, retry and exact replay comparison. |
| 4 | As a reviewer, I can inspect cloud-specific evidence. | Small sample loaded to Snowflake RAW with all seven counts passing; dbt and independent cloud quality suite remain to run. |

## Example standup update

Completed: local large-data build, automated reconciliation, mutation coverage, private S3 upload, and seven-table Snowflake RAW load/count checks on the small sample. Blocked: AWS Academy denies `iam:CreateRole`, so direct S3 integration requires lab-admin help. Next: run dbt and independent quality/reconciliation on the small Snowflake sample; SQL Server remains a separate optional integration requiring a reachable supported runtime.

## Sprint review template

Environment and commit:
Data volume and provenance:
Requirements covered:
Tests executed / passed / failed / not run:
Open defects by severity:
Evidence links:
Remaining release risk:
Next action and owner:

Use docs/backlog.csv to import issues into your own tracker or maintain them as a GitHub project. Importing into Jira is optional; do not interpret the CSV as an already created Jira board.
