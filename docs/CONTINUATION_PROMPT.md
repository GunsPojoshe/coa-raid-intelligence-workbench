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

## Official aggregate API — completed real gate

The first aggregate vertical slice is now real-proven:

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
analysis_run registered: true
raw source dependency registered: true
planner scoring: false
site Tier List algorithm: unverified
```

Canonical new real receipts:

```text
evidence/real-data/coa-public-api-statistics-provenance-capture-real.json
evidence/real-data/coa-public-api-statistics-persistence-real.json
```

Do **not** repeat this capture/persistence proof on restart.

## Current exact gate

Integrate the already proven aggregate artifact with Source Observatory / Source & Analysis Health.

Implementation provides:

```text
private archived capture replay -> reviewed request reconstruction
/statistics request dimensions -> private schema profile
source_capture + source_schema_snapshot + acquisition observation
source_endpoint=public_api_statistics artifact dependency
scalar-safe aggregate health review
```

The real health proof requires only replaying the already archived successful response. It must not perform another network request.

Expected operator command after syncing the current E4 implementation:

```powershell
uv run --no-sync python scripts/persist_public_api_statistics.py
```

Review only the generated scalar-safe receipt:

```text
data/exchange/out/coa-public-api-statistics-persistence-review.json
```

Do not ask for RawArchive, DuckDB, API key, query values or raw response.

## Source-health semantics

First Source Observatory registration may leave one informational `endpoint_added` event open. That is baseline provenance, not by itself an actionable problem.

Aggregate dedicated health should distinguish:

```text
informational baseline event -> retained, not attention-required
actionable warning/error source change -> attention-required
pending reanalysis -> attention-required
healthy acquisition/schema/dependencies/analysis -> integrated
```

Future source changes matter because the aggregate artifact now declares both exact `raw_object` and logical `source_endpoint=public_api_statistics` dependencies.

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
