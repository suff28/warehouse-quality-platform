# Quality engineering test plan

## Scope and layers

1. Source profiling and schema/type readiness.
2. Relational extraction under consistent reads, chunked Parquet delivery, CSV normalization.
3. Snowflake loading and copy-result inspection; the small sample is currently loaded through a Snowflake internal stage. Direct S3 integration is separate and blocked by AWS Academy IAM permissions.
4. dbt dimensions, facts, snapshots and incremental models.
5. Independent SQL reconciliation and Python release gates.
6. Regression and deliberate failure scenarios.

The 65.4-million-record scale run validates warehouse logic locally using dbt-duckdb. The small 65,443-row Snowflake sample has passed seven raw row-count checks, but dbt and independent Snowflake quality/reconciliation are still required for cloud acceptance. None of this establishes Snowflake scale performance, SQL Server connectivity, direct cloud IAM integration, or distributed concurrency behavior.

## Entry criteria

Known data provenance; a completed dataset manifest; exact table grain; a versioned mapping; a dedicated test database; configured credentials for the selected integration tier. Profile allowed nulls separately from contract violations. Cloud budget and integration configuration must exist before executing scale COPY.

## Exit criteria

Every required quality check passes; no query errors; dbt build passes; mutation scenarios are detected; regression tests pass; source-extraction comparisons have zero missing and extra rows; reports include the target environment. Any unexecuted integration remains explicitly marked pending. Never treat a skipped cloud test as a pass.

## Test design

The SQL suite defines failures as returned records. Zero violations is the expected result. A missing column or query failure is an ERROR and a failed gate. Full outer joins detect missing and extra keys; duplicate checks detect cardinality faults independently of values. Source formulas independently recompute target amounts. File SHA-256 verifies delivery identity, while typed relational multiset comparisons verify extracted content; hashes are not a substitute for business validation.

The pytest fixtures build actual dbt models in isolated databases. Mutation tests alter source or target state, assert the named detector fails, then roll back and assert the baseline passes. Lifecycle tests run actual incremental builds and snapshots after each changed batch.

## Risk-based priority

Critical: missing/duplicated facts, monetary errors, key integrity, historical attribution, failed/erroring gates.
High: invalid statuses, invalid chronology, replay behavior, failed-batch recovery.
Medium: optional descriptive data completeness and report usability.

## Defect workflow

New → triaged → in progress → ready for retest → verified → closed. Capture requirement, environment, input batch, observed/expected result, minimal query, impact, severity, and evidence link. Severity represents impact; priority represents scheduling. The included issue-import CSV is a simulation, not an actual Jira board.

## Release and rollback

Keep immutable delivery prefixes. Never publish a new mart to consumers before all mandatory checks pass. The sample cloud loader fails fast and can resume COPY using file-load history, but its multiple table loads are not globally atomic. Consumers must run only after the complete loader and quality pipeline succeeds. For production, promote validated schemas/tables with an explicit deployment mechanism; do not interpret this portfolio's RAW layer as an atomic publication boundary.

## Performance measurements

Record target, row counts, data size, dbt elapsed time, per-check duration, runtime versions and concurrency. Deterministic synthetic data is highly compressible and contains no customer PII; its speed must not be advertised as representative of production workloads. Scale tests are separate from lightweight PR checks.
