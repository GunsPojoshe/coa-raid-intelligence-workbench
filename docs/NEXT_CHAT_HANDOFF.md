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
analysis_run registered
raw dependency registered
planner scoring = false
site Tier List algorithm = unverified
```

Real receipts:

```text
evidence/real-data/coa-public-api-statistics-provenance-capture-real.json
evidence/real-data/coa-public-api-statistics-persistence-real.json
```

Do not repeat that real capture/persistence proof.

## Current gate

```text
existing RawArchive statistics response
-> Source Observatory replay
-> request-scope schema profile
-> source capture/schema/acquisition registration
-> source_endpoint=public_api_statistics dependency
-> scalar-safe Source & Analysis Health
```

No network call is needed for this gate. After the implementation is on canonical E4, the only local operator command is:

```powershell
uv run --no-sync python scripts/persist_public_api_statistics.py
```

Review only:

```text
data/exchange/out/coa-public-api-statistics-persistence-review.json
```

Do not request RawArchive, DuckDB, API key or private query values.

## Important health detail

The first endpoint observation can create one informational open `endpoint_added` event. Dedicated aggregate health does not treat this baseline info event as actionable. Warning/error changes or pending reanalysis do require attention.

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
