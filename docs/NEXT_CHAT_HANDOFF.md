# Next chat handoff — 2026-08-27

Authoritative detailed state:

```text
docs/CURRENT_PARADIGM.md
docs/PROJECT_STATE.md
docs/CONTINUATION_PROMPT.md
```

## Resume

```text
repo: GunsPojoshe/coa-raid-intelligence-workbench
canonical active branch: e4/interactive-har-discovery
Draft PR #9 -> e3/real-log-capture
```

Perform live GitHub HEAD/PR/CI checks first.

## Current paradigm

```text
official public API first
-> official semantics
-> pinned Companion source
-> persisted first-party evidence
-> browser/HAR only for exact gaps
-> inference last
```

## Aggregate API proof complete

```text
3 phases / 1 active-current candidate
285 bosses / 285 unique stable boss_id
provenance-aware /statistics: HTTP 200, archived, 21306 bytes
21 normalized classes
62 normalized specs
806 percentile values
first persistence inserted 21/62
second persistence matched 21/62 with zero inserts
idempotent = true
62 population-prior records
62 records with local_parse_share
Source Observatory integrated = true
source_endpoint_profile dependency = registered
legacy broad source_endpoint dependency = inactive
pending reanalysis = 0
actionable source changes = 0
health attention_required = false
planner scoring = false
site Tier List algorithm = unverified
```

Real receipts:

```text
evidence/real-data/coa-public-api-statistics-provenance-capture-real.json
evidence/real-data/coa-public-api-statistics-persistence-real.json
evidence/real-data/coa-public-api-statistics-profile-reanalysis-real.json
```

Do not repeat those real proofs.

## Current gate — bounded multi-profile population coverage

Implementation:

```text
src/coa_workbench/analytics/public_api_population_coverage.py
scripts/capture_public_api_population_coverage.py
```

Coverage v1:

```text
4 required slices
3 documented metric families
3 role-qualified slices
1 role-omitted slice
boss/location/week/realm/class/spec expansion excluded
bulk mode false
```

The command checks DuckDB first and only calls the API for missing slices. It stops on the first incomplete response and is safe to rerun because completed matching profiles are reused.

Operator command:

```powershell
uv run --no-sync python scripts/capture_public_api_population_coverage.py
```

Review only:

```text
data/exchange/out/coa-public-api-population-coverage-review.json
```

Do not request RawArchive, DuckDB, API key, private query values or profile fingerprints.

Expected success shape:

```text
coverage_after.complete = true
missing_slice_count = 0
legacy unscoped dependency count = 0
pending reanalysis = 0
actionable source changes = 0
attention_required = false
planner_scoring_allowed = false
```

## Profile reanalysis semantics

Profile-local schema changes target only matching private query profiles. `request_contract_changed` is endpoint-global. Events older than dependency registration do not back-trigger newer aggregate artifacts.

The real migration replay already proved the historical baseline event did not create a reanalysis request.

## Retained blockers

```text
historical two-report difficulty equivalence: insufficient_evidence
numeric historical cross-report scoring: blocked
cross-report player identity: unproven
fight-duration comparison semantics: unproven
site Tier List algorithm: undocumented
planner scoring: blocked
```

## Local audit

Already complete. Preserve the historical helper patch privately; it is incomplete due missing `guild_progression_js_lexical` and must not be applied as-is. Do not re-request the same inventory/patch unless the workspace materially changes.

## Branch chain

```text
main <- e2 (#3) <- e3 (#7) <- e4 (#9)
```

Resolve lower-chain integration debt deliberately and preserve the newest canonical documentation.
