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

## Branch chain

```text
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

Latest verified code checkpoint before documentation refresh:

```text
HEAD: a1517d44f3024efcb237f1f47ca775de1fee1c33
Verify repository run #133: success
Ubuntu: success
Windows: success
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

```text
immutable archived payload
+ exact fingerprint
+ reviewed mapping
+ mapping status verified
+ matching payload hash/fingerprint
```

В planner scoring допускаются только `corroborated` и `confirmed`. Всегда сохраняй contradicting evidence.

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

Пользователь предпочитает автономную работу через GitHub, один полный PowerShell block, полный код без обрывов, минимум ручных действий и честное разделение verified / observed / planned.

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
- raw-archive selector validation gate;
- verified Armory character and talent-grid mappings;
- bounded one-page public-report discovery collector and CLI.

## Real aura checkpoint

Report `2987`, spell `968746`.

```text
encounter 64795
fingerprint: 2994424cb95c2a7e1997651226b7942367ebe77003e0f4614aae5da4920f8b98
6 canonical events
3 reconstructed intervals
exact match with 3 debuff_sources intervals
0 rejects, 0 anomalies

encounter 64796
window: 10382-38265 ms
full duration: 117215 ms
fingerprint: d8b6dd869d6adf8f3433f9e285b8270cd1aa8d640839c915a42c80b2211cbf0b
3 canonical events
2 reconstructed intervals
exact match with 2 debuff_sources intervals
0 rejects, 0 anomalies
```

Это подтверждает normalizer/Aura State Engine behavior, но не numeric effect, stacking, overwrite, coexistence, scope или criticality.

## Verified Armory checkpoint

```text
character_id: 156120
character hash: 2a9d752d7af72d41cd9d41836d670069c78e408df7260f5d9caa83b07430985f
character fingerprint: efbcf618291d824667ba586c22af4ed031fa146d69b11a5539ec17a41d042621

class_slug: felsworn
talent-grid hash: 11be25407ec00898547c1b7f342d4596268b3164df9fe0f120bb911559cc5206
talent-grid fingerprint: 7e3b3bfc3966ddc5d0160c8d466e5ba92edbe55440449619d7204102a25b3240
```

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

Final local production gate:

```text
schema_version: 2
mapping_count: 2
raw_archive_count: 2
all_structurally_consistent: true
all_raw_archives_consistent: true
all_production_ready: true
```

Verified mappings prove reproducible extraction only for the exact reviewed hashes/fingerprints. Deferred scopes and interpretation boundaries are recorded in `docs/ARMORY_MAPPING_REVIEW_V1.md`.

## Bounded report discovery implementation

Implemented:

```text
src/coa_workbench/collector/report_discovery.py
scripts/capture_report_discovery.py
tests/unit/test_report_discovery.py
```

Allowed request shape:

```text
GET /api/reports/public
page=<explicit integer >= 1>
limit=<1..5, default 5>
sortBy=created_at
sortOrder=desc
```

Guarantees:

- one explicitly requested page per invocation;
- no automatic pagination;
- hard maximum `limit=5`;
- only observed sort values accepted;
- raw body archived before interpretation;
- compact result excludes report IDs, names and source scalar values;
- request-header values and cookies are not stored;
- invalid JSON is archived but not marked complete;
- transport failure does not create a false capture.

Not yet verified:

- real response top-level shape and field paths;
- number of returned report records;
- category/filter semantics;
- pagination metadata, stopping rules or additional pages.

`local_category` is a local label only and must not be represented as a source category.

## Первая задача нового агента

Run one real bounded public-report capture and inspect only its compact output.

Required local command shape:

```powershell
uv run --no-sync python scripts/capture_report_discovery.py `
    --local-category "public_recent" `
    --page 1 `
    --limit 5 `
    --output "data\exchange\out\report-discovery-page.json"
```

Then verify only:

- capture completed;
- HTTP status/content type;
- payload hash;
- schema fingerprint;
- response byte count;
- top-level JSON kind and keys;
- no source scalar values in the compact output.

Do not print, attach or commit the raw archived response.

After the real capture:

1. build a scalar-free structural review from the exact archive;
2. review response fields and occurrence counts;
3. define candidate selectors only for structurally unambiguous fields;
4. investigate filters/categories/pagination through separate explicit observations;
5. do not implement auto-pagination or per-category selection before those observations.

## Дальнейший pipeline

```text
real bounded report page
-> immutable archive
-> scalar-free structural review
-> reviewed report discovery mapping
-> explicit pagination/filter observations
-> deterministic bounded selection
-> encounter discovery
-> reviewed encounter/roster parsers
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
