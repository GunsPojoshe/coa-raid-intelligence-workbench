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
commit: 2ec8b46109685c44b688734a4b8c9e95d46aa17b
workflow: Verify repository
run: #184
conclusion: success
Ubuntu: success
Windows: success
```

Не считать HEAD и CI status из документа вечными.

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
- verified Armory character and talent-grid mappings;
- verified public-report discovery mapping for seven reviewed scalar fields;
- archived-SPA route inventory with exact gzip/hash/byte verification;
- inventory-gated progressive report/encounter/combatants capture tooling.

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

## Completed public-report production gate

Verified mapping:

```text
config/mappings/coa_public_report_discovery_v1.json
mapping_id: coa-public-report-discovery-v1
status: verified
collection: /reports/*
selected fields: 7
```

Final user-local exact-archive result:

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

User-local inventory verified one immutable SPA asset and found 24 API route shapes. Ten were lexically relevant to report/encounter discovery.

Observed shapes selected for the next bounded slice:

```text
/api/reports/{template}
/api/reports/{template}/encounters/{template}
/api/reports/{template}/encounters/{template}/combatants-info
```

These are observed frontend literals only. Route names do not prove payload semantics.

Inventory result:

```text
archive_count: 1
route_candidate_count: 24
lexically_relevant_candidate_count: 10
all_archives_verified: true
contains_source_record_scalar_values: false
semantic_verification_required: true
network_requests_performed: false
```

## Inventory-gated observed report slice capture

Implemented:

```text
src/coa_workbench/collector/report_slice_capture.py
scripts/capture_observed_report_slice.py
tests/unit/test_report_slice_capture.py
```

The capture contract:

1. requires the exact local SPA route inventory before any network request;
2. refuses capture if any of the three observed route shapes is absent;
3. uses one persistent `coa-fetch-context-v1` same-origin session;
4. captures report detail, encounter detail and combatants-info sequentially;
5. writes progressive safe output after each endpoint;
6. archives completed response bodies before JSON interpretation;
7. outputs route templates, hashes, fingerprints, byte counts and top-level shapes only;
8. never emits report/encounter IDs or payload source scalar values in the safe manifest;
9. keeps `semantic_verification_required: true`;
10. keeps `normalization_allowed: false` until structural review and verified mappings exist.

## Real aura checkpoint

Report `2987`, spell `968746`.

```text
encounter 64795:
  canonical events: 6
  reconstructed intervals: 3
  reference intervals: 3
  rejects: 0
  anomalies: 0

encounter 64796:
  canonical events: 3
  reconstructed intervals: 2
  reference intervals: 2
  rejects: 0
  anomalies: 0
```

This confirms technical behavior of the normalizer/Aura State Engine, not numeric/runtime gameplay semantics.

## Still unverified

- category/filter semantics;
- consistent enforcement of public-report `limit=5`;
- additional-page existence and pagination stopping rules;
- deterministic cross-page selection;
- guild, difficulty and location semantics;
- actual payload structures and semantics for the three newly selected route shapes;
- a complete verified report/encounter/roster normalization slice;
- corroborated gameplay mechanics for planner scoring.

## Current blockers

1. Run the inventory-gated observed report slice capture locally.
2. Build scalar-free structural reviews for each successful immutable response.
3. Create exact versioned candidate mappings from reviewed structures.
4. Validate selectors against exact archives and manually promote only reviewed fields.
5. Normalize one complete report/encounter/combatants slice.
6. Expand supporting and contradicting evidence coverage.
7. `docs/PROJECT_MASTER_CONTEXT.md` contains historical sections and must not override this operational state without code verification.

## Next bounded tasks

1. Capture report `2987`, encounter `64795` through the three observed route shapes.
2. Review only transport facts, hashes, fingerprints and top-level structures from the safe output.
3. Build endpoint-specific scalar-free structural review tooling.
4. Do not normalize any new response before exact mappings are verified.
5. Preserve all public-report deferred scopes until separately observed and reviewed.

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
