# Official CoA Ascension Logs Public API

Status date: **2026-08-28**.

Reviewed source:

```text
https://coa.ascensionlogs.gg/api/public/v1/openapi.json
OpenAPI 3.1.0
API title: Conquest of Azeroth Logs External API
API version: 1.0.0
```

This is the preferred Ascension Logs integration whenever it exposes the required facts.

## Access model

```text
stats:read
  self-service
  aggregate statistics, phases, bosses

events:read
  experimental
  on-request
  public reports, encounter actors and combat events
```

Scope availability is a runtime capability. Documentation alone never proves a particular key has `events:read`.

Local key boundary:

```text
data/private/coa-logs-api-key.txt
fallback: COA_LOGS_API_KEY
```

The key never enters Git, request URLs, RawArchive metadata, public receipts, logs, screenshots or hashes.

## Route inventory

Unauthenticated:

```text
GET /health
GET /openapi.json
```

`stats:read`:

```text
GET /phases
GET /bosses
GET /statistics
```

Documented `events:read`:

```text
GET /reports
GET /reports/{reportId}
GET /reports/{reportId}/encounters/{encounterId}/events
GET /reports/{reportId}/encounters/{encounterId}/actors
```

## Role in the product

`stats:read` provides population/context aggregates. The workbench normalizes and stores those facts and builds its own comparisons/read models.

`events:read`, when available, can provide raw encounter facts for independent combat BI such as deaths, casts, auras, interrupts, dispels and damage/healing timelines. It is not required to reproduce Ascension Logs UI and it is not a prerequisite for the existing aggregate lane.

## `/statistics` contract

Required: `phase`.

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

Documented difficulty values: `normal`, `heroic`, `mythic`, `ascended`, `all`.

Documented metrics: `avg_dps`, `avg_hps`, `avg_dtps`.

Metric objects expose documented fields including `avg`, `median`, `max`, `min`, `total_parses` and `percentiles`.

## Request-scope provenance

Exact aggregate interpretation requires the actual request dimensions. Prepared query values may be retained only in ignored/private RawArchive observation metadata for reproducibility. Public receipts exclude them.

The API key remains excluded from RawArchive metadata entirely.

## Real-proven aggregate chain

```text
/phases + /bosses catalog
bounded provenance-aware /statistics capture
exact normalization
DuckDB persistence + deterministic replay
population-prior read model
Source Observatory + profile-scoped reanalysis
bounded population coverage v1
bounded encounter context v1
matched encounter/location comparator v1
report encounter source correlation
encounter/population provenance binding
```

Implementation anchors:

```text
migrations/0013_public_api_statistics.sql
src/coa_workbench/collector/public_api_source_health.py
scripts/capture_public_api_population_coverage.py
```

Canonical receipts are listed in `docs/DOCUMENTATION_INDEX.md`.

## Population semantics

The workbench may derive descriptive metrics such as local parse share inside one explicit persisted request scope. These values are not evidence of the site's tier-list algorithm, player capability, mechanic requirements or planner scoring.

## Event schema semantics

The experimental OpenAPI documents event fields including timestamp, event type, amount, source/target actor IDs, spell ID and outcome flags. Filters cover event groups/types, actors, spells, time range and cursor pagination.

One observed event remains an observation, not universal mechanic proof.

## Gaps in public API v1.0.0

No documented endpoint was found for:

```text
builds / talents / gear / enchants
Armory
guild progression
site tier-list algorithm
```

Those gaps may use pinned executable Companion evidence, existing first-party observations or a narrow reviewed fallback. They must not be filled by structural guesswork.
