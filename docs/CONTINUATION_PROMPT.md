# Стартовый PROMPT для продолжения CoA Raid Intelligence Workbench

Скопируй этот документ в новый ChatGPT/Codex-чат или попроси агента прочитать его из репозитория.

---

Ты продолжаешь разработку проекта **CoA Raid Intelligence Workbench**.

## Обязательный порядок начала

До изменений:

1. Проверь repository `GunsPojoshe/coa-raid-intelligence-workbench`.
2. Проверь branch, HEAD и working tree.
3. Проверь PR #7 и его base branch.
4. Проверь PR #3.
5. Проверь последний GitHub Actions run и точную причину любого failure.
6. Прочитай:
   - `AGENTS.md`;
   - `docs/PROJECT_MASTER_CONTEXT.md`;
   - `docs/PROJECT_STATE.md`;
   - этот документ;
   - `docs/ADR_012_LOG_EVIDENCE_TRUTH_MODEL.md`;
   - `docs/REAL_LOG_CAPTURE.md`.
7. Сверь claims с кодом и CI.
8. Сообщи расхождения до расширения analytical model.

Старые HEAD, commit counts, test counts и CI status не считать вечными.

## Branch chain

```text
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

Подтверждённый checkpoint до следующей проверки:

```text
HEAD: 787ce2e35d66df7752ad7f9b1b6c83518bf68e40
CI: Verify repository run #98, success
```

После documentation refresh фактический HEAD будет новее. Всегда проверяй GitHub.

## Миссия

Создать localhost-first browser application для:

- подготовки рейдов FLEX / 10 / 25 / 40;
- хранения планов в DuckDB;
- автоматического сбора observations с `coa.ascensionlogs.gg`;
- evidence-first анализа игровых механик;
- explainable planner recommendations.

Pipeline:

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

Combat-log event является observation, а не доказательством общей mechanic.

## Trust rules

Нельзя придумывать routes, parameters, fields, pagination, event types, Spell IDs, class/spec/provider mappings или gameplay semantics.

Normalization разрешена только при:

- immutable archived payload;
- exact fingerprint;
- reviewed mapping;
- status `verified`;
- matching fingerprint.

В planner scoring допускаются только `corroborated` и `confirmed` mechanics.

Сохраняй contradicting evidence и разделяй provenance:

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
- абсолютные пути с username.

Cookies разрешены только в process memory.

## Окружение пользователя

```text
Windows 11
PowerShell
Python 3.12.x
uv
Git
local repo under C:\Users\<USER>\source\repos\...
```

Пользователь предпочитает автономную GitHub-работу, один полный PowerShell block, полный код без обрывов, минимум ручных действий и явное разделение verified/observed/planned.

## Подтверждённый фундамент

- localhost FastAPI app и browser raid constructor;
- DuckDB persistence;
- immutable raw archive;
- safe JSON/HAR import и deterministic inventory;
- schema fingerprints;
- verified mapping gate;
- canonical report/encounter/actor/participant/aura records;
- Aura State Engine;
- hypotheses и evidence links;
- trust/weighting policies;
- migrations `0001`–`0006`;
- repository verifier и Ubuntu/Windows CI;
- SPA route discovery;
- HTTP profile `coa-fetch-context-v1`;
- persistent same-origin session;
- timeout/retry/incomplete-response handling;
- endpoint-isolated progressive/resumable Armory capture;
- structural and type-only Armory review;
- candidate Armory mappings с production gate.

## Real aura checkpoint

Report `2987`, spell `968746`:

```text
encounter 64795:
  fingerprint 2994424cb95c2a7e1997651226b7942367ebe77003e0f4614aae5da4920f8b98
  6 canonical events
  3 reconstructed intervals
  exact match with 3 reference intervals
  0 rejects, 0 anomalies

encounter 64796:
  window 10382–38265 ms
  full duration 117215 ms
  fingerprint d8b6dd869d6adf8f3433f9e285b8270cd1aa8d640839c915a42c80b2211cbf0b
  3 canonical events
  2 reconstructed intervals
  exact match with 2 reference intervals
  0 rejects, 0 anomalies
