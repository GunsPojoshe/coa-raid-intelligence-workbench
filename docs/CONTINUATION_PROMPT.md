# Стартовый PROMPT для продолжения CoA Raid Intelligence Workbench

Скопируй этот документ в новый ChatGPT/Codex-чат или попроси агента прочитать его из репозитория.

---

Ты продолжаешь разработку проекта **CoA Raid Intelligence Workbench**.

## Обязательный порядок начала

До изменения кода:

1. Проверь repository `GunsPojoshe/coa-raid-intelligence-workbench`.
2. Проверь текущие branch, HEAD и working tree.
3. Проверь PR #7 и base branch.
4. Проверь PR #3.
5. Проверь последний GitHub Actions run и точную причину любого failure.
6. Прочитай полностью:
   - `AGENTS.md`;
   - `docs/PROJECT_MASTER_CONTEXT.md`;
   - `docs/PROJECT_STATE.md`;
   - этот документ;
   - `docs/ARMORY_MAPPING_REVIEW_V1.md`;
   - `docs/ADR_012_LOG_EVIDENCE_TRUTH_MODEL.md`;
   - `docs/REAL_LOG_CAPTURE.md`.
7. Сверь документированные claims с реальным кодом.
8. Сообщи расхождения до изменения analytical model.

Старые HEAD, commit counts, test counts и CI status не считать вечными.

## Репозиторий и branch chain

```text
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

На момент handoff:

```text
HEAD: d251460ea97a8b861b6cec77294108c3beddbb17
Verify repository run #115: success
```

Фактический HEAD и CI всегда перепроверить.

## Миссия

Создать localhost-first browser application для:

- подготовки рейдов FLEX / 10 / 25 / 40;
- хранения планов в DuckDB;
- автоматического сбора observations с `coa.ascensionlogs.gg`;
- evidence-first вывода игровых механик;
- explainable planner recommendations.

Канонический pipeline:

```text
immutable raw observation
-> SHA-256 + schema fingerprint
-> reviewed verified mapping
-> canonical normalized records
-> deterministic reconstruction
-> mechanic hypothesis
-> supporting and contradicting evidence
-> corroborated / confirmed mechanic
-> planner scoring
```

Combat-log event является observation, а не автоматическим доказательством общей mechanic.

## Trust rules

Нельзя придумывать:

- routes;
- query parameters;
- JSON fields;
- pagination behavior;
- event types;
- Spell IDs;
- class/spec/provider mappings;
- semantic meaning по route name;
- stacking, overwrite, coexistence или scope без evidence.

Normalization разрешена только при:

- immutable archived payload;
- exact fingerprint;
- reviewed mapping;
- mapping status `verified`;
- matching fingerprint.

В planner scoring допускаются только:

```text
corroborated
confirmed
```

Всегда сохраняй contradicting evidence.

Provenance разделять:

```text
raw_log
upstream_derived
companion_addon
local_inference
manual_override
```

## Privacy

Никогда не коммить и не отправляй в чат:

- HAR;
- raw payloads;
- DuckDB;
- cookies;
- Authorization headers;
- tokens;
- browser profiles;
- private query values;
- absolute paths containing username.

Cookies разрешены только в памяти process.

## Окружение пользователя

```text
Windows 11
PowerShell
Python 3.12.x
uv
Git
local repo under C:\Users\<USER>\source\repos\...
```

Пользователь предпочитает:

- автономную работу через GitHub;
- один полный PowerShell block за раз;
- полный код без обрывов;
- прямые ответы;
- минимум ручных действий;
- честное разделение verified / observed / planned.

## Подтверждённый фундамент

- localhost FastAPI app;
- browser raid constructor;
- DuckDB persistence;
- immutable raw archive;
- observations отдельно от deduplicated payload bodies;
- safe JSON/HAR import and inventory;
- schema fingerprints;
- verified mapping gate;
- canonical report/encounter/actor/participant/aura records;
- Aura State Engine;
- hypotheses and evidence links;
- trust/weighting policies;
- migrations `0001`–`0006`;
- repository verifier;
- Ubuntu and Windows CI;
- SPA route discovery;
- versioned HTTP profile `coa-fetch-context-v1`;
- endpoint-isolated progressive/resumable Armory capture;
- structural and mapping-review packets;
- candidate Armory mapping contracts;
- raw-archive selector validation gate.

## Real aura checkpoint

Report `2987`, spell `968746`:

### Encounter 64795

```text
fingerprint: 2994424cb95c2a7e1997651226b7942367ebe77003e0f4614aae5da4920f8b98
mapping: coa-aura-timeline-single-encounter-v1, verified
6 canonical events
3 reconstructed intervals
exact match with 3 debuff_sources intervals
0 rejects
0 anomalies
```

### Encounter 64796

```text
window: 10382-38265 ms
full duration: 117215 ms
fingerprint: d8b6dd869d6adf8f3433f9e285b8270cd1aa8d640839c915a42c80b2211cbf0b
3 canonical events
2 reconstructed intervals
exact match with 2 debuff_sources intervals
0 rejects
0 anomalies
```

Это подтверждает normalizer/Aura State Engine behavior, но не numeric effect, stacking, overwrite, coexistence, scope или criticality.

## Real Armory checkpoint

```text
character_id: 156120
class_slug: felsworn
profile: coa-fetch-context-v1
```

### Character

```text
route: /api/armory/character/156120
bytes: 59910
hash: 2a9d752d7af72d41cd9d41836d670069c78e408df7260f5d9caa83b07430985f
fingerprint: efbcf618291d824667ba586c22af4ed031fa146d69b11a5539ec17a41d042621
```

### Talent grid

```text
route: /api/armory/talent-grid/felsworn
bytes: 63025
hash: 11be25407ec00898547c1b7f342d4596268b3164df9fe0f120bb911559cc5206
fingerprint: 7e3b3bfc3966ddc5d0160c8d466e5ba92edbe55440449619d7204102a25b3240
```

## Mapping review state

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

```text
config/mappings/coa_armory_character_v1.json
config/mappings/coa_armory_talent_grid_v1.json
```

Review document:

```text
docs/ARMORY_MAPPING_REVIEW_V1.md
```

Review corrections:

- `cao_id` retained as `source_cao_id`;
- `bisbeard_tree` retained as `source_bisbeard_tree`;
- talent records preserve parent tree;
- connections preserve source talent/tree;
- rank texts preserve source talent/tree;
- empty `lock_rules` and `rank_spell_ids` item schemas remain deferred.

Mappings are still `candidate` and blocked from production.

## Raw-archive validation gate

`scripts/validate_armory_mappings.py` now validates:

1. safe type-only review packet;
2. structural manifest against exact gzip archives;
3. payload hash;
4. schema fingerprint;
5. route template;
6. singleton selector extraction;
7. collection occurrence counts;
8. `@item`, `@index`, `@ancestor[n]` selectors;
9. required field presence and JSON types.

Unit coverage verifies selector execution and controlled rejection of drift.

Repository CI:

```text
96 passed, 1 warning
Ubuntu verifier: success
Windows pytest/doctor/DuckDB initialization: success
```

The real private archives have not yet been run through the new raw selector gate.

## Первая задача нового агента

1. Проверить latest HEAD and CI.
2. Попросить пользователя выполнить один local PowerShell block:

```powershell
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location "C:\Users\<USER>\source\repos\coa-raid-intelligence-workbench"

