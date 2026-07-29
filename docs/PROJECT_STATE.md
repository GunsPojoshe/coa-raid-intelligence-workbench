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
commit: 37f24b12512b7486c857e9fe5199bf10a60cd777
workflow: Verify repository
run: #213
conclusion: success
Ubuntu: success
Windows: success
```

This documentation commit requires its own CI verification.

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
- verified Armory character and talent-grid mappings;
- bounded one-page public-report discovery collector;
- exact public-report structural and mapping reviews;
- completed verified public-report production gate for seven reviewed scalar fields;
- archive-only SPA API route inventory;
- inventory-gated observed report-slice capture;
- exact offline structural review for report detail, encounter detail and combatants info;
- completed scalar-free full-root report-slice mapping review;
- wildcarded candidate-path aggregation and manual scope-selection summary tooling.

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

## Completed Armory production gate

Verified mappings:

```text
config/mappings/coa_armory_character_v1.json
config/mappings/coa_armory_talent_grid_v1.json
```

Reviewer metadata:

```text
reviewed_by: GunsPojoshe (operator), OpenAI-assisted review
reviewed_at: 2026-07-29T15:34:00+03:00
```

User-local post-promotion validation:

```text
schema_version: 2
mapping_count: 2
raw_archive_count: 2
all_structurally_consistent: true
all_raw_archives_consistent: true
all_production_ready: true
```

Review decisions and deferred scopes are recorded in `docs/ARMORY_MAPPING_REVIEW_V1.md`.

## Completed public-report production gate

Observed request:

```text
GET /api/reports/public
page=1
limit=5
sortBy=created_at
sortOrder=desc
```

Exact immutable capture:

```text
HTTP: 200
payload hash: 2203e52709fad4fbc8d5235bc3699abeec6b85cf1e13b9df3e24091ddf8775c2
schema fingerprint: 4f47885820e6931cd76db538cabd68405b4969778c1bede9dee53a7f1e005ed4
```

Verified mapping:

```text
config/mappings/coa_public_report_discovery_v1.json
mapping_id: coa-public-report-discovery-v1
status: verified
collection: /reports/*
selected fields: 7
reviewed_by: GunsPojoshe (operator), OpenAI-assisted review
reviewed_at: 2026-07-29T16:41:00+03:00
production_ready: true
```

Deferred scopes:

```text
/pagination
/reports/*/guild_id
/reports/*/guild_name
/reports/*/highest_difficulty
/reports/*/locations
```

Any new payload hash or schema fingerprint requires a new review decision.

## Archived SPA route inventory

Local archive-only inventory:

```text
archive_count: 1
route_candidate_count: 24
lexically_relevant_candidate_count: 10
all_archives_verified: true
contains_source_record_scalar_values: false
semantic_verification_required: true
network_requests_performed: false
route inventory hash: f66d683319b0efc141134e5314038e8984fcd698bac083818d462ed5d1cf240f
```

Observed route shapes selected for the bounded slice:

```text
/api/reports/{template}
/api/reports/{template}/encounters/{template}
/api/reports/{template}/encounters/{template}/combatants-info
```

No separate `/roster` route was observed. `combatants-info` remains only a roster-adjacent candidate until reviewed mappings establish usable fields.

## Observed report-slice capture

All three endpoints returned HTTP 200 JSON and were archived immutably.

### Report detail

```text
route: /api/reports/{template}
payload hash: 161739896f0b8321f884bcc24d1896efb894a9c6e05166269189f9871c64cba9
schema fingerprint: 3d533a4178b67957bbd31544ddf5484bd5959635ebd5edcdd0c7689a4bace216
bytes: 3562
top-level keys: encounters, report, success, summary
```

### Encounter detail

```text
route: /api/reports/{template}/encounters/{template}
payload hash: 955437d6c9c287cc7db280dd2388b88603af2785508061b95c7811dcd272fe22
schema fingerprint: 567f36824efb37a29b835df01ce9b1fcc79eae57d6230202d16a6265c6ca0e85
bytes: 734084
top-level keys: character_stats, character_target_damage, encounter, healing_by_character, healing_targets_by_source_and_spell, rankings, success, target_damage_by_source
```

### Combatants info

```text
route: /api/reports/{template}/encounters/{template}/combatants-info
payload hash: 45672e0f0ff9eb461c575bdd38385795daa6326378bc3f8ad51474276140dc14
schema fingerprint: 41d6d15422c668f83d2ccae1ec0ff2969671861f9e43b21cb371578961c5f8ff
bytes: 637520
top-level keys: combatants, success
```

Capture boundary:

```text
route_inventory_verified: true
contains_source_scalar_values: false
semantic_verification_required: true
normalization_allowed: false
```

## Completed report-slice structural gate

User-local exact offline structural review:

```text
schema_version: 1
review_kind: observed_report_slice_structural_review
route_inventory_hash: f66d683319b0efc141134e5314038e8984fcd698bac083818d462ed5d1cf240f
raw_archive_count: 3
candidate_collection_count: 1452
all_archives_consistent: true
contains_source_scalar_values: false
semantic_verification_required: true
normalization_allowed: false
```

All three endpoint kinds were present exactly once. The structural review revalidated each payload hash, schema fingerprint, uncompressed byte count, HTTP status, content type, top-level kind and top-level keys directly against the immutable archives.

## Completed report-slice mapping review

User-local scalar-free full-root mapping review:

```text
schema_version: 1
review_kind: observed_report_slice_mapping_review
endpoint_count: 3
raw_archive_count: 3
field_path_count: 860
node_occurrence_count: 70011
numeric_map_path_count: 9
nullable_path_count: 108
array_path_count: 73
object_path_count: 112
candidate_collection_count: 1452
all_archives_consistent: true
contains_source_scalar_values: false
semantic_verification_required: true
normalization_allowed: false
ready_for_manual_mapping_review: true
```

Per endpoint:

```text
report_detail: field paths 52, nodes 168, candidate collections 2
encounter_detail: field paths 126, nodes 34987, candidate collections 533
combatants_info: field paths 682, nodes 34856, candidate collections 917
```

All endpoints remain `review_status: candidate`. No endpoint is production-ready and no normalization is enabled.

## Mapping scope-selection summary readiness

Implemented:

```text
src/coa_workbench/collector/report_slice_mapping_summary.py
scripts/summarize_observed_report_slice_mapping_review.py
tests/unit/test_report_slice_mapping_summary.py
```

The summary:

- validates mapping and structural reviews against each other;
- aggregates sampled numeric-index paths into wildcard paths such as `/combatants/*/...`;
- preserves candidate counts, observed keys, matched hints and structural scores;
- emits bounded shortlists for report, encounter, actor and aura-event review;
- does not automatically select scopes;
- keeps `can_promote: false` and `normalization_allowed: false`.

## Current blockers

1. Wildcarded candidate shortlists have not yet been reviewed locally.
2. Minimal report, encounter and combatants scopes have not been selected.
3. Exact versioned mappings for the three report-slice endpoints do not exist yet.
4. A complete report/encounter/participants slice is not normalized.
5. Evidence coverage remains narrow.
6. No corroborated gameplay mechanic is ready for canonical planner scoring.
7. Source category/filter semantics and pagination policy remain unverified.

## Next bounded tasks

1. Build the scalar-free wildcarded mapping summary locally.
2. Review top-level fields and candidate shortlists without assigning unsupported semantics.
3. Select minimal report, encounter and combatants scopes for candidate mappings.
4. Validate mappings against exact payload hashes and schema fingerprints.
5. Promote mappings manually only after review.
6. Normalize only after all required mappings are `verified`.
7. Preserve all deferred public-report scopes until separately observed and reviewed.

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
