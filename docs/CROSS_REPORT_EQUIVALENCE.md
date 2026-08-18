# Cross-report difficulty and encounter equivalence

`cross-report-equivalence-review-v1` is the promotion gate between structural cross-report peers and
any later numeric comparison.

It performs **no network requests**. It only reuses existing local persisted report models and immutable
raw Source Observatory captures.

## Difficulty corroboration rule v1

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

## Real two-report result

The first real review over the two persisted reports returned:

```text
status: insufficient_evidence
reports: 2

report-detail difficulty observed: 0
public highest difficulty observed: 0
cross-surface matches:             0
cross-surface mismatches:          0
ambiguous reports:                 0
verified reports:                  0

eligible structural cohorts:       3
difficulty-verified cohorts:       0
encounter-equivalence cohorts:     0
encounter non-unique cohorts:      0
```

This means the v1 corroboration surfaces did not provide usable scalar difficulty evidence for these two
reports. It does **not** prove that the reports have different difficulties.

The structural encounter-name gate did not fail: all three current structural peer cohorts remain free of
an encounter-name uniqueness conflict.

Public-safe receipt:

```text
evidence/real-data/coa-cross-report-equivalence-real.json
```

## Existing structural clue that is not yet promoted

An earlier private current-report structural review observed:

```text
encounter-catalog top-level field: reportDifficulty
encounter-row field:               difficulty
```

These field names are evidence candidates, not semantic truth. The current equivalence reviewer does not
promote them automatically.

## Scalar-safe source-structure probe

After the real `insufficient_evidence` result, `cross-report-source-structure-v1` was added:

```text
src/coa_workbench/analytics/cross_report_source_structure.py
scripts/review_cross_report_source_structure.py
tests/unit/test_cross_report_source_structure.py
```

It reads the already persisted local corpus and emits only fixed field names and JSON types for:

```text
matching report-detail report objects
encounter catalog row observations
public report rows
```

It excludes report/encounter IDs, report titles, encounter names, difficulty scalar values, raw
payloads/paths and private hashes.

The real source-structure result is still pending at the current handoff snapshot. No new HAR is needed.

Important limitation of v1: it inspects encounter **row** structures but not the encounter-catalog
response top-level structure. If row-level evidence is insufficient, extend the probe to include that
top-level shape so `reportDifficulty` can be evaluated structurally before requesting any new source
capture.

## Next difficulty decision tree

Use the real source-structure result to choose the evidence path:

1. If two independently bound existing surfaces expose one stable scalar difficulty value for each report
   and agree exactly, implement a revised corroboration rule and prove it synthetic + real.
2. If encounter-row `difficulty` exists, first prove it is stable/consistent within the report and obtain an
   independent report-level corroborator such as the already observed top-level `reportDifficulty` before
   promoting equivalence.
3. If persisted evidence truly has no independent corroborator, request only the smallest new Network
   observation that binds explicit report identity to an explicit difficulty field. Do not repeat a full
   current-report HAR merely to re-prove transport or persistence.

## Still blocked after difficulty alone

Even after difficulty + encounter identity pass, these remain separate gates:

```text
cross-report player identity: false
fight-duration comparison unit: false
numeric cross-report scoring: false
mechanic semantics: false
planner scoring: false
```

The next gate must define a defensible comparison unit and duration handling before any numeric
cross-report performance benchmark is enabled. Candidate existing timing evidence includes exact
encounter timing/duration observations and throughput `duration_ms`; units and exact encounter linkage
must be corroborated before deriving rates.

## Local scalar-safe reviews

Difficulty/encounter equivalence:

```powershell
uv run --no-sync python scripts/review_cross_report_equivalence.py `
  --output "$HOME\Desktop\coa-cross-report-equivalence-real.json"
```

Source-structure probe:

```powershell
uv run --no-sync python scripts/review_cross_report_source_structure.py `
  --output "$HOME\Desktop\coa-cross-report-source-structure-real.json"
```

Both outputs are designed to avoid private scalar identities. For the exact project restart point and
full next-step context, read `docs/NEXT_CHAT_HANDOFF.md`.