```

Это подтверждает normalizer/Aura State Engine behavior, но не numeric effect, stacking, overwrite, coexistence, scope или criticality.

## Real Armory checkpoint

Subject:

```text
character_id: 156120
class_slug: felsworn
realm: Vol'Jin
profile: coa-fetch-context-v1
```

Captured and verified locally:

```text
character:
  route /api/armory/character/156120
  HTTP 200
  bytes 59910
  hash 2a9d752d7af72d41cd9d41836d670069c78e408df7260f5d9caa83b07430985f
  fingerprint efbcf618291d824667ba586c22af4ed031fa146d69b11a5539ec17a41d042621

talent_grid:
  route /api/armory/talent-grid/felsworn
  HTTP 200
  bytes 63025
  hash 11be25407ec00898547c1b7f342d4596268b3164df9fe0f120bb911559cc5206
  fingerprint 7e3b3bfc3966ddc5d0160c8d466e5ba92edbe55440449619d7204102a25b3240
```

Оба payloads immutable, hash/fingerprint/size verified, raw bodies local-only.

## Mapping review checkpoint

Review packet schema `2`:

```text
2 verified archives
470 aggregated paths
6106 node occurrences
4 numeric maps
no source scalar values
ready for manual mapping review
```

Candidate mappings:

```text
config/mappings/coa_armory_character_v1.json
config/mappings/coa_armory_talent_grid_v1.json
```

Локальная validation:

```text
all_structurally_consistent: true
all_production_ready: false
mapping_count: 2
```

`all_production_ready: false` ожидаемо: mappings имеют status `candidate` и production gate должен их блокировать.

## Current CI

```text
commit: 787ce2e35d66df7752ad7f9b1b6c83518bf68e40
workflow: Verify repository
run: #98
conclusion: success
```

Старые Ruff blockers исправлены. Старые claims об отсутствующих `character` и `talent_grid` payloads устарели.

## Первая bounded задача нового агента

### A. Baseline

1. Проверить latest HEAD, PR и CI.
2. Проверить, что candidate mappings всё ещё структурно согласованы с локальным review packet.
3. Не менять migrations.

### B. Manual Armory mapping review

1. Review только заявленных paths/types/nullable/occurrence counts.
2. Не выводить gameplay semantics из названий fields.
3. Проверить scope candidate mappings:
   - character identity/context;
   - selected talents;
   - compact stat summaries;
   - talent-grid trees/nodes/connections/rank text.
4. Сохранить deferred:
   - detailed gear semantics;
   - hero build semantics;
   - character internal derived/raw computational structures;
   - empty `lock_rules` и `rank_spell_ids` item schemas.
5. Переводить mapping в `verified` только после явного review decision.
6. Не называть verified mapping подтверждённой игровой механикой.

### C. Следующий engineering slice

После mapping decision:

```text
verified report discovery
-> filters/pagination review
-> deterministic selection, default up to 5 reports/category
-> encounter discovery
-> selected analytical endpoints
-> immutable archive
-> reviewed parsers
-> full report/encounter/roster normalization
-> evidence expansion
```

Full event stream использовать только когда compact endpoints недостаточны.

## Remaining limitations

- Armory mappings пока candidate;
- bounded report discovery не реализован;
- полный report/encounter/roster slice не нормализован;
- evidence coverage узкая;
- нет corroborated gameplay mechanic для planner scoring.

## Completion gate

PR #3 остаётся Draft до:

1. real immutable payloads;
2. stable fingerprints;
3. reviewed verified mappings;
4. normalized report/encounter;
5. linked actors/participants/aura events;
6. reconstructed intervals;
7. independent supporting observations;
8. contradicting evidence review;
9. versioned reproducible output and provenance;
10. green Ubuntu + Windows CI.

## Формат отчёта

Сообщай:

- фактически проверенное;
- local-only observations;
- устаревшие claims;
- files changed;
- migrations added;
- exact commands/tests;
- CI state;
- remaining limitations;
- next bounded task.

Не называй scaffolding, parser correctness или verified schema mapping подтверждённой игровой механикой.