git fetch origin
git switch e3/real-log-capture
git pull --ff-only origin e3/real-log-capture

uv run --no-sync python scripts/validate_armory_mappings.py `
    --review "data\exchange\out\armory-mapping-review-v2.json" `
    --manifest "data\exchange\out\armory-endpoint-capture.json" `
    --raw-root "data\raw" `
    --output "data\exchange\out\armory-mapping-validation.json"

Get-Content "data\exchange\out\armory-mapping-validation.json" -Raw
```

3. Проверить ожидаемое:

```text
schema_version: 2
all_structurally_consistent: true
all_raw_archives_consistent: true
all_production_ready: false
mapping_count: 2
```

4. Не переводить mappings в `verified`, пока реальный raw result не проверен.
5. После successful raw validation выполнить отдельный explicit promotion change с `reviewed_by` и `reviewed_at`.
6. Затем перейти к bounded report discovery.

## Дальнейший план

```text
verified Armory mappings
-> bounded report discovery
-> filters/pagination review
-> default up to 5 reports per category
-> encounter discovery
-> selected analytical endpoints
-> immutable archive
-> reviewed parsers
-> full report/encounter/roster normalization
-> evidence expansion
-> planner integration
```

Full event stream использовать только для hypotheses, которые нельзя проверить compact endpoints.

## Completion gate

PR #3 и PR #7 остаются Draft до соответствующего evidence checkpoint:

1. real immutable payloads;
2. fingerprints;
3. verified mappings;
4. normalized report/encounter;
5. linked actors/participants/aura events;
6. reconstructed intervals;
7. independent supporting observations;
8. contradicting evidence review;
9. versioned reproducible output;
10. provenance;
11. green Ubuntu + Windows CI.

## Формат отчёта после каждой задачи

Сообщай:

- фактически проверенное;
- local-only observations;
- устаревшие claims;
- files changed;
- migrations added;
- exact commands run;
- exact tests;
- CI state;
- remaining limitations;
- next bounded task.

Не называй scaffolding, parser correctness или verified schema mapping подтверждённой игровой механикой.
