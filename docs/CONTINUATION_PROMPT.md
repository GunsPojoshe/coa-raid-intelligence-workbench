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

The aggregate vertical slice, source-health/dependency migration and bounded multi-profile coverage are real-proven:

```text
/phases + /bosses: archived/reviewed
provenance-aware /statistics: HTTP 200, archived
request context complete: true
single-slice exact normalization: 21 class summaries / 62 specs / 806 percentile values
single-slice persistence replay: idempotent
population-prior records: 62
Source Observatory integrated: true
legacy broad source_endpoint dependency active: false
bounded coverage required slices: 4
covered before real run: 1
missing before real run: 3
network requests: 3
successful new captures: 3
persisted new profiles: 3
deterministic second replays: 3
covered after: 4
missing after: 0
coverage complete: true
aggregate coverage: 60 class summaries / 162 specs / 2106 percentile values
source_endpoint_profile dependency count: 4
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
```

Do **not** repeat the generic single-slice or coverage-v1 proofs merely to reconfirm them.

## Current exact gate — product-driven encounter population context

Generic aggregate collection is sufficient for now. Do not turn the public API into a cartesian dataset crawl.

Next design/implementation target:

```text
one concrete planned encounter
-> reviewed official boss/difficulty/location scope selected locally
-> minimal required metric-family slices only
-> reuse existing provenance-complete batches when possible
-> capture only missing encounter-scoped slices
-> RawArchive
-> Source Observatory
-> exact normalization/persistence
-> deterministic replay
-> source_endpoint_profile dependency
-> profile-scoped reanalysis reconciliation
-> Source & Analysis Health
-> descriptive encounter population context
```

This encounter context remains non-scoring. It may describe participation/throughput/survivability distributions for a relevant cohort, but it does not by itself prove player utility, mechanics, composition fit or the site's Tier List logic.

Do not bulk-expand:

```text
all bosses
all locations
all weeks
all realms
all classes/specs
```

Start with one explicitly selected encounter from a real raid-planning need.

## Source-health semantics

Informational `endpoint_added` / `observation_profile_added` events are retained as provenance and are not automatically attention-required. Warning/error changes or pending reanalysis do require attention.

Profile-local schema events invalidate only matching private query profiles. `request_contract_changed` remains endpoint-global. Events older than dependency registration cannot back-trigger newer artifacts.

## Privacy boundary

Keep local/private:

```text
API key
query values
phase/difficulty/metric/role values in public receipts
boss/location/realm/week filter values in public receipts
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
