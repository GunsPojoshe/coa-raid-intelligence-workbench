# Current Report Analytics localhost API

Status: **typed local/private read surface implemented**.

The API exposes the persisted `current-report-comparison-read-model-v1` through FastAPI without
performing network requests or mutating analytical observations.

## Routes

```text
GET /api/current-report-analytics/reports
GET /api/current-report-analytics/latest
GET /api/current-report-analytics/reports/{report_id}
```

`/reports` lists locally persisted reports that already have a completed
`current-report-analytics-persistence-v1` run.

`/latest` returns the latest available comparison read model.

`/reports/{report_id}` selects one canonical local report identifier.

## Typed response surface

The detail response preserves the current structural boundaries:

```text
report
players
throughput_profiles
summary
interpretation
```

Throughput rows expose the exact observed ordering already established by the comparison read model:

```text
one report
-> one encounter
-> one exact request profile
-> roster-matched rows
-> upstream characters[].total_amount ordering
```

This is an observed comparison surface, not a performance grade.

Healing joins remain based on explicit character-ID fields.

Damage-taken joins remain exact-key matches only. The API does not claim that the dynamic damage group
key has verified target-ID semantics.

## Safety boundary

The route installer fails closed if the read model unexpectedly stops being explicitly local/private
or if planner scoring is promoted.

The detail payload is intentionally private and can contain local report/player IDs and names:

```text
local_private_payload = true
public_release_safe = false
```

Do not publish API responses as evidence receipts.

The API does not:

```text
perform browser/network collection
modify Source Observatory captures
create analytics observations
promote mechanic semantics
assign performance grades
enable planner scoring
```

## Product role

This is the first stable localhost product surface over the real persisted combat analytics corpus.
It is intended to feed the local UI and later cross-report benchmark models without forcing those
consumers to query `canonical_entity_observation` directly.
