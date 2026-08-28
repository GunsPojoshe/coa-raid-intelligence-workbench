# CoA Raid Leader Companion

Local-first raid planning and analytics workbench for **Conquest of Azeroth**.

The product is designed for a raid leader who needs to answer practical questions about the current roster: who to bring, what the composition is missing, how a player or specialization compares with relevant population context, and what evidence supports a recommendation.

It is not a scraper clone of Ascension Logs and it is not a static DPS tier list. Ascension Logs is one source of evidence; the workbench keeps its own normalized data and builds independent analytics in DuckDB.

## Architecture

```text
Browser
  -> FastAPI
  -> Planner / Catalog / Analytics
  -> DuckDB

External evidence
  -> official CoA Ascension Logs public API
  -> pinned AscensionLogsCompanion source where needed
  -> persisted first-party observations for documented gaps
  -> narrow browser/network fallback only for exact undocumented gaps
```

The application is localhost-only by default:

```text
http://127.0.0.1:8000
```

## Current capabilities

- local raid-plan persistence and composition UI;
- class/spec catalog and effect-coverage model;
- official Ascension Logs `stats:read` integration for phases, bosses and class/spec statistics;
- deterministic normalization and DuckDB persistence of bounded population slices;
- population priors and encounter-vs-location comparison models;
- Source Observatory, scoped dependency tracking and deterministic reanalysis;
- persisted report-scoped roster/build observations with explicit provenance;
- public-safe evidence receipts for real verification runs.

Planner scoring remains fail-closed: aggregate statistics, a field name, one combat result or one report are never promoted automatically into a roster recommendation.

## Official Ascension Logs API

Primary documented base:

```text
https://coa.ascensionlogs.gg/api/public/v1
```

Self-service `stats:read`:

```text
GET /phases
GET /bosses
GET /statistics
```

The public contract also documents experimental/on-request `events:read` report, actor and combat-event routes. Event-level data is an optional future input for independent encounter analytics; the aggregate product does not depend on that scope.

API keys stay local in:

```text
data/private/coa-logs-api-key.txt
```

or `COA_LOGS_API_KEY`. Keys, cookies, raw payloads and private report/player values are never committed.

## Quick start

```powershell
uv sync --extra dev
uv run coa-workbench init-db --database data/warehouse/coa.duckdb --migrations migrations
uv run coa-workbench serve
```

Useful checks:

```powershell
uv run coa-workbench doctor --project-root .
uv run --no-sync python scripts/verify_repo.py
```

## Repository map

```text
src/coa_workbench/web/          localhost application/API
src/coa_workbench/planner/      composition/planner primitives
src/coa_workbench/analytics/    deterministic analytics and trust-gated reviews
src/coa_workbench/collector/    source contracts, acquisition and observability
src/coa_workbench/normalizer/   deterministic normalization
src/coa_workbench/storage/      DuckDB persistence/read models
config/                         reviewed source and mapping contracts
migrations/                     forward-only migrations 0001-0013
scripts/                        maintained operators and verification tools
tests/                          unit/integration/golden coverage
evidence/real-data/             public-safe scalar receipts only
baseline/                       frozen migration/reference exports from the original workbook
```

The original Excel workbook is not part of runtime. Its extracted baseline/reference artifacts remain only to preserve migration tests and historical rule provenance.

## Source and trust policy

The current source order is:

```text
official documented public API
-> official documented semantics
-> pinned executable Companion source
-> persisted first-party evidence
-> narrow browser/network fallback
-> structural inference last
```

See `docs/DOCUMENTATION_INDEX.md`, `docs/CURRENT_PARADIGM.md` and `docs/OFFICIAL_PUBLIC_API.md` for the maintained architecture and evidence boundaries.
