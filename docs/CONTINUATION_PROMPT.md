# Continuation prompt — CoA Raid Intelligence Workbench

Continue development of `GunsPojoshe/coa-raid-intelligence-workbench`.

## Start

Perform GitHub/PR/CI/repository work directly. Use the user only for inaccessible Windows/browser/private boundaries and bundle those operations into one action whenever possible.

Read:

```text
AGENTS.md
docs/PROJECT_MASTER_CONTEXT.md
docs/PROJECT_STATE.md
docs/SOURCE_OBSERVABILITY_AND_REANALYSIS.md
docs/SOURCE_OBSERVATORY_BASELINE.md
docs/E3_GUILD_PROGRESSION_EVIDENCE_STATUS.md
docs/CI_OPERATIONS.md
```

Live GitHub and current local evidence override historical checkpoint text.

## Network-first rule

```text
real browser/network request
-> sanitized API inventory
-> reviewed contract
-> immutable capture
-> schema/dimension observation
-> source change
-> dependency
-> scoped reanalysis
```

SPA/static analysis is supporting evidence, not the first choice when runtime network traffic is available.

## Current local baseline

The user's local immutable corpus already contains successful browser-HAR observations for:

```text
phases_api
guild_phase_progression_api
```

Do not ask the user to rediscover/re-export this baseline just to continue development.

Public structural receipt:

```text
evidence/real-data/source-observatory-network-baseline-2026-08-14.json
```

## Operational tooling

```text
scripts/inventory_network_har.py
scripts/observe_source.py
scripts/observe_network_cycle.py
scripts/rebuild_source_dimensions.py
scripts/source_health.py
```

`observe_network_cycle.py` is the normal whole-HAR ingestion path. It now also rebuilds the approved source dimension index after capture.

## Source dimension index

Migration `0011` adds `source_dimension_index_value`.

The index is a real derived artifact with `artifact_dependency` rows bound to Observatory-ready registry routes that declare `dimension_keys`.

Approved automatic chain:

```text
source change
-> reanalysis_request
-> deterministic dimension-index rebuild
-> analysis_run completed
-> matching reanalysis_request completed
```

This automatic processing does not promote mechanic trust or planner scoring.

## Source & Analysis Health

```text
/source-health
/api/source-health
```

The localhost health view shows sources, captures, acquisition outcomes, dimension counts, source changes, dependencies, pending reanalysis and analysis runs. It must never expose HAR, cookies, request headers, raw payloads or dimension values.

## Progression correction

Do not resume the old helper/owner investigation and do not use guessed `POST /api/guilds/progression`.

Current runtime evidence is based on `/api/phases` and `/api/guilds/phase-progression`. Archived SPA `progression/rankings*` routes remain alternate reviewed GET contracts only.

## Next path

```text
verify exact-head CI
-> initialize source_dimension_index against the user's existing baseline in one bundled local action
-> later run one new browser/network capture cycle
-> verify real no-change/change and scoped reanalysis behavior
-> reduce manual browser capture work
-> expand reviewed Network-first coverage
```

Expansion targets: reports, encounters, rankings/statistics, characters, Armory/talent-grid, BisBeard.

## Safety

- Never rewrite published migrations.
- Never delete `.gitkeep`.
- Private/raw files are valid analysis inputs but are not public by default.
- Never promote new source fields/dimensions into trusted mechanics or scoring automatically.
- Never infer runtime use from static frontend presence alone.
