# Business requirements and acceptance criteria

This is a portfolio simulation of stakeholder requirements, not evidence of employment or stakeholder meetings.

The retailer needs a trustworthy daily sales mart. Finance must reconcile net merchandise sales by purchase date. Operations needs current order state and reliable delivery chronology. Customer analysis must attribute purchases to the customer address that was valid at purchase time. QE blocks release when critical data contracts fail.

| ID | Requirement | Acceptance evidence |
|---|---|---|
| REQ-01 | Every source obeys its declared grain and required identifiers. | Source uniqueness and null checks; 7 tables. |
| REQ-02 | Orders, lines, reviews and payments reference valid parent records. | Six anti-join checks, with failing row samples. |
| REQ-03 | Each dimension/fact preserves its declared grain. | Eight mart grain checks and required keys; dbt tests. |
| REQ-04 | Source-to-target completeness and values reconcile independently. | Full outer joins, counts and independent daily revenue calculations. |
| REQ-05 | Customer history has exactly one current version and nonoverlapping intervals. | Snapshot, interval tests, temporal attribution, lifecycle integration test. |
| REQ-06 | Business values are valid and totals follow specified monetary rules. | Twelve domain checks; fixed decimals and order-payment tolerance. |
| REQ-07 | Arrival batches support updates, late business events and replay. | Five-batch real dbt integration test. |
| REQ-08 | Failed ingestion can be retried without partial transactional changes. | Deliberate transaction failure, rollback and retry test. |
| REQ-09 | QE reports identify failed checks, expected outcomes and sample records. | JSON/HTML reports, exceptions fail closed, defect before/after evidence. |
| REQ-10 | SQL Server/PostgreSQL, files and S3 have explicit ingestion paths. | Adapters, source schema, CSV normalization, delivery manifest, cloud runbook. |
| REQ-11 | Assess source readiness and preserve delivery audit data. | Profiling, schema checks, manifest hashes, extraction reconciliation. |
| REQ-12 | Repeatable CI and QE communications support change control. | GitHub workflows, traceability, sprint plan, release status template. |

## Business definitions

- Order item grain: `(order_id,line_id)`. Three lines per order in this synthetic benchmark; this is not an inferred universal retail constraint.
- Payment source grain: `(order_id,payment_sequence)`. Two split payments per synthetic order. Never join raw payments to raw lines to calculate revenue.
- Net merchandise amount = `quantity * unit_price - discount_amount`, fixed decimal scale 2. Freight is separate. All data uses a single currency, BRL; no foreign exchange conversion is claimed.
- Revenue excludes cancelled orders. Payment reconciliation includes all generated orders because generated cancelled orders retain a payment record; this project does not model refunds or revenue recognition under accounting standards.
- Split payment rounding tolerance: at most BRL 0.01 per order. Merchandise and daily revenue comparisons have zero tolerance.
- Customer history intervals are `[valid_from,valid_to)`; a null end means current. Missing historical customer keys fail the gate, rather than silently using the current address.
- `batch_id` is a monotonically increasing arrival sequence, independent of business dates. Updated/late records MUST receive a new arrival ID. Hard deletes and out-of-order batch-ID reuse are out of scope.
- Source `updated_at` is authoritative and monotonically increasing per customer. Backdated corrections require a controlled full history repair; dbt timestamp snapshots do not solve arbitrary CDC reconstruction.
- Missing review text is allowed; missing identifiers are not. A profile finding is not automatically a defect.
