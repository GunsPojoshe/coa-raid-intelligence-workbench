# Фактическое состояние проекта

Дата актуализации: 2026-07-29.

Этот документ фиксирует изменяемое operational state. Перед работой всегда перепроверять GitHub, код и CI.

## Репозиторий

```text
repository: GunsPojoshe/coa-raid-intelligence-workbench
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

Latest verified code checkpoint before this documentation update:

```text
commit: 0190937d6ba9364ef88ad03e164964fd18415ba7
workflow: Verify repository
run: #126
conclusion: success
Ubuntu: success
Windows: success
```

Documentation commits follow that code checkpoint. Не считать HEAD и CI status из документа вечными.

## Реализованный фундамент

- localhost FastAPI application;
- browser raid constructor FLEX / 10 / 25 / 40;
- DuckDB raid-plan persistence;
- immutable raw archive;
- separate observations and deduplicated payload bodies;
- source registry;
- JSON/HAR import and safe inventory;
- schema fingerprints;
- verified normalization mapping gate;
- canonical report/encounter/actor/participant/aura records;
- Aura State Engine;
- hypotheses and supporting/contradicting evidence;
- trust and weighting policies;
- migrations `0001`–`0006`;
- repository verifier and Ubuntu/Windows CI;
- SPA/asset capture and frontend route discovery;
- versioned HTTP profile `coa-fetch-context-v1`;
- persistent same-origin session with in-memory cookie jar;
- timeout/retry/incomplete-response handling;
- endpoint-isolated progressive/resumable Armory capture;
- structural review and mapping-review packet schema v2;
- raw-archive selector validation;
- verified Armory character and talent-grid mappings.

## Trust boundary

Normalization разрешена только при:

```text
immutable archived payload
+ exact SHA-256
+ exact schema fingerprint
+ reviewed mapping
+ mapping status verified
```

Verified schema/parser compatibility не является подтверждением игровой механики. В planner scoring допускаются только corroborated/confirmed mechanics.

## Real aura checkpoint

Report `2987`, spell `968746`.

### Encounter 64795

```text
fingerprint: 2994424cb95c2a7e1997651226b7942367ebe77003e0f4614aae5da4920f8b98
mapping: coa-aura-timeline-single-encounter-v1
mapping status: verified
canonical events: 6
reconstructed intervals: 3
reference intervals: 3
rejects: 0
anomalies: 0
```

### Encounter 64796

```text
window: 10382-38265 ms
full duration: 117215 ms
fingerprint: d8b6dd869d6adf8f3433f9e285b8270cd1aa8d640839c915a42c80b2211cbf0b
canonical events: 3
reconstructed intervals: 2
reference intervals: 2
rejects: 0
anomalies: 0
```

Это подтверждает technical behavior normalizer/Aura State Engine, но не numeric/runtime mechanic `Ninja's Focus`.

## Real Armory capture

Subject:

```text
character_id: 156120
class_slug: felsworn
profile: coa-fetch-context-v1
```

### Character

```text
route: /api/armory/character/156120
HTTP: 200
bytes: 59910
payload hash: 2a9d752d7af72d41cd9d41836d670069c78e408df7260f5d9caa83b07430985f
fingerprint: efbcf618291d824667ba586c22af4ed031fa146d69b11a5539ec17a41d042621
keys: capture, ci_resolved, stats_summary, success
```

### Talent grid

```text
route: /api/armory/talent-grid/felsworn
HTTP: 200
bytes: 63025
payload hash: 11be25407ec00898547c1b7f342d4596268b3164df9fe0f120bb911559cc5206
fingerprint: 7e3b3bfc3966ddc5d0160c8d466e5ba92edbe55440449619d7204102a25b3240
keys: class_name, success, trees
```

Raw payloads и local review/validation outputs остаются gitignored.

## Armory mapping review

Review packet schema `2`:

```text
archive_verified: 2
field_path_count: 470
node_occurrence_count: 6106
numeric_map_path_count: 4
contains_source_scalar_values: false
ready_for_manual_mapping_review: true
```

Verified mappings:

```text
config/mappings/coa_armory_character_v1.json
config/mappings/coa_armory_talent_grid_v1.json
```

Review document:

```text
docs/ARMORY_MAPPING_REVIEW_V1.md
```

Review decisions:

- source `cao_id` retained as `source_cao_id`;
- source `bisbeard_tree` retained as `source_bisbeard_tree`;
- talent records preserve parent tree;
- connections preserve source talent and tree;
- rank texts preserve source talent and tree;
- empty `lock_rules` and `rank_spell_ids` item schemas remain deferred;
- detailed gear, hero build and computational stat internals remain deferred.

Reviewer metadata:

```text
reviewed_by: GunsPojoshe (operator), OpenAI-assisted review
reviewed_at: 2026-07-29T15:34:00+03:00
```

## Completed raw-archive validation

User-local validation against the exact private archives:

```text
schema_version: 2
mapping_count: 2
raw_archive_count: 2
all_structurally_consistent: true
all_raw_archives_consistent: true
all_production_ready: false
```

The run was executed before promotion, so `all_production_ready: false` was expected.

Per-mapping result:

```text
coa-armory-character-v1
  raw_payload_validated: true
  route_matched: true
  singleton_value_count: 19
  extracted_value_count: 328

coa-armory-talent-grid-v1
  raw_payload_validated: true
  route_matched: true
  singleton_value_count: 2
  extracted_value_count: 2955
```

After pulling the promotion commits, a repeated local run must return:

```text
all_structurally_consistent: true
all_raw_archives_consistent: true
all_production_ready: true
```

Any new payload hash or fingerprint requires a new review decision.

## Current blockers

1. Bounded report discovery filters and pagination are not reviewed.
2. Default report limits are not implemented/verified against real behavior.
3. A complete report/encounter/roster slice is not normalized.
4. Evidence coverage remains narrow.
5. No corroborated gameplay mechanic is ready for canonical planner scoring.
6. `docs/PROJECT_MASTER_CONTEXT.md` still contains older historical sections and must not override this operational state without code verification.

## Next bounded tasks

1. Inspect existing report discovery code and frontend observations.
2. Implement bounded report discovery with default up to 5 reports per category.
3. Verify filters and pagination only from observed source behavior.
4. Archive one deterministic discovery result.
5. Select and normalize one complete report/encounter/roster slice.
6. Expand supporting and contradicting evidence.
7. Integrate only corroborated/confirmed mechanics into planner scoring.

## Completion gate

PR #3 and PR #7 remain Draft until the relevant evidence checkpoint is complete:

- real immutable payloads;
- stable fingerprints;
- reviewed verified mappings;
- normalized report/encounter/actors/participants/aura events;
- reconstructed intervals;
- independent supporting observations;
- contradicting evidence review;
- reproducible versioned output;
- provenance;
- green Ubuntu and Windows verification.
