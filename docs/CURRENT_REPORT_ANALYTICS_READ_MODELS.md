# Current report analytics read models

Status date: **2026-08-14**.

## Purpose

This layer turns the already captured current-report browser responses into deterministic local
read-model observations for:

```text
throughput timeline
spell healing
damage taken by ability
```

It does not infer mechanics, player value, build quality, rankings, or planner-scoring eligibility.

## Input boundary

The parser consumes the existing `CurrentReportHarSlice` and the already reviewed current roster
parser result. No network requests are performed.

Current source families:

```text
GET /api/reports/{reportId}
GET /api/reports/{reportId}/encounters
GET /api/reports/{reportId}/combatants-roster
GET /api/reports/{reportId}/encounters/{encounterId}/throughput-timeline
GET /api/reports/{reportId}/character_damage_taken_abilities
GET /api/reports/{reportId}/character_spell_healing
```

Every source response must already exist as a `schema_candidate` Source Observatory capture at the
exact HAR observation timestamp before persistence is allowed.

## Deterministic observations

The v1 parser emits:

```text
current_throughput_request_observation
current_throughput_character_observation
current_throughput_point_observation
current_damage_taken_ability_observation
current_healing_spell_observation
current_healing_source_breakdown_observation
current_healing_target_breakdown_observation
```

All rows are persisted through `canonical_entity_observation` with stable IDs, source-capture
provenance and one completed `analysis_run`.

The main current payload dictionaries use dynamic source keys. Those keys are retained only as
opaque grouping keys. The parser does not assume they represent character, spell, target, or actor
identity. A throughput series key is linked to a character only when it exactly equals a
`characters[].character_id` from the same response.

## Cross-source checks

Before persistence the parser verifies:

```text
all analytics responses belong to one report path scope
throughput encounter IDs exist in the current encounter catalog
damage/healing payload report_id agrees with the request path when present
throughput character IDs are compared with the current roster without requiring a match
healing source character IDs are compared with the current roster without requiring a match
```

Roster matches are structural joins only. They do not establish gameplay semantics.

## Scoped reanalysis

The analytics artifact depends on all six source families above through:

```text
dependency_type = source_endpoint_scope
scope_path_keys = [reportId]
```

A later source change can therefore target only the analytics artifact for the affected private
report scope. Report IDs and scope fingerprints remain local/private.

## Public/private boundary

Public command output exposes counts and endpoint codes only. It excludes:

```text
HAR/body content
report/encounter/character IDs
character names
query values
dynamic grouping keys
source-capture IDs
source-scope values/fingerprints
input/output fingerprints
```

## Trust boundary

```text
read_model_only: true
mechanic_semantics_verified: false
planner_scoring_allowed: false
```

A separate evidence-backed semantic layer is required before any of these observations can influence
raid-planner scoring.
