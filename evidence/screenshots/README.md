# Public screenshot evidence

These four images are cropped or redacted copies prepared for the public repository. Raw originals stay under the ignored `data/screenshot-originals/` directory and are never published.

- `aws-s3-sample-upload.png` — seven Parquet files uploaded successfully to a private S3 bucket; the bucket name and account chrome are redacted.
- `snowflake-raw-row-counts.png` — seven Snowflake RAW row-count checks passed for the 65,443-row smoke sample.
- `snowflake-dbt-build-pass.png` — Snowflake dbt build completed with 46/46 nodes passing.
- `snowflake-warehouses-suspended.png` — warehouse list showed the listed warehouses suspended after validation.

The S3 screenshot demonstrates object upload only. The AWS Academy account denied `iam:CreateRole`, so direct S3-to-Snowflake integration was not available. The Snowflake sample used an internal stage.
