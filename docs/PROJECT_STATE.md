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

Latest verified checkpoint before this documentation update:

```text
commit: 8d2c92404b7c155b2b2177f1ed83529c5b35aa16
workflow: Verify repository
run: #166
conclusion: success
Ubuntu: success
Windows: success
```

Documentation commits after this checkpoint require their own CI verification.

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
- scalar-free plain-text mapping summary;
- versioned public-report mapping contract;
- exact public-report raw-archive selector validation;
- verified public-report discovery mapping for seven reviewed scalar fields.

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

Per-mapping exact raw validation:

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

Review decisions and deferred scopes are recorded in `docs/ARMORY_MAPPING_REVIEW_V1.md`.

## Real bounded report discovery

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
content type: application/json
payload hash: 2203e52709fad4fbc8d5235bc3699abeec6b85cf1e13b9df3e24091ddf8775c2
schema fingerprint: 4f47885820e6931cd76db538cabd68405b4969778c1bede9dee53a7f1e005ed4
duplicate payload: false
duplicate observation: false
top-level keys: pagination, reports, success
candidate collections: 6
```

Structural review:

```text
schema_version: 1
review_kind: report_discovery_structural_review
archive_verified: 1
all archive comparisons: true
category_semantics_verified: false
pagination_policy_verified: false
```

Exact scalar-free mapping review and summary:

```text
review_kind: report_discovery_mapping_review
summary_kind: report_discovery_mapping_summary
field_path_count: 24
node_occurrence_count: 84
numeric_map_path_count: 0
candidate_collection_count: 6
array_path_count: 2
nullable_path_count: 3
report_field_count: 11
contains_source_scalar_values: false
ready_for_manual_mapping_review: true
```

The only report-like collection is `/reports`, with five object items. The reviewed bounded item selector is `/reports/*`. The other five candidate collections are the non-object `locations` arrays under those reports.

All eleven source keys were present on all five report objects:

```text
created_at
end_time
guild_id
guild_name
highest_difficulty
id
locations
start_time
title
uploader_username
visibility
```

Nullable observations:

```text
/reports/*/guild_id                         null x 5
/reports/*/guild_name                       null x 5
/reports/*/highest_difficulty/trial_level   null x 5
```

The five returned objects prove only that this one response matched the requested `limit=5`; consistent limit enforcement is not established.

## Completed public-report production gate

Verified mapping:

```text
config/mappings/coa_public_report_discovery_v1.json
mapping_id: coa-public-report-discovery-v1
status: verified
collection: /reports/*
selected fields: 7
reviewed_by: GunsPojoshe (operator), OpenAI-assisted review
reviewed_at: 2026-07-29T16:41:00+03:00
```

Selected fields:

```text
source_report_id
created_at
start_time
end_time
title
visibility
uploader_username
```

Deferred scopes:

```text
/pagination
/reports/*/guild_id
/reports/*/guild_name
/reports/*/highest_difficulty
/reports/*/locations
```

User-local post-promotion exact-archive validation:

```text
mapping_id: coa-public-report-discovery-v1
status: verified
all_structurally_consistent: true
all_raw_archive_selectors_consistent: true
route_matched: true
raw_payload_validated: true
report_item_count: 5
field_contract_count: 7
extracted_value_count: 35
nullable_value_count: 0
production_ready: true
can_promote: false
contains_source_scalar_values: false
```

`can_promote: false` remains correct: automatic promotion is forbidden, while the manual promotion is complete and documented.

Review decisions and interpretation boundaries are recorded in `docs/REPORT_DISCOVERY_MAPPING_REVIEW_V1.md`.

Any new payload hash or schema fingerprint requires a new review decision.

Implemented public-report files include:

```text
config/mappings/coa_public_report_discovery_v1.json
docs/REPORT_DISCOVERY_MAPPING_REVIEW_V1.md
src/coa_workbench/collector/report_discovery.py
src/coa_workbench/collector/report_discovery_review.py
src/coa_workbench/collector/report_discovery_mapping_review.py
src/coa_workbench/collector/report_discovery_mapping_summary.py
src/coa_workbench/collector/report_discovery_mapping_text.py
src/coa_workbench/normalizer/report_discovery_mapping.py
scripts/capture_report_discovery.py
scripts/review_report_discovery.py
scripts/build_report_discovery_mapping_review.py
scripts/summarize_report_discovery_mapping_review.py
scripts/validate_report_discovery_mapping.py
tests/unit/test_report_discovery.py
tests/unit/test_report_discovery_review.py
tests/unit/test_report_discovery_mapping_review.py
tests/unit/test_report_discovery_mapping_summary.py
tests/unit/test_report_discovery_mapping_text.py
tests/unit/test_report_discovery_mapping.py
```

The review, summary and validation outputs contain only structural counts, paths, JSON types and reproducibility identifiers. They do not emit report IDs, names, timestamps or other source scalar values.

Still unverified:

- consistent enforcement of the requested limit across observations;
- meaning of source category/filter fields;
- whether additional pages exist;
- source pagination metadata and stopping rules;
- deterministic cross-page/category selection;
- guild field semantics;
- highest-difficulty and trial-level semantics;
- location value semantics.

`local_category` is only a local label. It must not be treated as a source-supported category.

## Current blockers

1. Source category/filter semantics and pagination policy remain unverified.
2. Encounter/roster discovery for a complete report slice is not established.
3. A complete report/encounter/roster slice is not normalized.
4. Evidence coverage remains narrow.
5. No corroborated gameplay mechanic is ready for canonical planner scoring.
6. `docs/PROJECT_MASTER_CONTEXT.md` contains historical sections and must not override this operational state without code verification.

## Next bounded tasks

1. Investigate filters/categories/pagination only through separate explicit observations.
2. Discover an encounter or roster route only from observed application behavior; do not invent routes.
3. Capture one bounded report/encounter/roster slice immutably.
4. Build scalar-free structural and mapping review for that slice.
5. Create and validate exact versioned mappings.
6. Normalize only after the exact mappings are verified.
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
