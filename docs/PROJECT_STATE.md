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

Latest verified checkpoint:

```text
commit: 6053ea3f6d3f933026f88d67f398d4a2d92b0a3a
workflow: Verify repository
run: #193
conclusion: success
Ubuntu: success
Windows: success
```

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
- completed verified public-report production gate for seven reviewed scalar fields;
- archive-only SPA API route inventory;
- inventory-gated observed report-slice capture;
- exact report-slice structural review implementation.

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

User-local post-promotion exact-archive validation:

```text
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

Deferred scopes remain:

```text
/pagination
/reports/*/guild_id
/reports/*/guild_name
/reports/*/highest_difficulty
/reports/*/locations
```

## Archived SPA route inventory

User-local archive-only inventory:

```text
schema_version: 1
inventory_kind: archived_spa_api_route_inventory
archive_count: 1
route_candidate_count: 24
lexically_relevant_candidate_count: 10
all_archives_verified: true
contains_source_record_scalar_values: false
semantic_verification_required: true
network_requests_performed: false
```

Observed route shapes used for the bounded report slice:

```text
/api/reports/{template}
/api/reports/{template}/encounters/{template}
/api/reports/{template}/encounters/{template}/combatants-info
```

A route name is not proof of payload semantics. No separate `/roster` route was observed in this archived asset.

## Observed report-slice capture

The inventory-gated local capture completed all three observed endpoints with HTTP 200 and JSON bodies.

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
```

The console line containing the encounter top-level keys was truncated. Exact keys must be read from the saved compact capture manifest and verified against the immutable archive; they must not be reconstructed from the truncated console output.

### Combatants info

```text
route: /api/reports/{template}/encounters/{template}/combatants-info
payload hash: 45672e0f0ff9eb461c575bdd38385795daa6326378bc3f8ad51474276140dc14
schema fingerprint: 41d6d15422c668f83d2ccae1ec0ff2969671861f9e43b21cb371578961c5f8ff
bytes: 637520
top-level keys: combatants, success
```

Capture guarantees:

```text
route_inventory_verified: true
route_inventory_hash: f66d683319b0efc141134e5314038e8984fcd698bac083818d462ed5d1cf240f
http_profile_version: coa-fetch-context-v1
contains_source_scalar_values: false
normalization_allowed: false
```

Implemented offline structural review:

```text
src/coa_workbench/collector/report_slice_review.py
scripts/review_observed_report_slice.py
tests/unit/test_report_slice_review.py
```

The review validates the exact inventory hash, required route set, all three payload hashes, schema fingerprints, byte counts, HTTP/content-type consistency and top-level shapes. It emits no report, encounter, player or combatant scalar values.

## Current blockers

1. Exact local structural review of the three new archives must complete.
2. Scalar-free mapping-review packets for report detail, encounter detail and combatants info are not built.
3. Exact versioned mappings for the new schemas are not reviewed or verified.
4. A complete report/encounter/roster slice is not normalized.
5. Source category/filter semantics and pagination policy remain unverified.
6. Evidence coverage remains narrow.
7. No corroborated gameplay mechanic is ready for canonical planner scoring.
8. `docs/PROJECT_MASTER_CONTEXT.md` contains historical sections and must not override this operational state without code verification.

## Next bounded tasks

1. Run the offline structural review against the exact local archives.
2. Build scalar-free mapping-review packets only after structural consistency is confirmed.
3. Review exact report, encounter and combatants mappings.
4. Normalize only after mappings are explicitly promoted to `verified`.
5. Preserve all deferred public-report and gameplay-semantic scopes.

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
