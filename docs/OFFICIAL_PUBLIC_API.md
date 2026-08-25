# Official CoA Ascension Logs Public API

Status date: **2026-08-25**.

Reviewed source:

```text
https://coa.ascensionlogs.gg/api/public/v1/openapi.json
OpenAPI 3.1.0
API title: Conquest of Azeroth Logs External API
API version: 1.0.0
```

This source is now preferred over frontend reverse engineering whenever the documented public API
covers the same information.

## Access model

The published contract separates two scopes:

```text
stats:read
  availability: self-serve
  purpose: aggregate class/spec statistics, phases, bosses

events:read
  availability: on-request
  experimental: true
  purpose: one-encounter-at-a-time combat events and actor dictionaries
```

Published tiers include:

```text
free:     30 requests/minute, 5,000/day, stats:read
partner: 120 requests/minute, 50,000/day, stats:read
research: 60 requests/minute, 10,000/day, stats:read + events:read
```

API keys are documented for request headers only:

```text
Authorization: Bearer <key>
X-API-Key: <key>
```

The contract explicitly says keys are not accepted in the query string. The workbench must never
persist a key value in RawArchive metadata, receipts, request URLs, Git, logs, or screenshots.

The published access text also requires visible attribution linking back to Ascension Logs when API
data is displayed publicly and says bulk redistribution of the dataset is not permitted. The
workbench therefore treats API-derived raw data as local evidence and does not publish bulk source
payloads.

## Documented route inventory

Unauthenticated:

```text
GET /health
GET /openapi.json
```

Self-serve `stats:read`:

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

The local reviewed registry is:

```text
config/coa_public_api_sources.yaml
source_code = coa_ascension_logs_public_api
base_url = https://coa.ascensionlogs.gg/api/public/v1
```

`stats:read` routes are marked production-ready at the contract level. `events:read` routes remain
reviewed/experimental and are not production-ready by default even though the route shapes are
officially documented.

## High-value aggregate statistics contract

`GET /statistics` requires `phase` and documents these optional query dimensions:

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

Documented role filter values:

```text
tank
dps
tanks-and-dps
support
```

The response contains class-level aggregates and per-spec:

```text
avg
median
max
min
total_parses
percentiles
```

This makes the public API the preferred source for population performance priors. `total_parses`
can support a workbench-derived participation/popularity signal, but it is **not** promoted as the
site's Meta Tier List popularity algorithm. The OpenAPI contract does not document that algorithm.

## Event-level semantics documented by the API

The experimental event schema is unusually valuable because it publishes several semantics that
were previously uncertain:

```text
Event.id
  64-bit id serialized as a string; treat as opaque

Event.timestamp_ms
  integer milliseconds from encounter combat start, not wall clock

Event.amount
  64-bit value serialized as a string; meaning depends on event_type

Event.spell_id
  -1 is the published melee sentinel

is_glancing / is_crushing
  nullable; null can mean not recorded and is not evidence of mechanic absence

EncounterSummary.duration_seconds
  integer-or-null duration field explicitly named in seconds
```

The event endpoint also documents raw event groups, melee-only filtering, actor source/target
filters, spell filters, start/end millisecond offsets, and keyset pagination. Actor IDs are resolved
through the separate `/actors` dictionary.

This is strong source-contract evidence. It still does not make one encounter observation proof of
a universal gameplay mechanic.

## Important gaps in public API v1.0.0

The reviewed OpenAPI path inventory contains **no documented endpoint** for:

```text
Meta Builds / talents / gear / enchants
Armory
Guild progression
site Tier List algorithm
```

Therefore the public API does not replace the pinned Companion source, current report observations,
or selected frontend/source discovery for those surfaces.

Current source priority becomes:

```text
1. official documented public API
2. official documented site semantics
3. pinned executable AscensionLogsCompanion source
4. persisted first-party report responses
5. narrow browser/network observation for undocumented gaps
6. structural inference only after the stronger sources are exhausted
```

## Relationship to the old difficulty blocker

The real `difficulty-sequence-binding-v3` receipt over the existing two-report corpus produced:

```text
unique full sequence alignments:    0
ambiguous full sequence alignments: 1
no full sequence alignment:         1
sequence-linked pulls:              0
status: insufficient_evidence
```

That line of investigation remains valid evidence but is no longer the highest-value next step.
The official `/statistics` endpoint already exposes an explicit documented `difficulty` dimension
for aggregate cohorts, so population analytics no longer needs to wait for cross-report difficulty
equivalence of the two historical reports.

The historical two-report corpus remains useful for local raw/report-specific analytics and for
corroborating source behavior. Numeric comparison between those two reports remains blocked until
its own equivalence gate is proven.

## Deterministic contract review

Implementation:

```text
src/coa_workbench/collector/public_api_contract.py
scripts/review_public_api_contract.py
tests/unit/test_public_api_contract.py
config/coa_public_api_sources.yaml
```

The reviewer consumes a local copy of the official OpenAPI JSON and produces only public contract
metadata: route templates, parameter names, enums, scope counts, documented units/types, access
rules, and registry consistency. It does not require an API key and does not make a network request.

Example:

```powershell
uv run --no-sync python scripts/review_public_api_contract.py `
  --input data/exchange/in/coa-public-api-openapi.json `
  --output data/exchange/out/coa-public-api-contract.json
```

## Next implementation gate

After the contract layer is green:

```text
self-serve API key stored only in local environment
-> capture /phases + /bosses through RawArchive
-> one bounded /statistics slice
-> parser/schema verification
-> aggregate statistics persistence
-> derive population priors by explicit phase/difficulty/content/role/metric dimensions
```

No `events:read` request is required for this next gate. Event-level access can be considered later
for mechanics research if the project receives that scope explicitly.
