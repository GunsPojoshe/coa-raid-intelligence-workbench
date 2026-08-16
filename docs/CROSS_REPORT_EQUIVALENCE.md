# Cross-report difficulty and encounter equivalence

`cross-report-equivalence-review-v1` is the promotion gate between structural cross-report peers and
any later numeric comparison.

It performs **no network requests**. It only reuses existing local persisted report models and immutable
raw Source Observatory captures.

## Difficulty corroboration rule

A report receives a verified private difficulty identity only when all of the following hold:

```text
current persisted report source ID
-> exact /api/reports/{reportId} raw payload
-> /report/difficulty is one stable scalar value

same source report ID
-> exact /api/reports/public raw observation
-> /reports/*/highest_difficulty is one stable scalar value

detail difficulty == public highest_difficulty
```

The scalar value itself stays private. Public review exposes only counts and booleans.

The rule deliberately requires two independently observed source surfaces. A field name by itself is not
used as semantic proof.

## Encounter equivalence rule

An existing `eligible_structural_peer` cohort is promoted to verified encounter equivalence only when:

```text
exact zone
+ exact encounter name
+ exact throughput metric/perspective structural peer
+ corroborated equal difficulty identity across contributing reports
+ encounter name resolves to exactly one source encounter in every contributing report
+ that unique source encounter is the encounter used by the throughput profile
```

This is a source-identity gate. It does not infer boss mechanics.

## Still blocked

Even after this gate passes:

```text
cross-report player identity: false
fight-duration comparison unit: false
numeric cross-report scoring: false
mechanic semantics: false
planner scoring: false
```

The next gate must define a defensible comparison unit and duration handling before any numeric
cross-report performance benchmark is enabled.

## Local scalar-safe review

```powershell
uv run --no-sync python scripts/review_cross_report_equivalence.py `
  --output "$HOME\Desktop\coa-cross-report-equivalence-real.json"
```

The output contains no report/encounter/player IDs or names, no zone/difficulty values, no raw payloads
or paths, and no private hashes.
