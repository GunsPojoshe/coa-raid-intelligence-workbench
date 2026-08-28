# Continuation prompt — current project state

Updated: **2026-08-28**.

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

The aggregate vertical slice, source-health/dependency migration, bounded multi-profile coverage and one encounter-scoped context are real-proven:

```text
/phases + /bosses: archived/reviewed
provenance-aware /statistics: HTTP 200, archived
request context complete: true
single-slice exact normalization: 21 class summaries / 62 specs / 806 percentile values
single-slice persistence replay: idempotent
population-prior records: 62
Source Observatory integrated: true
legacy broad source_endpoint dependency active: false
bounded population coverage: 4/4 complete
aggregate coverage: 60 class summaries / 162 specs / 2106 percentile values
one bounded encounter context: 4/4 complete
encounter aggregate: 59 class summaries / 148 specs / 1924 percentile values
source_endpoint_profile dependency count after encounter run: 8
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
evidence/real-data/coa-public-api-population-coverage-real.json
evidence/real-data/coa-public-api-encounter-context-real.json
```

Do **not** repeat the generic single-slice, population-coverage or first encounter-context proofs merely to reconfirm them.

## Encounter binding trust boundary

The real encounter-context workflow proved:

```text
valid Ascension Logs report/encounter URL shape
operator-reviewed concrete boss/location/difficulty selection
exact boss name + location -> one official /bosses record
four exact /statistics profiles for that reviewed scope
full RawArchive/persistence/profile-health chain
```

It did **not** independently correlate the selected report encounter to that boss/difficulty through a report API response. Treat the binding as operator-reviewed + official-catalog-bound, not machine source-correlated.

Do not claim `concrete_encounter_reference_validated=true` means the report payload independently verified boss/difficulty; it means the reference shape was validated and the selected scope was then bound separately.

## Current exact gate — matched encounter comparator

Do not cartesian-expand the public API.

For the already selected concrete raid-planning need, build a same-scope location comparator:

```text
same current phase
+ same concrete reviewed difficulty
+ same reviewed location
+ same four metric/role slices
+ bossId omitted
-> review DuckDB first
-> reuse provenance-complete exact location profiles
-> capture only missing slices
-> RawArchive
-> Source Observatory
-> exact normalization/persistence
-> deterministic replay
-> source_endpoint_profile dependency
-> profile-scoped reanalysis + health
-> compare boss-scoped vs location-scoped records only on matching dimensions
```

The comparison may produce descriptive local signals such as:

```text
spec parse-share difference / ratio
metric median/average delta or ratio
sample-size availability
missing/zero-baseline flags
```

These remain descriptive encounter-population context. They are **not** planner scores, mechanic proofs, composition-fit proofs or the site's Tier List algorithm.

Do not use the existing generic `difficulty=all` population coverage as the comparator because it does not match the concrete encounter difficulty.

## Separate future source-correlation gate

At a later bounded step, independently bind the selected report encounter to boss/difficulty through reviewed first-party report evidence or another documented source. Do not reopen historical difficulty-v4 heuristics merely to force this.

## Source-health semantics

Informational `endpoint_added` / `observation_profile_added` events are retained as provenance and are not automatically attention-required. Warning/error changes or pending reanalysis do require attention.

Profile-local schema events invalidate only matching private query profiles. `request_contract_changed` remains endpoint-global. Events older than dependency registration cannot back-trigger newer artifacts.

## Privacy boundary

Keep local/private:

```text
API key
query values
report/encounter ids in public receipts
boss/location/difficulty values in public receipts
phase/metric/role values in public receipts
class/spec dynamic names
raw IDs and paths
request/schema/profile fingerprints
metric and percentile scalar values
DuckDB and raw payloads
```

Public real receipts remain counts/booleans/version markers only.

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
