# Continuation prompt — current project state

Updated: **2026-08-27**.

## Repository

```text
GunsPojoshe/coa-raid-intelligence-workbench
local: C:\Users\Simpa\source\repos\coa-raid-intelligence-workbench
active canonical workstream: e4/interactive-har-discovery
Draft PR #9 -> e3/real-log-capture
```

Perform live GitHub HEAD/PR/CI checks first. Stored SHAs/run numbers are checkpoints only.

## Read in order

```text
AGENTS.md
docs/DOCUMENTATION_INDEX.md
docs/CURRENT_PARADIGM.md
docs/COA_DOMAIN_BOUNDARY.md
docs/COA_TARGET_PRODUCT_DEFINITION.md
docs/PROJECT_MASTER_CONTEXT.md
docs/PROJECT_STATE.md
docs/OFFICIAL_PUBLIC_API.md
docs/SOURCE_OBSERVABILITY_AND_REANALYSIS.md
docs/UPSTREAM_ASCENSION_LOGS_EVIDENCE.md
docs/LOCAL_WORKSPACE_BOUNDARY.md
docs/CI_OPERATIONS.md
docs/WINDOWS_DEVELOPMENT_ENVIRONMENT.md
```

Historical handoffs/experiments do not override this order.

## Product question

> **Почему конкретный человек нужен именно текущему составу?**

Maintain fail-closed semantics: observation/field/UI label/population metric is not automatic mechanic or planner proof.

## Source order

```text
official documented public API
official documented site semantics
pinned executable Companion source
persisted first-party report/API evidence
narrow browser/network fallback
structural inference last
```

## Official aggregate API — completed real gates

The first aggregate vertical slice and its source-health/dependency layer are real-proven:

```text
/phases + /bosses: archived/reviewed
provenance-aware /statistics: HTTP 200, archived
request context complete: true
exact normalization: 21 classes / 62 specs / 806 percentile values
first persistence: 21 class + 62 spec rows inserted
second persistence: 21 class + 62 spec rows matched, zero inserts
idempotent: true
population-prior records: 62
records with local_parse_share: 62
Source Observatory integrated: true
raw dependency registered: true
source_endpoint_profile dependency registered: true
legacy broad source_endpoint dependency active: false
profile dependency count: 1
old eligible events after dependency registration: 0
created reanalysis requests: 0
pending reanalysis: 0
actionable open source changes: 0
source health attention required: false
planner scoring: false
site Tier List algorithm: unverified
```

Canonical real receipts:

```text
evidence/real-data/coa-public-api-statistics-provenance-capture-real.json
evidence/real-data/coa-public-api-statistics-persistence-real.json
evidence/real-data/coa-public-api-statistics-profile-reanalysis-real.json
```

Do **not** repeat these single-slice capture/persistence/profile-migration proofs on restart.

## Current exact gate — bounded population coverage v1

Implementation:

```text
src/coa_workbench/analytics/public_api_population_coverage.py
scripts/capture_public_api_population_coverage.py
```

V1 deliberately defines a small set rather than a cartesian crawl:

```text
required slices: 4
metric families represented: 3
role-qualified slices: 3
role-omitted slices: 1
boss/location/week/realm/class/spec expansion: excluded
bulk dataset mode: false
```

The workflow selects the current phase privately from the archived `/phases` catalog, reviews the local DuckDB first, reuses any already persisted matching profiles and makes network requests only for missing slices.

For every new successful slice:

```text
capture -> RawArchive -> Source Observatory -> exact normalization
-> persistence -> deterministic second replay -> source_endpoint_profile dependency
```

Then it reconciles profile-scoped reanalysis and Source & Analysis Health.

Operator command after syncing canonical E4:

```powershell
uv run --no-sync python scripts/capture_public_api_population_coverage.py
```

The command is resumable. It stops on the first incomplete network response; a later rerun intentionally skips already completed matching slices.

Review only the generated scalar-safe receipt:

```text
data/exchange/out/coa-public-api-population-coverage-review.json
```

Do not ask for RawArchive, DuckDB, API key, query values, profile fingerprints or raw response.

Success gate:

```text
coverage_after.complete = true
missing_slice_count = 0
profile-scoped dependency count >= required covered batches
legacy broad dependency count = 0
pending reanalysis = 0
actionable source changes = 0
attention_required = false
planner_scoring_allowed = false
```

## Source-health semantics

Informational `endpoint_added` / `observation_profile_added` events are retained as provenance and are not automatically attention-required. Warning/error changes or pending reanalysis do require attention.

Profile-local schema events invalidate only matching private query profiles. `request_contract_changed` remains endpoint-global. Events older than dependency registration cannot back-trigger newer artifacts.

## Historical report evidence

E3 report persistence/analytics/generalization remains valid on two reports. Historical difficulty equivalence remains `insufficient_evidence`; numeric comparison for that pair remains blocked. Do not resume a difficulty-v4 heuristic.

## Upstream source

```text
FangYuanWoW/AscensionLogsCompanion
main @ 0f63fe9c50b470402e3a29fba2e0322095856fd4
version 0.67.2
```

Use executable code for client behavior; treat comments/backend claims as hypotheses.

## Browser/HAR

Fallback only for an exact undocumented gap. No anti-bot evasion.

## Local workspace audit

Already completed. The historical helper patch is valuable but incomplete because it depends on missing `coa_workbench.collector.guild_progression_js_lexical`. Preserve privately; do not apply as-is and do not re-request the same patch/inventory on restart.

## Branch/integration debt

```text
main <- e2 (#3) <- e3 (#7) <- e4 (#9)
```

Resolve lower-chain integration debt deliberately; do not blindly choose older canonical document versions.

## Verification

```powershell
uv sync --frozen --extra dev --no-build-package ruff
uv run --no-sync python scripts/verify_repo.py
```

Then verify exact-head GitHub jobs:

```text
public-release-audit
ubuntu
windows
```
