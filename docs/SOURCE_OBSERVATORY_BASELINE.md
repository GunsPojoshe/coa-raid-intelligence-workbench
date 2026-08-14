# Source Observatory baseline — 2026-08-14

## Purpose

This document records the first successful Network-first Source Observatory baseline from a real browser page load.

The private browser HAR and raw response bodies remain local. The repository stores only sanitized structural evidence.

## Network inventory

One browser load of the CoA guild progression page produced:

```text
same-origin API entries: 7
normalized API route shapes: 6
data-candidate route shapes: 3
```

Observed same-origin route classes included:

```text
session/control
guild progression data
phase catalog data
report queue data
telemetry
```

The sanitized inventory retains method, route shape, query-key names, status/content family and JSON structural fingerprints, but not query values, cookies, headers or response scalar values.

## First persisted reviewed endpoints

### `phases_api`

```text
GET /api/phases
HTTP 200
application/json
capture mode: browser_har
schema snapshot recorded: true
scan truncated: false
```

Observed domain-dimension count:

```text
phase_number: 3
```

### `guild_phase_progression_api`

```text
GET /api/guilds/phase-progression
reviewed query keys:
  phase
  board
  difficulty

HTTP 200
application/json
capture mode: browser_har
schema snapshot recorded: true
scan truncated: false
```

Observed domain-dimension counts:

```text
bossId: 12
location: 2
phase: 1
difficulty: 1
```

These are observations for the captured point in time, not hardcoded product constants.

## Change baseline

The first successful schema-bearing capture of each endpoint created:

```text
endpoint_added: 2
```

No reanalysis requests were created because no derived artifact dependency was yet registered against these endpoints.

Future captures can now produce meaningful diffs against a persisted prior state.

## Runtime route lesson

Static SPA analysis and runtime network observation are complementary, not interchangeable.

The archived frontend still exposes alternate progression GET contracts, but the current progression page load used:

```text
/api/phases
/api/guilds/phase-progression
```

Therefore current runtime traffic is the primary source-discovery signal.

## Operational loop

The next standard cycle is:

```text
browser HAR
-> scripts/observe_network_cycle.py
-> sanitized API inventory
-> ingest every matching reviewed GET route
-> immutable RawArchive
-> schema/dimension diff
-> change registry
-> scripts/source_health.py
```

Later, browser acquisition itself should be automated or reduced to one bounded local action.

## Privacy

Versioned:

```text
route shapes
query-key names
HTTP status/content family
schema fingerprints
dimension counts
change-event counts
sanitized inventory fingerprint
```

Local/private:

```text
original HAR
request/response headers
cookies/session material
query values
raw JSON bodies
raw source identifiers and scalar values
local DuckDB/raw archive
```
