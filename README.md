# CoA Raid Intelligence Workbench

Локальное браузерное приложение для подготовки рейдовых составов и evidence-first анализа Classless / Ascension WoW.

## Что строим

Проект объединяет два контура:

1. **Raid Planner** — конструктор рейдов FLEX / 10 / 25 / 40, структурная проверка состава и хранение планов в DuckDB.
2. **Raid Intelligence** — воспроизводимый сбор наблюдений с `coa.ascensionlogs.gg`, проверка их происхождения и использование в рекомендациях только после достаточного подтверждения.

Канонический принцип:

```text
combat-log event = observation
combat-log event != proof of a general game mechanic
```

В planner scoring допускаются только механики со статусом `corroborated` или `confirmed`.

## Простыми словами: где мы сейчас

Мы уже умеем безопасно получать данные, сохранять исходные ответы без изменений, считать их hashes/schema fingerprints, проверять структуру и выпускать публичные scalar-free receipts без приватных ID и строк.

Для гильдии Argentum уже:

- полностью собран публичный список отчётов;
- подтверждена identity гильдии;
- выделены 17 отчётов гильдии;
- зафиксирован contract будущего полного сбора;
- проверен маршрут поиска гильдий `/api/guilds/search`;
- проверена структура ответа и типы полей;
- подтверждено, что параметр `limit` сервер принимает.

Но пока не доказано, как именно `limit` ограничивает несколько результатов. Также не доказаны pagination, termination и completeness. Поэтому полный автоматический crawl, character graph, performance model и BiS 25 scoring остаются выключены.

Следующий этап уже реализован в коде: bounded multi-result probe. Он должен выполнить три ограниченных запроса с приватной поисковой строкой, которая возвращает несколько гильдий, и проверить стабильность результата при `limit=1`, `limit=25` и повторном `limit=25`.

## Архитектура

```text
Browser
-> localhost FastAPI
-> planner / catalog / evidence pipeline
-> DuckDB
```

Evidence pipeline:

```text
source response
-> immutable raw archive
-> retrieval observation
-> SHA-256 + schema fingerprint
-> reviewed mapping or extractor
-> deterministic normalization/extraction
-> immutable observations
-> supporting / contradicting evidence
-> corroborated / confirmed mechanic
-> explainable planner scoring
```

## Ветки и milestone

```text
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

E3 остаётся Draft. Перед любой новой работой фактические HEAD, PR и CI необходимо перепроверять.

## Реализованный фундамент

- localhost FastAPI runtime и браузерный raid constructor;
- class/spec/role catalog и Python validation;
- DuckDB persistence и CRUD raid plans;
- immutable content-addressed raw archive;
- отдельные retrieval observations;
- JSON/HAR privacy-safe tooling;
- schema fingerprints и reviewed mapping gates;
- canonical report/encounter/actor/participant/aura records;
- Aura State Engine;
- hypotheses, supporting/contradicting evidence и trust policies;
- migrations `0001`–`0008`;
- Ubuntu/Windows repository verification;
- public-release audit.

## Report/encounter и combatants checkpoint

```text
normalized:
  reports: 2
  encounters: 15
  actors: 31
  participants: 31
  aura events: 0

reconstructed:
  reports: 1
  encounters: 14
  actors: 31
  participants: 31
  field conflicts: 0

persisted through 0007:
  canonical entity observations: 77

combatants through 0008:
  parser observations: 1343
  actor/build observations: 1339
  linked actors: 11
  integrity checks: 14/14
