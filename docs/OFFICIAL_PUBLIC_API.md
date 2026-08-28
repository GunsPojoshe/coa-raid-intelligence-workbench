# Official CoA Ascension Logs Public API

Status date: **2026-08-28**.

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

Local key boundary:

```text
data/private/coa-logs-api-key.txt
fallback: COA_LOGS_API_KEY
```

The key never enters Git, request URLs, RawArchive metadata, public receipts, logs or screenshots.

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

Documented experimental `events:read`:

```text
GET /reports
GET /reports/{reportId}
GET /reports/{reportId}/encounters/{encounterId}/events
GET /reports/{reportId}/encounters/{encounterId}/actors
```

Do not assume `events:read` is available merely because the contract documents it.

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

For healing metric requests the collector omits `role` per the reviewed contract.

Documented metric-object fields:

```text
avg
median
max
min
total_parses
percentiles
```

## Real-proven aggregate / encounter chain

Closed real gates:

```text
/phases + /bosses catalog
provenance-aware /statistics capture
exact normalization
DuckDB persistence + deterministic replay
population-prior read model
Source Observatory + profile-scoped reanalysis
bounded population coverage v1
bounded encounter context v1
matched encounter/location comparator v1
report encounter boss/difficulty source correlation v2
machine-correlated encounter population binding v1
```

Retained implementation anchors:

```text
Request-scope provenance rule
migrations/0013_public_api_statistics.sql
src/coa_workbench/collector/public_api_source_health.py
scripts/capture_public_api_population_coverage.py
```

Scalar-safe receipts:

```text
evidence/real-data/coa-public-api-catalog-real.json
evidence/real-data/coa-public-api-statistics-provenance-capture-real.json
evidence/real-data/coa-public-api-statistics-persistence-real.json
evidence/real-data/coa-public-api-statistics-profile-reanalysis-real.json
evidence/real-data/coa-public-api-population-coverage-real.json
evidence/real-data/coa-public-api-encounter-context-real.json
evidence/real-data/coa-public-api-encounter-comparator-real.json
evidence/real-data/coa-report-encounter-source-correlation-real.json
evidence/real-data/coa-report-encounter-population-binding-real.json
```

## Request-scope provenance

Exact aggregate interpretation requires the actual request dimensions. Prepared query values may be retained only in ignored/private RawArchive observation metadata for reproducibility. Public receipts exclude them.

The API key remains excluded from RawArchive metadata entirely.

## Population semantics

The normalized model preserves documented fields exactly. The workbench may derive:

```text
local_parse_share = spec total_parses / sum(spec total_parses within the same persisted batch)
```

This is descriptive participation inside one explicit request scope. It is not evidence of the site's Tier List algorithm and not planner scoring.

## Encounter-scoped population context v1 — real proven

Implementation:

```text
src/coa_workbench/analytics/public_api_encounter_context.py
scripts/capture_public_api_encounter_context.py
```

Real result:

```text
required slices: 4
covered after: 4/4
class summaries: 59
spec records: 148
percentile values: 1924
source_endpoint_profile dependencies after run: 8
pending reanalysis: 0
actionable source changes: 0
health attention required: false
planner scoring allowed: false
```

## Matched encounter/location comparator v1 — real proven

Implementation:

```text
src/coa_workbench/analytics/public_api_encounter_comparator.py
scripts/capture_public_api_encounter_comparator.py
```

Comparator dimensions:

```text
same phase
+ same concrete difficulty
+ same location
+ same metric
+ same role
+ same bracket
+ same damage mode
+ same capture day_number
+ bossId omitted only
```

Real result:

```text
encounter context complete: true
location comparator covered: 4/4
matched records: 148
encounter-only records: 0
location-only records: 2
exact dimension match verified: true
temporal scope match verified: true
missing spec treated as zero: false
planner scoring allowed: false
mechanic semantics verified: false
site Tier List algorithm verified: false
```

Receipt:

```text
evidence/real-data/coa-public-api-encounter-comparator-real.json
```

## Comparator trust rules

```text
all dimensions except bossId must match exactly
capture day_number must match
missing spec is never coerced to zero
zero denominator yields no ratio
metric/share scalars remain private
planner scoring remains blocked
```

## Report encounter source correlation v2 — real proven

Implementation:

```text
src/coa_workbench/analytics/report_encounter_source_correlation.py
scripts/capture_report_encounter_source_correlation.py
```

Successful proof used the compact first-party encounter catalog and verified exact report/encounter identity, selected boss identity/boss flag and difficulty independently.

Receipt:

```text
evidence/real-data/coa-report-encounter-source-correlation-real.json
```

The earlier heavier `/api/reports/{reportId}/encounters/{encounterId}` site request timed out while reading the response. That remains transport evidence only and was not used for proof.

## Machine-correlated encounter population binding v1 — real proven

Implementation:

```text
src/coa_workbench/analytics/report_encounter_population_binding.py
scripts/build_report_encounter_population_binding.py
```

The binding recomputes the report-side source correlation and the exact persisted encounter-context/comparator selection from the same private operator inputs, without new acquisition.

Real source path:

```text
archived first-party report encounter catalog
+ existing persisted official /statistics batches
-> exact source correlation
-> encounter context 4/4
-> matched location comparator 4/4
-> exact dimension/day-number validation
-> scalar-safe binding review
```

Real receipt:

```text
evidence/real-data/coa-report-encounter-population-binding-real.json
```

Real result:

```text
binding version: report-encounter-population-binding-v1
archived report catalog reused: true
report catalog observation count: 1
existing public API persistence reused: true
network request count: 0
source correlation complete: true
encounter context complete: true
location comparator complete: true
differential built: true
matched records: 148
encounter-only records: 0
location-only records: 2
exact dimension match verified: true
temporal scope match verified: true
same private scope inputs reused: true
machine-correlated encounter population binding complete: true
player identity verified: false
mechanic semantics verified: false
site Tier List algorithm verified: false
planner scoring allowed: false
public release safe: true
```

This closes encounter identity/population provenance. It does not establish player identity, build evidence, mechanic semantics or roster value.

## Current next gate — player/current-build identity

The next trust lane should first reuse persisted first-party report roster/actor evidence where possible, then use pinned executable source or other stronger reviewed evidence for build semantics/freshness.

Requirements:

```text
name equality is not cross-report identity proof
current-report identity remains report-scoped unless corroborated
build observations require source + freshness/provenance
missing/stale build evidence fails closed
population aggregates do not establish individual capability
mechanic semantics remain separate
planner scoring remains blocked
```

No new `events:read` scope should be requested merely to reconfirm identity facts already available in persisted first-party report evidence.

## Event-level semantics documented by the API

The experimental schema documents, among other things:

```text
Event.id: opaque 64-bit id serialized as string
Event.timestamp_ms: milliseconds from encounter combat start
Event.amount: 64-bit value serialized as string; meaning depends on event type
Event.spell_id: -1 is the documented melee sentinel
is_glancing / is_crushing: nullable
EncounterSummary.duration_seconds: seconds
```

These contract semantics do not turn one observed event into a universal mechanic.

## Gaps in API v1.0.0

No documented endpoint was found for:

```text
Meta Builds / talents / gear / enchants
Armory
Guild progression
site Tier List algorithm
```

Those gaps use pinned client source, persisted first-party evidence or narrow fallback discovery.
