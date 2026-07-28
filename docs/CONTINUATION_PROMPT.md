# Стартовый PROMPT для продолжения CoA Raid Intelligence Workbench

Скопируй этот документ в новый ChatGPT/Codex-чат или попроси агента прочитать его из репозитория.

---

Ты продолжаешь разработку проекта **CoA Raid Intelligence Workbench**.

## Обязательный порядок начала

Ничего не меняй, пока не выполнишь:

1. Проверь repository `GunsPojoshe/coa-raid-intelligence-workbench`.
2. Проверь текущие branch, HEAD и working tree.
3. Проверь PR #7 и его base branch.
4. Проверь PR #3.
5. Проверь последний GitHub Actions run и точную причину любого failure.
6. Прочитай полностью:
   - `AGENTS.md`;
   - `docs/PROJECT_MASTER_CONTEXT.md`;
   - `docs/PROJECT_STATE.md`;
   - этот документ;
   - `docs/ADR_012_LOG_EVIDENCE_TRUTH_MODEL.md`;
   - `docs/REAL_LOG_CAPTURE.md`.
7. Сверь документированные claims с реальным кодом.
8. Сообщи расхождения до изменения analytical model.

Старые HEAD, commit counts, test counts и CI status не считать вечными.

## Репозиторий и branch chain

На момент handoff:

```text
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

Последний подтверждённый кодовый head до documentation refresh:

```text
ad605cc test: cover incomplete chunked responses
```

После него в ту же ветку добавлена обновлённая документация. Фактический HEAD проверь через GitHub.

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

## Жёсткие trust rules

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

Разделяй provenance:

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
- separate observations and deduplicated payload bodies;
- safe JSON/HAR import;
- deterministic HAR inventory;
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
- Armory collector;
- HTTP profile `coa-fetch-context-v1`;
- persistent same-origin session and in-memory cookies;
- timeout/retry/incomplete-response handling.

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
window: 10382–38265 ms
full duration: 117215 ms
fingerprint: d8b6dd869d6adf8f3433f9e285b8270cd1aa8d640839c915a42c80b2211cbf0b
3 canonical events
2 reconstructed intervals
exact match with 2 debuff_sources intervals
0 rejects
0 anomalies
```

Это подтверждает normalizer/Aura State Engine behavior, но не `+8% AP`, stacking, overwrite, coexistence, scope или criticality.

## Verified HTTP finding

Полный profile:

```text
Accept: application/json, text/plain, */*
Accept-Language: en-US,en;q=0.9
Cache-Control: no-cache
Pragma: no-cache
User-Agent: Chromium-like
Referer: https://coa.ascensionlogs.gg/
Sec-Fetch-Dest: empty
Sec-Fetch-Mode: cors
Sec-Fetch-Site: same-origin
```

Вернул HTTP 200 для reports public, character search и Armory by-name.

Не доказано:

- minimal header subset;
- cookie requirement;
- request-order dependency;
- fresh-session Armory-first behavior.

## Real Armory state

Subject:

```text
Gunspojoshe
Vol'Jin
Tyrant
phase 0
World Bosses
normal
```

Подтверждено:

```text
character_id: 156120
character_class: Felsworn
has_armory: true
identity_source: by_name
profile: coa-fetch-context-v1
```

Archived successfully:

### by_name

```text
hash: a81bb54342ee1573017b314af418e54da3ec56c51131f62bd2dd5efe826d5cff
fingerprint: 108ea5ed6a659d7161904ab087b4631df0f5c2ec69f94e1f2d90cbbaeaea0c37
```

### captures

```text
hash: 34192051026d918ec0dcb311efc236c5873fda2f7748bc2acad128e5f5ec7851
fingerprint: e03d3b0d7c308ab4740280720cbaaaf60740a19e50826d23eb2194124397b814
```

Missing:

```text
armory_api_character body
armory_api_talent_grid body
```

Оба endpoint давали status 200, но body read зависал. Был один `IncompleteRead`, затем timeout. `IncompleteRead` handling добавлен. Последний запуск пользователь остановил во время второй 180-second attempt. DuckDB и уже archived payloads целы.

## Current CI state at handoff

Последний проверенный run для `ad605cc`:

```text
run #65
Windows: success
Ubuntu full pytest: 78 passed, 1 warning
Ubuntu verifier: failed on Ruff only
```

Known Ruff blockers:

- unused `ssl` in `scripts/diagnose_armory_access.py`;
- unused `FETCH_CONTEXT_PROFILE_VERSION` import in `armory_api_capture.py`;
- format `scripts/diagnose_armory_access.py`;
- format `scripts/import_armory_har.py`.

Проверь, не исправлены ли они documentation commits или последующими changes.

## Local environment caveat

Локальный `uv sync --frozen --extra dev` на Windows пытался build Ruff from source и упал из-за missing `link.exe`.

При этом:

- targeted tests через `uv run --no-sync` работают;
- GitHub Actions Windows sync прошёл;
- не требуй Visual Studio Build Tools без отдельной диагностики wheel selection.

Последний targeted local suite:

```text
12 passed
```

## Первая задача нового агента

Выполни строго bounded slice:

### A. Baseline

1. Проверь latest HEAD and CI.
2. Исправь только актуальные Ruff blockers.
3. Запусти/проверь CI до green Ubuntu + Windows.
4. Не меняй migrations.

### B. Endpoint-isolated Armory capture

1. Не запускай снова полный long-timeout chain.
2. Добавь отдельный capture command/function для одного endpoint.
3. Используй короткий bounded timeout.
4. Сделай progressive result writing после каждого endpoint.
5. Добавь resumable manifest.
6. Не скачивай повторно `by_name` и `captures`, если archive reuse подтверждает payload.
7. Получи только missing `character` и `talent_grid`.
8. Сохрани hashes, fingerprints, sizes, status и safe transport warning.
9. Unit tests не должны зависеть от live network.

После этого:

- inspect real structures;
- не создавай semantic mapping до review;
- создай candidate mapping;
- переводи в `verified` только после проверки.

## Дальнейший план

```text
verified report discovery
-> filters/pagination review
-> default up to 5 reports per category
-> encounters
-> selected analytical endpoints
-> immutable archive
-> reviewed parsers
-> full report/encounter/roster normalization
-> evidence expansion
-> planner integration
```

Full event stream использовать только для hypotheses, которые нельзя проверить compact endpoints.

## Completion gate

PR #3 остаётся Draft до:

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

## Формат ответа после каждой задачи

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

---

Стартуй с чтения `docs/PROJECT_MASTER_CONTEXT.md` полностью и проверки фактического состояния GitHub.
