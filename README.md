# CoA Raid Intelligence Workbench

Локальное браузерное приложение для подготовки рейдовых составов и evidence-first анализа Classless / Ascension WoW.

## Что строим

Проект объединяет два контура:

1. **Raid Planner** — конструктор рейдов FLEX / 10 / 25 / 40, структурная проверка состава и хранение планов в DuckDB.
2. **Raid Intelligence** — воспроизводимый сбор наблюдений с `coa.ascensionlogs.gg`, проверка происхождения данных и использование их в рекомендациях только после достаточного подтверждения.

Канонический принцип:

```text
combat-log event = observation
combat-log event != proof of a general game mechanic
```

В planner scoring допускаются только mechanics со статусом `corroborated` или `confirmed`.

## Простыми словами: где мы сейчас

Уже реализованы безопасный raw capture, hashes/schema fingerprints, reviewed mappings, scalar-free public receipts, deterministic persistence и privacy gates.

Для Argentum подтверждены:

- публичный manifest: `6454` уникальных отчёта;
- identity гильдии;
- private comparison baseline: `17` отчётов;
- full-crawl collection contract;
- `/api/guilds/search` route/schema;
- стабильная bounded limit truncation semantics `1 / 7 / 7`;
- `/api/guilds/progression` route candidate;
- offline usage-context и helper/call-site review;
- evidence-backed unambiguous HTTP method candidate `POST`.

Но generic-helper identity и точное отображение request payload пока не подтверждены. Поэтому guessed network probe, pagination, completeness, full crawl, character graph, performance model и BiS 25 scoring остаются выключены.

Следующий инструмент уже реализован и CI-green: offline helper-definition inventory. Он должен найти bounded definition/alias/call-chain candidates в exact archived SPA asset, сохранить raw JavaScript только private и выпустить scalar-free public receipt с `36` integrity checks.

## Текущий проверенный implementation checkpoint

```text
HEAD: 82265903a26bbf8e0032e6dc2512e623055da972
Verify repository run: #578
conclusion: success
public-release-audit: success
Ubuntu: success
Windows: success
```

После него были добавлены documentation-only commits. Фактический текущий HEAD и CI всегда перепроверяются перед продолжением.

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

## Ветки

```text
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

PR #7 остаётся Draft до закрытия evidence gates.

## Реализованный фундамент

- localhost FastAPI runtime и raid constructor;
- class/spec/role catalog и validation;
- DuckDB persistence и CRUD raid plans;
- immutable content-addressed raw archive;
- retrieval observations;
- JSON/HAR privacy-safe tooling;
- schema fingerprints и reviewed mapping gates;
- canonical report/encounter/actor/participant/aura records;
- Aura State Engine;
- hypotheses, supporting/contradicting evidence и trust policies;
- migrations `0001`–`0008`;
- Ubuntu/Windows repository verification;
- public-release audit.

## Progression checkpoint

```text
route candidate: /api/guilds/progression
usage context reviewed: true
helper/call-site reviewed: true
call class: generic_helper_call
HTTP method candidate: POST
method candidate unambiguous: true
helper identity resolved: false
request payload mapping resolved: false
request shape verified: false
ready for bounded route probe: false
```

Implemented helper-definition inventory:

```text
src/coa_workbench/collector/guild_progression_helper_definition_command.py
src/coa_workbench/collector/guild_progression_helper_definition_index.py
src/coa_workbench/collector/guild_progression_helper_definition_inventory.py
scripts/inventory_guild_progression_helper_definition.py
tests/unit/test_guild_progression_helper_definition_command.py
tests/unit/test_guild_progression_helper_definition_index.py
tests/unit/test_guild_progression_helper_definition_inventory.py
```

## Текущая граница

```text
helper-definition inventory implementation complete: true
helper-definition inventory executed on private artifacts: false
helper-definition public receipt validated: false
helper-definition receipt versioned: false
helper-definition review complete: false
progression helper identity resolved: false
progression request payload mapping resolved: false
ready for bounded progression route probe: false
pagination semantics verified: false
termination semantics verified: false
completeness verified: false
automatic full guild crawl allowed: false
ready for full guild crawl: false
ready for multi-report character graph: false
ready for performance model: false
ready for BiS 25 scoring: false
planner scoring allowed: false
```

## Следующий этап

1. Проверить текущий documentation HEAD и CI.
2. Fast-forward локальную ветку `e3/real-log-capture`.
3. Убедиться, что working tree чист и private evidence сохранён.
4. Запустить offline helper-definition inventory на exact local private artifacts.
5. Проверить private output, все `36` integrity checks и privacy boundaries.
6. Валидировать scalar-free public receipt.
7. Версионировать только public receipt.
8. Реализовать отдельный deterministic helper-definition review.
9. Рассматривать bounded progression route probe только после подтверждения helper identity и exact payload contract.

## Установка и проверка

```text
Python >= 3.12
uv
```

Canonical CI verification:

```powershell
uv sync --frozen --extra dev
uv run python scripts/verify_repo.py
```

На текущей Windows-машине локальный `uv sync --frozen --extra dev` ранее попытался собрать Ruff `0.12.12` из исходников и остановился из-за отсутствия MSVC `link.exe`. Для разового форматирования использовался официальный standalone Ruff `0.12.12`; Visual Studio Build Tools специально для этого не устанавливались.

Запуск приложения:

```powershell
uv run coa-workbench serve
```

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/docs
```

## Data policy

Versioned: code, tests, migrations, reviewed mappings/reviews, documentation and scalar-free receipts.

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

Не коммитить raw payloads, unsanitized HAR, DuckDB/WAL, private receipts, source guild IDs, report IDs, raw JavaScript, cookies, Authorization headers, tokens, browser profiles, `.env` или private queries.

## Workflow notification convention

После каждого push или connector write, запускающего GitHub Actions:

1. сразу проверить новый workflow run;
2. показать текущие статусы `public-release-audit`, Ubuntu и Windows;
3. предложить одноразовое уведомление для exact run;
4. создать задачу только после подтверждения пользователя;
5. отключить её после завершения или supersession.

Пользователь предпочитает проверку раз в 15 минут. Текущая automation platform поддерживает не чаще одного раза в час, поэтому нельзя утверждать, что настроено 15-минутное polling.

## Документация

- `docs/PROJECT_MASTER_CONTEXT.md` — каноническая цель, архитектура и trust model;
- `docs/PROJECT_STATE.md` — текущее operational state;
- `docs/CONTINUATION_PROMPT.md` — полный prompt для продолжения разработки;
- `docs/REAL_LOG_CAPTURE.md` — capture/review/persistence protocol;
- `docs/GUILD_WIDE_COLLECTION_CONTRACT.md` — guild-wide collection gates;
- `evidence/real-data/README.md` — versioned evidence checkpoint;
- `AGENTS.md` — обязательные инструкции агентам.