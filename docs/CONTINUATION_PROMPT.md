# Continuation prompt — current project state

Updated: **2026-08-26**.

Use this to continue development in a fresh session.

## Repository

```text
GunsPojoshe/coa-raid-intelligence-workbench
local: C:\Users\Simpa\source\repos\coa-raid-intelligence-workbench
active workstream: e4/interactive-har-discovery
Draft PR #9 -> e3/real-log-capture
```

Do not trust stored HEAD/CI values. Perform live GitHub checks first.

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
docs/UPSTREAM_ASCENSION_LOGS_EVIDENCE.md
docs/LOCAL_WORKSPACE_BOUNDARY.md
docs/CI_OPERATIONS.md
docs/WINDOWS_DEVELOPMENT_ENVIRONMENT.md
```

Historical dated handoffs/experiments do not override this list.

## Product question

> **Почему конкретный человек нужен именно текущему составу?**

Maintain fail-closed semantics: observation/field/UI labels are not automatic mechanic proof.

## Current source order

```text
official documented public API
official documented site semantics
pinned executable Companion source
persisted first-party report/API evidence
narrow browser/network fallback
structural inference last
```

## Current real API checkpoint

Self-service `stats:read` is reviewed and real-tested:

```text
/phases: archived and reviewed
/bosses: archived and reviewed
/statistics: current-phase HTTP 200, archived and shape-reviewed
```

Public-safe shape:

```text
statistics top-level entries: 21
max depth: 5
objects with documented metric fields: 83
statistics_normalization_ready: true
```

Default key file:

```text
data/private/coa-logs-api-key.txt
```

Never request/paste the key unless a local execution genuinely cannot proceed without operator action; the existing capture CLI reads the file itself.

## Exact next development gate

Do **not** start with HAR, Playwright, a new difficulty heuristic, `events:read` or the historical helper patch.

Implement:

```text
exact deterministic parser for the real documented StatisticsResponse
-> normalized aggregate statistics representation
-> DuckDB migration/persistence
-> idempotent replay on the existing archived real capture
-> read model for population priors using explicit documented dimensions
-> integrate source/analysis health
```

Dynamic class/spec keys are runtime values; do not hardcode current names or publish them in scalar-safe receipts.

## Retained report evidence

E3 report persistence/analytics/generalization remains valid. Two reports passed the generic pipeline. Structural cross-report cohorts exist, but historical difficulty equivalence is still `insufficient_evidence`; numeric comparison for that pair remains blocked.

Do not confuse the independent official aggregate statistics lane with that historical blocker.

## Upstream source

Pinned Companion source remains a first-class client-state evidence provider. Use executable code for client behavior; treat comments/backend claims as hypotheses.

## Browser/HAR

Fallback only for an exact undocumented gap after stronger sources are exhausted. No anti-bot evasion.

## Local workspace audit — completed checkpoint

The real Windows metadata inventory and its sole Git-visible untracked implementation candidate have already been reviewed for the 2026-08-26 checkpoint.

Checkpoint state:

```text
modified tracked files: 0
missing tracked files: 0
Git-visible untracked files: 1
local-only exact file audit: complete/classified
```

The single candidate was a historical E3 helper-analysis patch. It is valuable but incomplete: it modifies 10 current-lineage source/test files and introduces stronger lexical/structural helper analysis, but depends on an absent shared module `coa_workbench.collector.guild_progression_js_lexical`. That module is neither in the patch nor tracked Git history. The patch must be preserved privately and **not applied as-is**.

If the guild-progression helper lane is resumed later, treat reconstruction of the shared JavaScript lexical scanner as a new reviewed task and port the useful behavior/tests deliberately. Do not recreate missing code from assumptions merely to make the patch apply.

Do **not** ask the operator to re-upload the same workspace inventory or historical patch just because a chat restarted. Re-run the inventory only after material local changes or if a new unknown modified/untracked implementation candidate appears.

Do not request broad directory listings or the raw private corpus. RawArchive, DuckDB, API-key, Browser Observatory state and HAR inputs remain private/local evidence and do not require bulk upload for repository integrity.

Inventory schema v3 skips `.venv-capture`/`*.egg-info` tooling noise while flagging raw-transport candidates placed under `data/exchange/out/`. `data/exchange/out/` is local staging, not a blanket publication-safe directory.

## Branch/integration debt

Staged chain:

```text
main <- e2 (#3) <- e3 (#7) <- e4 (#9)
```

At the 2026-08-26 audit, #9 and #7 were mergeable while #3 had lower-chain conflict debt. Resolve branch integration deliberately after current work is coherent; do not blindly choose old document versions or merge Draft PRs just to clear the warning.

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
