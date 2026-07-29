# Фактическое состояние проекта

Дата актуализации: 2026-07-29.

Главный контекст:

```text
docs/PROJECT_MASTER_CONTEXT.md
```

Этот документ фиксирует изменяемое operational state. Перед работой проверять GitHub, код и CI заново.

## Репозиторий

- repository: `GunsPojoshe/coa-raid-intelligence-workbench`;
- default branch: `main`;
- evidence branch: `e2/log-evidence-refactor`;
- active capture branch: `e3/real-log-capture`;
- PR #3: `e2/log-evidence-refactor -> main`, Draft;
- PR #7: `e3/real-log-capture -> e2/log-evidence-refactor`, Draft;
- PR #8 safe HAR inventory merged into PR #7;
- latest verified branch head: `7772eac950e005f93b28d5b90bb6935f04a3da74`;
- latest verified workflow: `Verify repository`, run #119, success.

Не доверять commit count, HEAD или CI status из документа без проверки.

## Реализованный фундамент

- localhost FastAPI application;
- browser raid constructor FLEX / 10 / 25 / 40;
- DuckDB raid-plan persistence;
- immutable raw archive;
- separate observations and deduplicated payload bodies;
- source registry;
- JSON/HAR import;
- safe HAR inventory;
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
- candidate Armory mapping contracts;
- type-only and raw-archive mapping validation gates.

## Real aura checkpoint

Report `2987`, spell `968746`:

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

## HTTP access finding

Полный same-origin profile возвращал HTTP 200 для:

- `/api/reports/public`;
- `/api/characters/search`;
- `/api/armory/by-name/...`;
- `/api/armory/character/156120`;
- `/api/armory/talent-grid/felsworn`.

Не доказано:

- минимальное подмножество headers;
- обязательность cookie;
- request-order dependency;
- Armory-first behavior в completely fresh session.

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

## Mapping review checkpoint

Review packet schema `2`:

```text
archive_verified: 2
field_path_count: 470
node_occurrence_count: 6106
numeric_map_path_count: 4
contains_source_scalar_values: false
ready_for_manual_mapping_review: true
```

Candidate mappings:

- `config/mappings/coa_armory_character_v1.json`;
- `config/mappings/coa_armory_talent_grid_v1.json`.

Documented review:

```text
docs/ARMORY_MAPPING_REVIEW_V1.md
```

Review corrections:

- source `cao_id` retained as `source_cao_id`;
- source `bisbeard_tree` retained as `source_bisbeard_tree`;
- talent records preserve parent tree;
- connections preserve source talent and tree;
- rank texts preserve source talent and tree;
- empty `lock_rules` and `rank_spell_ids` item schemas remain deferred.

Candidate mappings remain blocked by `require_verified()`.

## Mapping validation gates

### Completed type-only validation

User-local result against the real review packet:

```text
all_structurally_consistent: true
all_production_ready: false
mapping_count: 2
character: 19 singletons, 5 collections, 36 fields
talent_grid before review refinement: 2 singletons, 4 collections, 17 fields
```

After review refinement the talent-grid mapping contains 22 fields because parent tree/talent relations are now explicit.

### Implemented raw-archive validation

The validator checks the exact immutable gzip archives:

- payload hash;
- schema fingerprint;
- route template;
- singleton selectors;
- collection occurrence counts;
- `@item`, `@index` and `@ancestor[n]` selectors;
- required field presence and JSON types.

The local real-archive run is still pending. Until it passes, mappings remain `candidate`.

Expected result before promotion:

```text
all_structurally_consistent: true
all_raw_archives_consistent: true
all_production_ready: false
```

## Tests and CI

Latest verified checkpoint:

```text
commit: 7772eac950e005f93b28d5b90bb6935f04a3da74
workflow: Verify repository
run: #119
conclusion: success
Ubuntu repository verifier: success
Windows pytest/doctor/DuckDB initialization: success
full pytest: 96 passed, 1 warning
```

The verifier uses `ruff format --diff`, so formatting failures include the exact formatter patch.

## Local environment caveat

A previous local `uv sync --frozen --extra dev` attempted to build Ruff from source and failed because MSVC `link.exe` was unavailable.

Targeted commands through `uv run --no-sync` work. Do not require Visual Studio Build Tools without a separate dependency-resolution diagnosis.

## Current blockers

1. Real raw-archive selector validation has not yet been executed on the user's private archives.
2. Armory mappings remain `candidate`, not `verified`.
3. Bounded report discovery filters and pagination are not reviewed.
4. A complete report/encounter/roster slice is not normalized.
5. Evidence coverage remains narrow.
6. No corroborated gameplay mechanic is ready for canonical planner scoring.

## Next bounded tasks

1. Run raw-archive validation locally.
2. Review the compact validation result.
3. Promote only structurally validated mappings through a separate explicit change.
4. Implement bounded report discovery, default up to 5 reports/category.
5. Review filters and pagination on real observations/frontend behavior.
6. Normalize one complete report/encounter/roster slice.
7. Expand supporting and contradicting evidence.
8. Integrate only corroborated/confirmed mechanics into planner scoring.

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
- green Ubuntu and Windows verification.
