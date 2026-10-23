# Deliberate defects and remediation

These are controlled faults injected into isolated test databases. They are not discovered production incidents. The automated before/after demonstration rolls back the injected transaction; a real code fix would follow the remediation below and be retested with the same detector.

| ID | Fault | Expected detector | Remediation to review |
|---|---|---|---|
| DEF-01 | Duplicate order source | Source grain uniqueness | Reject duplicate delivery keys or define explicit CDC ordering; do not silently lose conflicts. |
| DEF-02 | Revenue multiplied by fan-out | Daily net reconciliation | Preaggregate split payments; join at a compatible grain. |
| DEF-03 | Removed amount column | Query ERROR, gate fails | Restore schema contract or version mappings and consumer models together. |
| DEF-04 | One-cent amount corruption | Independent line recomputation | Use fixed decimal expression and declared rounding rule. |
| DEF-05 | Missing parent customer | Order/customer anti-join | Restore parent delivery or quarantine dependent orders. |
| DEF-06 | Overlapping history | SCD interval test | Repair interval boundaries and current-row flags; retest as-of attribution. |
| DEF-07 | Replayed target duplicates | Incremental fact grain | Use stable unique key and replacement/merge semantics. |
| DEF-08 | Delivery before purchase | Chronology test | Correct parsing/time normalization or quarantine invalid input. |
| DEF-09 | Negative quantity | Positive quantity test | Reject invalid transactions; model returns separately if required. |
| DEF-10 | Missing fact line | Source count and full join | Investigate rejected loads or lossy inner joins; replay corrected batch. |
| DEF-11 | Missing historical customer key | Required temporal key | Deliver valid history or apply an explicit unknown-member policy. |
| DEF-12 | Unrecognized status | Accepted-domain test | Correct source mapping and document the accepted status dictionary. |

A separate negative test loads a malformed CSV timestamp and asserts a typed-load exception. This checks parse failure, whereas DEF-08 checks a syntactically valid but semantically impossible date relationship.
