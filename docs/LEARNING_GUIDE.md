# Learn the project well enough to defend it in an interview

Do not memorize a list of tools. Follow one order through every layer and explain why each check exists.

1. Read REQUIREMENTS.md. Explain grain, payment fan-out and the difference between net merchandise sales and paid amount.
2. Run `make smoke`. Open the quality report and locate the SQL behind a passing check in config/checks.yml.
3. Open `dbt/models/marts/fct_order_items.sql`. Explain the temporal customer join and why missing history is a failure.
4. Run `make defects`. Compare DEF-02 before and after. Explain why row counts alone cannot establish monetary accuracy.
5. Read tests/test_incremental.py. Explain business time versus arrival time, inclusive replay and why customer updates need monotonic timestamps.
6. Inspect the profiling report. Explain why nullable review text is allowed but null order IDs are not.
7. Trace cloud.py's extraction and delivery.py's strict CSV conversion. Explain why 50,000-row batches avoid loading the entire source into Python memory.
8. Execute the AWS/Snowflake runbook when your account is ready. Save real query IDs and reports. Learn the SQL Server path separately from PostgreSQL.
9. Review the test-plan entry/exit criteria. Give a two-minute QE status report stating executed coverage, open blockers and release risk.

## Questions you should be able to answer

- How do you find records missing from either side of a mapping?
- How can equal row counts conceal bad data?
- Why does joining two one-to-many datasets overstate revenue?
- Why use DECIMAL rather than FLOAT for money?
- How does a Type 2 customer dimension preserve historical meaning?
- What happens if a record arrives today with last year's purchase date?
- How do you prove replay is idempotent beyond just matching counts?
- What does a query error mean in the quality gate?
- What did you actually run in Snowflake versus locally?
- What remains untested, and how would you test it in a real team?

## Honest resume wording

After the local evidence is verified: "Built a retail warehouse QE portfolio with 65.4 million synthetic records, dbt dimensional models, 59 SQL data-quality gates and Python regression tests covering deliberate defects, historical dimensions and incremental replay."

Add PostgreSQL extraction numbers only from the execution report. Add AWS/Snowflake execution only after your own cloud acceptance run. Do not claim this was employment, real customer data, or a production deployment. Use measured test counts from the current report rather than copying stale examples.
