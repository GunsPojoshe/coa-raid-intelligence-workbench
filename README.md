# CoA Raid Intelligence Workbench

Localhost-first, evidence-first raid intelligence for **Ascension WoW / Conquest of Azeroth**.

Primary product question:

> **Почему конкретный человек нужен именно текущему составу?**

The project is not a DPS-ranking scraper. Its trust model requires every important conclusion to preserve provenance from source observation through reviewed transformation to the final analytical claim.

## Current workstreams

```text
e3/real-log-capture
  stable/canonical report-evidence baseline

e4/interactive-har-discovery
  current isolated source-discovery branch
  Draft PR #9 -> e3/real-log-capture
```

The E4 branch name is historical. The active E4 paradigm is now **official-API + upstream-source first**; Browser Observatory/HAR is a fallback tool.

## Source priority

```text
1. official documented CoA Ascension Logs public API
2. official documented site semantics
3. pinned executable AscensionLogsCompanion source
4. persisted first-party report/API responses
5. narrow browser/network observation for undocumented gaps
6. structural inference only after stronger sources are exhausted
```

See `docs/CURRENT_PARADIGM.md` and `docs/DOCUMENTATION_INDEX.md`.

## Current official API lane

Reviewed contract:

```text
https://coa.ascensionlogs.gg/api/public/v1/openapi.json
OpenAPI 3.1.0
API version 1.0.0
```

Self-service `stats:read`:

```text
GET /phases
GET /bosses
GET /statistics
```

Experimental/on-request `events:read` is a separate future research lane and is not used by the current aggregate collector.

Real evidence currently proves:

```text
phases:                              3
active/current phase candidates:     1
bosses:                            285
unique stable boss_id values:      285
first current-phase /statistics: HTTP 200, archived
statistics top-level entries:       21
statistics max observed depth:       5
objects with documented metrics:    83
statistics normalization ready:   true
```

The real statistics shape receipt does not publish class/spec names, difficulty values, query values or numeric source metrics.

## Local API key

Default private file:

```text
data/private/coa-logs-api-key.txt
```

`data/private/**` is Git-ignored. The capture CLI prefers this file and may fall back to `COA_LOGS_API_KEY`. Never place the key in a CLI argument, query string, Git artifact, RawArchive metadata, screenshot or public receipt.

## Quick verification

Python requirement: **3.12+**.

```powershell
uv sync --frozen --extra dev --no-build-package ruff
uv run --no-sync python scripts/verify_repo.py
```

GitHub CI must pass for the exact pushed HEAD:

```text
public-release-audit
ubuntu
windows
```

## Current API workflow

Catalog review from already archived `/phases` + `/bosses`:

```powershell
uv run --no-sync python scripts/review_public_api_catalog.py
```

Current-phase aggregate capture:

```powershell
uv run --no-sync python scripts/capture_current_public_api_statistics.py
```

Scalar-safe statistics shape review:

```powershell
uv run --no-sync python scripts/review_public_api_statistics.py
```

The next implementation gate is **exact `StatisticsResponse` normalization + DuckDB persistence + idempotence**, not another browser probe.

## Historical report lane

The E3 report pipeline remains valuable for private report-specific analytics, source observability and corroboration. The existing two-report difficulty/equivalence investigation remains `insufficient_evidence`; numeric cross-report scoring for that historical pair stays blocked.

No difficulty-v4 heuristic is planned simply to force an answer.

## Client-source lane

Pinned source evidence:

```text
FangYuanWoW/AscensionLogsCompanion
main @ 0f63fe9c50b470402e3a29fba2e0322095856fd4
version 0.67.2
```

The repository contains deterministic Lua source inventory/lineage tools. Executable upstream code is strong evidence of client behavior; comments/backend notes are hypotheses until corroborated.

## Repository layout

```text
src/coa_workbench/analytics/    deterministic analytics/reviews
src/coa_workbench/collector/    source contracts/acquisition/observability
src/coa_workbench/normalizer/   normalization
src/coa_workbench/planner/      planner layer, trust-gated
src/coa_workbench/storage/      DuckDB persistence/read models
src/coa_workbench/web/          localhost API/UI
scripts/                        durable project/operator commands
config/                         reviewed source/mapping configuration
migrations/                     forward-only DuckDB migrations (currently 0001-0012)
tests/                          deterministic coverage
evidence/real-data/             scalar-safe real receipts only
docs/                           current + historical documentation
```

## Private/local workspace

Git is not the whole operational corpus. Ignored/untracked raw data, DuckDB, API captures and helper artifacts can be authoritative local inputs and must not be destroyed as “cleanup”.

For an exact workstation integrity audit:

```powershell
uv run --no-sync python scripts/inventory_local_workspace.py
```

Private manifest:

```text
data/private/local-workspace-inventory.json
```

The inventory reads metadata only, not file contents or secret values. See `docs/LOCAL_WORKSPACE_AUDIT.md`.

## Trust boundary

Do not infer mechanics from field names, UI labels, talent names, item metadata or one combat result. Do not equate character name with identity. Do not expose private IDs/names/query values/dynamic keys through public receipts or low-entropy hashes.

Population aggregates can be collected now; **planner scoring remains blocked** until the required normalization, identity, mechanic and composition reasoning gates are separately proven.

## Documentation

Start with:

```text
AGENTS.md
docs/DOCUMENTATION_INDEX.md
docs/CURRENT_PARADIGM.md
docs/PROJECT_STATE.md
docs/OFFICIAL_PUBLIC_API.md
docs/CONTINUATION_PROMPT.md
```

Dated experiment documents are retained as historical evidence and do not override current state.
