# Continuation prompt — CoA Raid Intelligence Workbench

Continue development of `GunsPojoshe/coa-raid-intelligence-workbench`.

## Start

The agent first performs all GitHub work itself: inspect repository, PR #7, PR #3, current remote HEAD and exact-head CI. Do not ask the user to run GitHub commands for information available through the connector.

Use the user only for Windows/local/private operations that the agent cannot directly execute. Bundle local work into one action whenever possible.

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

## Current source-discovery model

Network-first is canonical.

```text
browser/network capture
-> sanitized same-origin API inventory
-> reviewed source contracts
-> immutable raw archive
-> schema/dimension snapshots
-> source change registry
-> dependency/reanalysis graph
```

SPA/static analysis is secondary and is used when real network traffic does not explain request construction or hidden contracts.

## Current progression evidence

Do not resume the old helper/owner investigation and do not use direct `POST /api/guilds/progression`.

Archived SPA evidence still contains alternate GET contracts:

```text
GET /api/guilds/progression/rankings
GET /api/guilds/progression/full-clears
GET /api/guilds/progression/rankings/{bossId}
```

But the actual browser runtime capture of the current progression page observed:

```text
GET /api/phases
GET /api/guilds/phase-progression?phase=<value>&difficulty=<value>
```

Both returned 200 JSON and are now the first persisted Network-first Source Observatory baseline.

Canonical public baseline receipt:

```text
evidence/real-data/source-observatory-network-baseline-2026-08-14.json
```

## Local corpus boundary

The user's local DuckDB/raw archive contains the real browser-origin baseline for:

```text
phases_api
guild_phase_progression_api
```

Do not ask the user to re-export or re-run the same HAR merely to rediscover this baseline.

The original HAR/raw bodies remain private/local. Private files may be inspected when required; publication/versioning is a separate decision.

## Operational tooling

Current Source Observatory tooling includes:

```text
scripts/inventory_network_har.py
scripts/observe_source.py
scripts/observe_network_cycle.py
scripts/source_health.py
```

Prefer `observe_network_cycle.py` for a complete reviewed-route ingestion cycle from one HAR instead of one endpoint command at a time.

`source_health.py` is the command-line precursor of the future Source & Analysis Health UI.

## Next product path

```text
verify exact-head CI
-> make browser/network acquisition repeatable with minimal user action
-> improve dynamic schema normalization where source maps use IDs as object keys
-> register derived artifact dependencies
-> generate scoped reanalysis requests from real source changes
-> expose Source & Analysis Health in localhost UI
-> expand Network-first source coverage
```

Expansion targets:

```text
reports
encounters
rankings/statistics
characters
Armory/talent-grid
BisBeard
```

## Safety

- Never rewrite published migrations.
- Never delete `.gitkeep`.
- Never publish HAR/cookies/tokens/headers/raw private bodies by default.
- Never promote a new field or source into trusted mechanic/scoring semantics automatically.
- Never infer a route is current merely because it appears in static frontend code.
- Do not ask the user to perform GitHub work the connector can do.
