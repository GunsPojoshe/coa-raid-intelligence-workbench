# Фактическое состояние проекта

Дата актуализации: **2026-08-14**.

## GitHub

Active branches:

```text
main
e2/log-evidence-refactor
e3/real-log-capture
```

PR #7 remains Draft: `e3/real-log-capture -> e2/log-evidence-refactor`.

Latest fully verified checkpoint before the current Source Health commit:

```text
HEAD: 905bf6f38226319964eaa5bd0c9281f206e7505b
Verify repository #651: success
public-release-audit: success
ubuntu: success
windows: success
```

Newer HEAD/CI must always be checked live.

## Network-first Source Observatory baseline

A sanitized browser HAR from the real `/guilds/progression` page was inventoried and then persisted into the local immutable corpus.

Actual runtime data routes observed in that page load:

```text
GET /api/phases
GET /api/guilds/phase-progression?phase=<value>&difficulty=<value>
```

Both returned `200 application/json` and were recorded through Source Observatory as schema-bearing captures.

Versioned public baseline receipt:

```text
evidence/real-data/source-observatory-network-baseline-2026-08-14.json
```

The receipt publishes only structural/fingerprint/count metadata. HAR, raw bodies, query values, cookies, headers and dimension values remain private/local.

## Persisted local baseline

Observed Source Observatory state:

```text
phases_api
  capture mode: browser_har
  HTTP: 200 JSON
  schema snapshot: recorded
  phase dimension values observed: 3

guild_phase_progression_api
  capture mode: browser_har
  HTTP: 200 JSON
  schema snapshot: recorded
  boss dimension values observed: 12
  location dimension values observed: 2
  phase dimension values observed: 1
  difficulty dimension values observed: 1
```

The first observations created two `endpoint_added` change events. No reanalysis requests were created yet because no derived artifact dependency has been registered against these endpoints.

Local Git status in the handoff had no tracked changes; only the old untracked `e3-current-local.patch` remained.

## Important route correction

The historical assumption around a direct `POST /api/guilds/progression` remains superseded.

Current evidence distinguishes:

```text
archived SPA alternate contracts:
  GET /api/guilds/progression/rankings
  GET /api/guilds/progression/full-clears
  GET /api/guilds/progression/rankings/{bossId}

actual runtime requests observed on the current progression page:
  GET /api/phases
  GET /api/guilds/phase-progression
```

Do not assume an alternate SPA contract is currently used merely because it still exists in the frontend bundle.

## Source Observatory operating direction

The product path is now:

```text
browser/network observation
-> sanitized same-origin API inventory
-> reviewed route registry
-> immutable raw capture
-> schema/dimension snapshot
-> change registry
-> dependency graph
-> scoped reanalysis
-> Source & Analysis Health
```

The next tooling slice adds:

```text
scripts/observe_network_cycle.py
scripts/source_health.py
src/coa_workbench/collector/source_health.py
```

`observe_network_cycle.py` processes one browser HAR against all currently reviewed GET contracts, rather than requiring one command per endpoint.

`source_health.py` reports endpoint health, latest acquisition/capture/schema state, open change events and pending reanalysis requests without exposing raw payload or dimension values.

## Next product work

After the operational Source Health slice is green:

```text
make recurring capture acquisition easier than manual per-endpoint handling
-> normalize schema handling for dynamic keyed maps where necessary
-> register real derived artifact dependencies
-> create scoped reanalysis requests on source changes
-> add Source & Analysis Health to localhost UI
-> expand Network-first discovery to reports/encounters/characters/armory/talent-grid/BisBeard
```

No unknown write contracts. No automatic semantic trust promotion. Raw/private material remains usable for analysis but is not published by default.
