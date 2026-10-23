# Operations and troubleshooting

## PostgreSQL verification environment on this Mac

The project-created cluster is `data/postgres-local`, port 55432, listening only on localhost. It is separate from any existing user database. Databases: `postgres` (small test) and `retail_scale` (large test). It uses trust authentication solely for an isolated local portfolio verification run and should remain stopped when unused. Do not expose it to a network.

Start when needed:

```bash
/Applications/Postgres.app/Contents/Versions/latest/bin/pg_ctl \
  -D data/postgres-local -l artifacts/postgres-server.log \
  -o '-p 55432 -h 127.0.0.1 -k /tmp' start
```

Stop:

```bash
/Applications/Postgres.app/Contents/Versions/latest/bin/pg_ctl -D data/postgres-local stop
```

Connection used for scale verification: `postgresql://retail@127.0.0.1:55432/retail_scale`. This contains no password. For your own remote database, require normal authentication/TLS and configure POSTGRES_DSN locally.

## Failures and recovery

- Dataset already exists: choose a new output folder. Do not mix fragments from different generation runs.
- DuckDB database locked: close other writers, including dbt. Parallel tests use isolated databases; don't run two builds against the same file.
- Missing source file: compare delivery manifest, file names and checksums. Restore the immutable delivery before building.
- S3 prefix not empty: select a new run prefix. The uploader intentionally rejects reuse.
- Missing staged delivery marker or Parquet file: finish the upload before COPY. The loader verifies file presence, while the uploader verifies bytes and SHA metadata.
- Snowflake COPY fails: inspect recorded query/error details; fix the file/schema/IAM cause, retry the same delivery, and do not run downstream models before a successful load.
- dbt test failure: inspect compiled SQL and failing records; correct source/mapping/model rather than disabling the test.
- ODBC missing: install Microsoft's Driver 18 and its supported driver manager on the host used for SQL Server. Python pyodbc alone is not the driver.

## Reproducibility

requirements.lock.txt records the environment used on the verification machine. `pyproject.toml` defines installable dependencies; cross-platform wheel availability may vary. Tests build isolated fixtures and do not require cloud secrets. Large files are excluded from Git. Keep a manifest and verified report snapshot instead of committing database binaries.
