# Source Observatory baseline — 2026-08-14

## Purpose

This document records the first successful Network-first Source Observatory baseline from a real
browser page load and its first real deterministic derived layer.

The private browser HAR, raw response bodies and actual dimension values remain local. The repository
stores only sanitized structural evidence.

## Network inventory

One browser load of the CoA guild progression page produced:

```text
same-origin API entries: 7
normalized API route shapes: 6
data-candidate route shapes: 3
```

Observed same-origin route classes included session/control, guild progression data, phase catalog data,
report queue data and telemetry.

The sanitized inventory retains route shape, query-key names, status/content family and structural
metadata, but not query values, cookies, request headers or response scalar values.

## Persisted reviewed endpoints

### `phases_api`

```text
GET /api/phases
HTTP 200
application/json
capture mode: browser_har
schema snapshot recorded: true
scan truncated: false
observed phase_number values: 3
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
observed bossId values: 12
observed location values: 2
observed phase values: 1
observed difficulty values: 1
```

These counts describe one observation, not permanent game configuration.

## Initial change baseline

The first schema-bearing capture of each endpoint created:

```text
endpoint_added: 2
```

At that moment no derived dependency was registered, so no reanalysis request was emitted.

## Real derived baseline

The local Source Observatory has now initialized the approved `source_dimension_index` derived artifact.

```text
status: completed
observed endpoints: 2
active source_endpoint dependencies: 2
dimension names represented: 5
dimension values represented: 19
completed analysis runs: 1
acquisition-problem endpoints: 0
```

The active dependencies are the two persisted reviewed endpoints above.

Canonical structural receipt:

```text
evidence/real-data/source-observatory-derived-baseline-2026-08-14.json
```

## Same-input idempotence

The original already-existing HAR was replayed locally through the normal `observe_network_cycle.py`
path. The replay itself performed no network request.

```text
reviewed route observations replayed: 2
open change events: 2 -> 2
pending reanalysis: 0 -> 0
new change events: 0
new reanalysis requests: 0
Source & Analysis Health before/after: identical
```

This proves real same-input/no-change idempotence. It does not yet prove behavior on a genuinely newer
upstream source change.

## Source-change/reanalysis loop

Current approved loop:

```text
browser HAR
-> reviewed route ingestion
-> immutable RawArchive
-> schema/dimension diff
-> source change event
-> active artifact dependency
-> pending reanalysis_request
-> deterministic source_dimension_index rebuild
-> completed analysis_run
-> Source & Analysis Health
```

No part of this loop automatically promotes mechanics or planner scoring trust.

## Runtime route lesson

Static SPA analysis and runtime network observation are complementary, not interchangeable.

The archived frontend still exposes alternate progression GET contracts, but the captured current page
used:

```text
/api/phases
/api/guilds/phase-progression
```

Runtime network evidence remains the primary source-discovery signal.

## Privacy

Versioned here:

```text
route shapes and endpoint codes
query-key names
HTTP/status families
dimension counts
change/reanalysis counts
derived-analysis state
```

Local/private:

```text
original HAR
request/response headers
cookies/session material
query values
raw JSON bodies
actual dimension values
source record identifiers
local DuckDB/raw archive
```
