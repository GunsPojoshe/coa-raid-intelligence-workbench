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

Latest fully verified checkpoint before the current Source Health UI change:

```text
HEAD: 2a74f237a4b38d5a6a01aa360332af4f64c0a2dc
Verify repository #671: success
public-release-audit: success
ubuntu: success
windows: success
```

Newer HEAD/CI must always be checked live.

## Network-first Source Observatory baseline

A sanitized browser HAR from the real `/guilds/progression` page was inventoried and persisted into the local immutable corpus.

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

## Source Observatory operating layer

Current product path:

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

Operational tooling:

```text
scripts/inventory_network_har.py
scripts/observe_source.py
scripts/observe_network_cycle.py
scripts/source_health.py
```

`observe_network_cycle.py` processes one browser HAR against all currently reviewed GET contracts.

## Source & Analysis Health UI

The localhost application now exposes a privacy-safe Source Observatory view:

```text
/source-health
/api/source-health
```

The page shows:

```text
registered/captured source counts
open source-change count
pending reanalysis count
acquisition problems
per-endpoint health state
method + reviewed route template
capture count and latest acquisition outcome
dimension counts without dimension values
recent change types without raw payloads
```

The API initializes migrations before reading the local warehouse, so it also works against a clean localhost database.

It does **not** expose raw payloads, HAR, cookies, request headers or domain dimension values.

## Next product work

```text
register real derived artifact dependencies
-> prove scoped reanalysis from a real source change
-> make recurring browser/network acquisition require minimal operator action
-> normalize dynamic keyed-map schema noise where necessary
-> expand Network-first source coverage to reports/encounters/rankings/statistics/characters
-> Armory/talent-grid
-> BisBeard
```

No unknown write contracts. No automatic semantic trust promotion. Raw/private material remains usable for analysis but is not published by default.