```

Это подтверждает воспроизводимость parser/persistence pipeline, но не подтверждает игровые механики или пригодность данных для scoring.

## Public manifest, identity и filtering

```text
public reports: 6454
unique public report IDs: 6454
public-manifest checks: 19/19
exact Argentum label reports: 17
identity-decision checks: 16/16
guild identity verified: true
selected guild reports: 17
unique selected report IDs: 17
filter checks: 14/14
```

Source guild ID и report IDs остаются private. Публичные receipts содержат только counts, hashes, schemas и решения.

## Full-crawl contract

```text
receipt: evidence/real-data/argentum-guild-full-crawl-contract.json
integrity checks: 12/12
full crawl collection contract reviewed: true
verified private comparison baseline: 17 reports
```

Contract требует до полного crawl отдельно доказать:

- точный route/query contract;
- response schema;
- limit behavior;
- pagination semantics;
- termination semantics;
- completeness boundary;
- deterministic comparison API-derived report set с private 17-report baseline.

## Guild route/schema checkpoint

Capture:

```text
receipt: evidence/real-data/argentum-guild-route-semantics-capture.json
attempts: 3
completed attempts: 3
HTTP 200 responses: 3
capture checks: 13/13
observed result counts: [1]
```

Review:

```text
receipt: evidence/real-data/argentum-guild-route-semantics-review.json
review checks: 22/22
route template verified: true
query shapes verified: true
response schema verified: true
limit parameter accepted: true
ready for bounded limit-semantics capture: true
```

Verified guild record fields:

```text
id: integer
name: string
realm: string
report_count: string
```

Все три запроса вернули одну и ту же запись. Поэтому это не доказывает truncation semantics.

## Реализованный следующий probe

```text
src/coa_workbench/collector/guild_limit_semantics_capture.py
scripts/capture_guild_limit_semantics.py
tests/unit/test_guild_limit_semantics_capture.py
```

Probe выполняет:

```text
private query + low limit
private query + high limit
private query + identical high-limit repeat
```

Capture становится готовым к отдельному review только если:

- все три ответа полные и валидные;
- schema стабильна;
- low-limit выдача заполняет low limit;
- high-limit выдача содержит больше записей;
- повтор high-limit даёт тот же ordered-record hash и source-ID order hash;
- low-limit source-ID hash sequence является точным префиксом high-limit sequence.

Даже успешный capture не включает full crawl. Он устанавливает только `ready_for_limit_semantics_review=true`.

## Текущая граница

```text
guild identity verified: true
guild filtering completed: true
full crawl collection contract reviewed: true
guild route template verified: true
guild query shapes verified: true
guild response schema verified: true
limit parameter accepted: true
ready for bounded limit-semantics capture: true
limit truncation semantics verified: false
pagination semantics verified: false
termination semantics verified: false
completeness verified: false
guild API route semantics verified: false
automatic full guild crawl allowed: false
ready for full guild crawl: false
ready for multi-report character graph: false
ready for performance model: false
ready for BiS 25 scoring: false
planner scoring allowed: false
```

## Следующие шаги

1. Дождаться green Ubuntu, Windows и public-release-audit на актуальном HEAD.
2. Локально выбрать privacy-safe query, которая возвращает несколько гильдий.
3. Запустить `scripts/capture_guild_limit_semantics.py`.
4. Загрузить только public receipt `data/exchange/out/argentum-guild-limit-semantics-capture.json`.
5. Проверить receipt и выпустить отдельный scalar-free limit-semantics review.
6. Отдельно доказать pagination, termination и completeness.
7. Сравнить будущий API-derived report set с private 17-report baseline.
8. Только после прохождения всех gates отдельно разрешать full crawl.
9. После полного verified corpus переходить к character identity graph, performance corpus и BiS 25 optimizer.

## Установка и проверка

```text
Python >= 3.12
uv
```

```powershell
uv sync --frozen --extra dev
uv run python scripts/verify_repo.py
```

Запуск приложения:

```powershell
uv run coa-workbench serve
```

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/docs
```

## Data policy

В Git версионируются код, tests, migrations, reviewed mappings, документация и scalar-free receipts.

Local-only:

```text
data/raw/
data/warehouse/
data/normalized/
data/reconstructed/
data/extracted/
data/exchange/in/
data/exchange/out/
```

Не коммитить raw payloads, unsanitized HAR, DuckDB/WAL, private batches, private receipts, source guild IDs, report IDs, cookies, Authorization headers, tokens, browser profiles, `.env` или абсолютные локальные пути с username.

## Документация

- `docs/PROJECT_MASTER_CONTEXT.md` — каноническая цель, архитектура и trust model;
- `docs/PROJECT_STATE.md` — текущее operational state;
- `docs/CONTINUATION_PROMPT.md` — полный prompt для продолжения разработки;
- `docs/REAL_LOG_CAPTURE.md` — capture/review/persistence protocol;
- `docs/GUILD_WIDE_COLLECTION_CONTRACT.md` — guild-wide collection gates;
- `evidence/real-data/README.md` — versioned evidence checkpoint;
- `AGENTS.md` — обязательные инструкции агентам.
