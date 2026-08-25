# Official CoA Ascension Logs Public API

Status date: **2026-08-26**.

Reviewed source:

```text
https://coa.ascensionlogs.gg/api/public/v1/openapi.json
OpenAPI 3.1.0
API title: Conquest of Azeroth Logs External API
API version: 1.0.0
```

This is the preferred Ascension Logs source whenever it documents the required information.

## Access model

Published scopes:

```text
stats:read
  self-service
  aggregate statistics, phases, bosses

events:read
  on-request
  experimental
  encounter events/actors/report surfaces
```

Published tiers in the reviewed contract:

```text
free:      30 requests/minute,   5,000/day, stats:read
partner:  120 requests/minute,  50,000/day, stats:read
research:  60 requests/minute,  10,000/day, stats:read + events:read
```

Published key headers:

```text
Authorization: Bearer <key>
X-API-Key: <key>
```

Keys are not accepted in query strings.

Local project key boundary:

```text
data/private/coa-logs-api-key.txt
fallback environment variable: COA_LOGS_API_KEY
```

The value must never enter Git, request URLs, RawArchive metadata, public receipts, logs or screenshots.

Published access text also requires visible attribution when API-derived data is displayed publicly and disallows bulk dataset redistribution. Raw API payloads are therefore treated as local evidence.

## Route inventory

Unauthenticated:

```text
GET /health
GET /openapi.json
```

Self-service `stats:read`:

```text
GET /phases
GET /bosses
GET /statistics
```

On-request experimental `events:read`:

```text
GET /reports
GET /reports/{reportId}
GET /reports/{reportId}/encounters/{encounterId}/events
GET /reports/{reportId}/encounters/{encounterId}/actors
```

Reviewed registry:

```text
config/coa_public_api_sources.yaml
source_code = coa_ascension_logs_public_api
base_url = https://coa.ascensionlogs.gg/api/public/v1
```

## Aggregate statistics contract

`GET /statistics` requires `phase` and documents optional dimensions including:

```text
difficulty
metric
bracket
location
bossId
damageMode
role
class
spec
weekNumber
realm
```

Documented difficulty values:

```text
normal
heroic
mythic
ascended
all
```

Documented metrics:

```text
avg_dps
avg_hps
avg_dtps
```

Documented damage attribution modes:

```text
standard
boss-only
trash
```

Documented role values:

```text
tank
dps
tanks-and-dps
support
```

Documented metric-object fields:

```text
avg
median
max
min
total_parses
percentiles
```

`total_parses` can support a workbench-derived participation/popularity feature, but it is **not** evidence of the site's private Tier List algorithm.

## Real catalog evidence

The bounded real `/phases` + `/bosses` capture/review proved:

```text
phase records: 3
active phases: 1
current-by-null-end-date: 1
active + current candidate: 1
boss records: 285
unique stable boss_id values: 285
duplicate stable boss_id values: 0
```

Public-safe receipt:

```text
evidence/real-data/coa-public-api-catalog-real.json
```

The project selects the current phase only when the observed payload has one unambiguous candidate satisfying the reviewed current-phase rule. The scalar phase value remains private.

## Real current `/statistics` evidence

The current-phase selector used the unique `is_active=true` + `end_date=null` phase without publishing its scalar value.

Capture result:

```text
HTTP 200
application/json
archived: true
query values published: false
source scalar values published: false
```

Capture receipt:

```text
evidence/real-data/coa-public-api-statistics-capture-real.json
```

Deterministic scalar-safe shape review of the archived real payload proved:

```text
statistics kind: object
statistics top-level entries: 21
max observed nested depth: 5
objects with documented metric fields: 83
documented metric field occurrences: 393
statistics_normalization_ready: true
```

The review publishes no dynamic class/spec keys, query values, difficulty/phase values, metric values or percentile values.

Shape receipt:

```text
evidence/real-data/coa-public-api-statistics-shape-real.json
```

## Event-level semantics documented by the API

The experimental schema documents useful units/types, including:

```text
Event.id
  64-bit id serialized as string; treat as opaque

Event.timestamp_ms
  integer milliseconds from encounter combat start, not wall clock

Event.amount
  64-bit value serialized as string; event-type dependent

Event.spell_id
  -1 is the documented melee sentinel

is_glancing / is_crushing
  nullable; null is not evidence of mechanic absence

EncounterSummary.duration_seconds
  explicitly named in seconds
```

The event endpoint also documents actor source/target filters, spell filters, start/end millisecond offsets and keyset pagination. Actor IDs are resolved through the separate `/actors` dictionary.

These are strong contract semantics but do not make one observed event a universal gameplay mechanic.

## Gaps in API v1.0.0

No documented endpoint was found for:

```text
Meta Builds / talents / gear / enchants
Armory
Guild progression
site Tier List algorithm
```

Those surfaces require pinned client source, first-party persisted evidence or narrow fallback discovery.

## Relationship to historical report difficulty work

Historical two-report difficulty equivalence remains `insufficient_evidence` and still blocks numeric comparison of that specific pair.

It does **not** block official aggregate population analytics because `/statistics` exposes explicit documented dimensions within its own contract.

## Implementation

```text
config/coa_public_api_sources.yaml
src/coa_workbench/collector/public_api_contract.py
src/coa_workbench/collector/public_api_catalog.py
src/coa_workbench/collector/public_api_statistics_review.py
scripts/review_public_api_contract.py
scripts/capture_public_api_stats.py
scripts/capture_current_public_api_statistics.py
scripts/review_public_api_catalog.py
scripts/review_public_api_statistics.py
```

Current real capture path is bounded and credential-safe:

```text
private key file/environment
-> reviewed endpoint registry
-> HTTPS request with header credential
-> immutable RawArchive payload
-> scalar-safe capture receipt
-> scalar-safe structural review
```

## Current next gate

Discovery is complete enough for the first aggregate model. Next:

```text
exact parser for the observed documented StatisticsResponse
-> normalized aggregate representation
-> forward-only DuckDB migration/persistence
-> idempotent replay of the existing archived capture
-> read model for population priors by explicit documented dimensions
-> Source & Analysis Health integration
```

Do not request `events:read`, capture a new HAR or run Playwright for this gate.
