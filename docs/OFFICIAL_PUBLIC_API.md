# Official CoA Ascension Logs Public API

Status date: **2026-08-27**.

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
  report/encounter event and actor surfaces
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

Local key boundary:

```text
data/private/coa-logs-api-key.txt
fallback: COA_LOGS_API_KEY
```

The key never enters Git, request URLs, RawArchive metadata, public receipts, logs or screenshots.

Published access text requires visible attribution for public display of API-derived data and disallows bulk dataset redistribution. Raw payloads remain local evidence.

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

## `/statistics` contract

Required:

```text
phase
```

Documented optional dimensions include:

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

Documented damage modes:

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

For healing metric requests the collector omits `role` per the reviewed API contract.

Documented metric-object fields:

```text
avg
median
max
min
total_parses
percentiles
```

`total_parses` may support a workbench-derived participation feature. It is not evidence of the site's private Tier List algorithm.

## Real catalog evidence

```text
phase records: 3
active phases: 1
current-by-null-end-date: 1
active + current candidate: 1
boss records: 285
unique stable boss_id values: 285
duplicate stable boss_id values: 0
```

Receipt:

```text
evidence/real-data/coa-public-api-catalog-real.json
```

The current phase is selected only when one unambiguous observed record satisfies the reviewed rule `is_active=true` + `end_date=null`. The scalar phase value stays private.

## Real statistics evidence

Historical structure receipts:

```text
evidence/real-data/coa-public-api-statistics-capture-real.json
evidence/real-data/coa-public-api-statistics-shape-real.json
```

They proved a valid response shape but the older capture did not retain the requested non-echoed `role` value, so it could not support fully scoped normalization.

A new bounded provenance-aware capture closed that gap:

```text
HTTP 200
application/json
archived: true
bytes: 21306
request context retained privately: true
query values published: false
source scalar values published: false
```

Receipt:

```text
evidence/real-data/coa-public-api-statistics-provenance-capture-real.json
```

Real exact normalization/persistence then proved:

```text
class summaries: 21
spec records: 62
percentile scalar values: 806
request context complete: true
first-pass class inserts: 21
first-pass spec inserts: 62
second-pass class matches: 21
second-pass spec matches: 62
second-pass new inserts: 0
idempotent: true
population-prior records: 62
records with local_parse_share: 62
analysis_run registered: true
raw dependency registered: true
```

Receipt:

```text
evidence/real-data/coa-public-api-statistics-persistence-real.json
```

The later local no-network replay proved the source-health/profile dependency layer:

```text
archived capture replayed: true
Source Observatory integrated: true
source_endpoint_profile dependency registered: true
legacy unscoped source_endpoint dependency active: false
profile dependency count: 1
eligible old events after registration: 0
created reanalysis requests: 0
pending reanalysis requests: 0
actionable open source changes: 0
health attention required: false
```

Receipt:

```text
evidence/real-data/coa-public-api-statistics-profile-reanalysis-real.json
```

No receipt publishes dynamic class/spec names, request values, difficulty/phase values, metric values, raw IDs, profile fingerprints or credentials.

## Request-scope provenance rule

Exact aggregate interpretation requires the actual request dimension values, not just the response body.

New captures store prepared query values only in private RawArchive observation metadata:

```text
private RawArchive: exact query values allowed/required for reproducibility
public capture receipt: values excluded
public persistence/health/coverage receipts: values excluded
```

The API key remains excluded from RawArchive metadata entirely.

## Exact normalization and persistence

Implemented:

```text
src/coa_workbench/normalizer/public_api_statistics.py
src/coa_workbench/collector/public_api_archive.py
src/coa_workbench/storage/public_api_statistics.py
src/coa_workbench/analytics/public_api_population_priors.py
migrations/0013_public_api_statistics.sql
scripts/persist_public_api_statistics.py
```

The normalizer:

```text
requires success=true
validates documented request enums
validates exact metric-object structure
requires finite numeric metrics and nonnegative total_parses
resolves request scope from private provenance and response-echoed dimensions
rejects query/response conflicts
fails closed when a requested non-echoed dimension is unavailable
iterates dynamic class/spec keys without hardcoding names
```

