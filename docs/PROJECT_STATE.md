# Фактическое состояние проекта

Дата актуализации: 2026-07-29.

Главный архитектурный контекст: `docs/PROJECT_MASTER_CONTEXT.md`.

Этот документ фиксирует изменяемое operational state. Перед работой заново проверять GitHub, код, CI и локальные данные.

## Репозиторий

- repository: `GunsPojoshe/coa-raid-intelligence-workbench`;
- default branch: `main`;
- evidence branch: `e2/log-evidence-refactor`;
- active branch: `e3/real-log-capture`;
- PR #3: `e2/log-evidence-refactor -> main`, Draft;
- PR #7: `e3/real-log-capture -> e2/log-evidence-refactor`, Draft;
- current verified PR #7 head for this checkpoint: `787ce2e35d66df7752ad7f9b1b6c83518bf68e40`.

Не доверять HEAD, commit count или CI status из документа без повторной проверки.

## Реализованный фундамент

- localhost FastAPI application и browser raid constructor;
- DuckDB raid-plan persistence;
- immutable content-addressed raw archive;
- observations отдельно от deduplicated payload bodies;
- JSON/HAR import и privacy-safe HAR inventory;
- schema fingerprints;
- verified normalization gate;
- canonical report/encounter/actor/participant/aura records;
- Aura State Engine;
- hypotheses и supporting/contradicting evidence;
- trust и weighting policies;
- migrations `0001`–`0006`;
- repository verifier и Ubuntu/Windows CI;
- SPA/asset discovery;
- versioned HTTP profile `coa-fetch-context-v1`;
- persistent same-origin session с in-memory cookie jar;
- bounded timeout/retry/incomplete-response handling;
- endpoint-isolated progressive/resumable Armory capture;
- structural Armory review и type-only mapping review packet;
- candidate Armory mapping contracts с production gate.

## Real aura checkpoint

Report `2987`, spell `968746`.

### Encounter 64795

```text
fingerprint: 2994424cb95c2a7e1997651226b7942367ebe77003e0f4614aae5da4920f8b98
mapping: coa-aura-timeline-single-encounter-v1, verified
canonical events: 6
reconstructed intervals: 3
reference intervals: 3
rejects: 0
anomalies: 0
```

### Encounter 64796

```text
window: 10382–38265 ms
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

Полный same-origin profile `coa-fetch-context-v1` возвращал HTTP 200 для public reports, character search, Armory by-name и endpoint-isolated Armory endpoints.

Не доказано:

- минимальное подмножество headers;
- обязательность cookie;
- независимость от request order;
- Armory-first behavior в completely fresh session.

## Real Armory checkpoint

Subject:

```text
character_id: 156120
character_class: Felsworn
realm: Vol'Jin
class_slug: felsworn
http_profile_version: coa-fetch-context-v1
```

### character

```text
route: /api/armory/character/156120
HTTP: 200
bytes: 59910
payload hash: 2a9d752d7af72d41cd9d41836d670069c78e408df7260f5d9caa83b07430985f
fingerprint: efbcf618291d824667ba586c22af4ed031fa146d69b11a5539ec17a41d042621
keys: capture, ci_resolved, stats_summary, success
```

### talent_grid

```text
route: /api/armory/talent-grid/felsworn
HTTP: 200
bytes: 63025
payload hash: 11be25407ec00898547c1b7f342d4596268b3164df9fe0f120bb911559cc5206
fingerprint: 7e3b3bfc3966ddc5d0160c8d466e5ba92edbe55440449619d7204102a25b3240
keys: class_name, success, trees
```

Оба payloads:

- захвачены endpoint-isolated collector;
- сохранены локально как immutable gzip JSON;
- повторно проверены по SHA-256, размеру и fingerprint;
- перечислены в progressive resumable manifest;
- не коммитятся в repository.

## Mapping review checkpoint

Type-only packet schema version `2`:

```text
endpoint_count: 2
archive_verified: 2
field_path_count: 470
node_occurrence_count: 6106
numeric_map_path_count: 4
contains_source_scalar_values: false
ready_for_manual_mapping_review: true
```

Endpoint summaries:

```text
character: 445 paths, 3312 node occurrences, 4 numeric maps
talent_grid: 25 paths, 2794 node occurrences
```

Candidate mappings:

```text
config/mappings/coa_armory_character_v1.json
config/mappings/coa_armory_talent_grid_v1.json
```

Оба имеют status `candidate` и блокируются production gate до явного ручного перевода в `verified`.

Локальная validation пользователя:

```text
all_structurally_consistent: true
all_production_ready: false
mapping_count: 2
character: 19 singletons, 5 collections, 36 fields
talent_grid: 2 singletons, 4 collections, 17 fields
```

`all_production_ready: false` является ожидаемым состоянием candidate mappings.

## Mapping scope

Character mapping включает:

- capture/encounter context;
- player identity и basic context;
- active specialization index;
- selected talent ranks;
- primary/offensive/defensive/resistance summaries.

Deferred:

- detailed gear semantics;
- hero build semantics;
- internal character talent-tree representation;
- `_gearOnly`, `derived`, `raw`, `sourcesByStat` computational internals.

Talent-grid mapping включает trees, talents, IDs, coordinates, node type, ranks, connections and rank text. `lock_rules` и `rank_spell_ids` deferred, поскольку в проверенном payload их массивы пустые.

## Tests and CI

Последний проверенный CI для commit `787ce2e35d66df7752ad7f9b1b6c83518bf68e40`:

```text
workflow: Verify repository
run number: 98
status: completed
conclusion: success
```

Предыдущие Ruff blockers и отсутствие `character`/`talent_grid` больше не являются актуальными blockers.

Локальная Windows caveat сохраняется: `uv sync --frozen --extra dev` ранее пытался собрать Ruff из source distribution без MSVC `link.exe`. Targeted commands через `uv run --no-sync` и GitHub Actions Windows работают.

## Current blockers

1. Candidate Armory mappings ещё не прошли явный semantic/manual review и не имеют status `verified`.
2. Нет bounded automated report discovery с проверенными filters/pagination.
3. Не нормализован полный report/encounter/roster slice.
4. Evidence coverage остаётся узкой.
5. Нет corroborated gameplay mechanic для canonical planner scoring.

## Next bounded tasks

1. Выполнить ручной review candidate Armory mappings без расширения игровой семантики.
2. Зафиксировать решение review и только затем решить, какие mappings допустимо перевести в `verified`.
3. Реализовать bounded report discovery, default до 5 reports/category.
4. Проверить filters и pagination на реальных observations/frontend behavior.
5. Нормализовать один полный report/encounter/roster slice.
6. Расширить supporting и contradicting evidence.
7. Допускать в planner только corroborated/confirmed mechanics.

## Completion gate

PR #3 остаётся Draft до выполнения полного evidence checkpoint:

- real immutable payloads;
- stable fingerprints;
- reviewed verified mappings;
- complete normalized report/encounter/actors/participants/aura events;
- reconstructed intervals;
- independent supporting observations;
- contradicting evidence review;
- reproducible versioned output with provenance;
- green Ubuntu and Windows verification.