Persistence uses deterministic insert-or-match semantics keyed to the RawArchive object and normalizer version.

Population prior:

```text
local_parse_share = spec total_parses / sum(spec total_parses within the same batch)
```

This is a local descriptive aggregate only.

## Source Observatory / Source & Analysis Health

The aggregate artifact uses:

```text
src/coa_workbench/collector/public_api_source_health.py
src/coa_workbench/collector/source_profile_reanalysis.py
```

Archived statistics responses can be replayed into the generic observability layer without network I/O:

```text
private archived request provenance
-> reviewed request reconstruction
-> source_capture
-> source_schema_snapshot
-> source_acquisition_observation
-> source_change_event when applicable
-> profile-scoped artifact dependency
-> Source & Analysis Health
```

All documented `/statistics` request-shaping query dimensions are configured as private `schema_profile_keys`. Different phase/difficulty/metric/role/filter scopes therefore have separate schema baselines.

Persistence registers:

```text
raw_object
  exact payload provenance

source_endpoint_profile
  private reviewed query-profile dependency for source-change reanalysis
```

The legacy broad aggregate `source_endpoint` dependency is deactivated when an existing batch is replayed through current persistence.

Profile-local changes match only dependencies with the same private `observation_profile_key`. `request_contract_changed` remains endpoint-global and intentionally fans out to every active profile dependency. Events older than dependency registration cannot back-trigger the new artifact.

The first Source Observatory registration may leave an informational `endpoint_added`. Dedicated aggregate health distinguishes informational baseline events from actionable warning/error changes.

## Bounded population coverage v1

Implementation:

```text
src/coa_workbench/analytics/public_api_population_coverage.py
scripts/capture_public_api_population_coverage.py
```

V1 is deliberately not a bulk crawl. It defines a small current-phase set:

```text
required slices: 4
metric families represented: 3
role-qualified slices: 3
role-omitted slices: 1
broader population dimensions: held stable
boss/location/week/realm/class/spec expansion: not included
```

Operator properties:

```text
select current phase privately from archived /phases
review DuckDB before network access
reuse already persisted matching slices
capture only missing slices
stop on the first incomplete response
archive before interpretation
observe + normalize + persist each successful slice
perform deterministic second replay locally
reconcile profile-scoped reanalysis
emit scalar-safe counts/booleans only
```

The command is resumable:

```powershell
uv run --no-sync python scripts/capture_public_api_population_coverage.py
```

Default public-safe receipt:

```text
data/exchange/out/coa-public-api-population-coverage-review.json
```

Real multi-profile coverage execution remains pending until the operator runs this bounded workflow on the local RawArchive/DuckDB.

## Event-level semantics documented by the API

The experimental schema documents, among other things:

```text
Event.id
  opaque 64-bit id serialized as string

Event.timestamp_ms
  milliseconds from encounter combat start, not wall clock

Event.amount
  64-bit value serialized as string; meaning depends on event type

Event.spell_id
  -1 is the documented melee sentinel

is_glancing / is_crushing
  nullable; null is not proof of mechanic absence

EncounterSummary.duration_seconds
  explicitly seconds
```

These are strong contract semantics but do not make one observed event a universal gameplay mechanic.

## Gaps in API v1.0.0

No documented endpoint was found for:

```text
Meta Builds / talents / gear / enchants
Armory
Guild progression
site Tier List algorithm
```

Those gaps use pinned client source, persisted first-party evidence or narrow fallback discovery.

## Relationship to historical report difficulty work

Historical two-report difficulty equivalence remains `insufficient_evidence` and blocks numeric comparison of that specific pair. It does not block official aggregate analytics because `/statistics` exposes explicit documented dimensions.

## Current next gate

```text
real normalization/persistence/idempotence: proven
real Source Observatory/Health: proven
real profile-scoped dependency migration: proven
-> run bounded population coverage v1
-> prove missing-only capture + multi-profile persistence + health on real local data
-> store one scalar-safe real coverage receipt
-> decide any next dimension expansion from product need rather than cartesian completeness
```

Do not request `events:read`, capture a HAR or run Playwright for this gate.
