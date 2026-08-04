# CoA Raid Intelligence Workbench

Локальная evidence-first платформа рейдовой аналитики исключительно для **Conquest of Azeroth**.

## Что строим

Проект объединяет:

1. **Raid Planner** — работа с фактической явкой, составами FLEX / 10 / 25 / 40 и ручными решениями РЛ.
2. **Raid Intelligence** — воспроизводимый сбор и анализ CoA Ascension Logs, Armory, talent-grid, characters, rankings, statistics и guild data.
3. **Encounter-aware roster completion** — объяснимый добор и замены под текущий состав и конкретных боссов.

Главный вопрос системы:

> Почему конкретный человек нужен именно текущему составу?

## Каноническая граница

Проект не является системой для Bronzebeard или Classless Ascension.

Не входят в текущую CoA-модель:

- Mystic Enchants;
- Hero Architect;
- freeform classless ability selection;
- Bronzebeard-specific role и mechanic rules;
- shared Ascension FAQ claims без exact CoA evidence.

Полная граница: `docs/COA_DOMAIN_BOUNDARY.md`.

Целевой продукт: `docs/COA_TARGET_PRODUCT_DEFINITION.md`.

## Evidence-first правило

```text
combat-log event = observation
combat-log event != proof of a mechanic
class/spec presence != verified capability coverage
shared Ascension text != CoA mechanic proof
```

В planner scoring допускаются только mechanics со статусом `corroborated` или `confirmed`.

## Продуктовый контекст

У гильдии есть ядро примерно из 15–20 постоянных игроков, но явка меняется. На рейд может прийти 15, 18, 20 или другое количество людей.

Система должна учитывать:

- кто реально пришёл;
- как эти люди играли раньше;
- какие роли и билды они реально использовали;
- что требует конкретный энкаунтер;
- что закрыто надёжно, слабо или не закрыто;
- кого добавить или заменить;
- альтернативные варианты состава и последствия.

Конечная цель — не один постоянный `optimal BiS 25 roster`, а динамическое управление составом под фактическую явку.

## Текущий verified baseline

```text
public reports: 6454
unique public report IDs: 6454
exact Argentum label reports: 17
guild identity verified: true
private selected baseline: 17 unique reports
full-crawl collection contract reviewed: true
migrations: 0001–0008
```

Guild-search:

```text
route/schema verified: true
limit result counts: 1 / 7 / 7
limit truncation semantics verified: true
```

Progression:

```text
route candidate: /api/guilds/progression
call class: generic_helper_call
HTTP method candidate: POST
method candidate unambiguous: true
helper identity resolved: false
request payload mapping resolved: false
ready for bounded route probe: false
```

## Provisional raid utility baseline

`docs/COA_RAID_UTILITY_BASELINE_2026-08-02.md` фиксирует supplied working reference:

```text
source SHA-256: adbb2f7f06d750ddad4d981cca3f22b3141f471e8f9819e87f528f357fabdddd
class cards: 28
class/spec associations: 87
unique specialization labels: 67
utility rows: 187
observed in latest 30-log sample: 132
zero observations in sample: 55
```

Это не полный проверенный каталог 69 специализаций и не input для planner scoring. Каждая возможность требует отдельной проверки CoA логами.

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
-> trust decision
-> explainable raid-leader recommendation
```

## Реализованный фундамент

- localhost FastAPI runtime;
- raid plans and CRUD in DuckDB;
- immutable content-addressed raw archive;
- retrieval observations;
- JSON/HAR privacy-safe tooling;
- schema fingerprints and reviewed mapping gates;
- report/encounter/actor/participant/aura records;
- Aura State Engine;
- hypotheses and evidence links;
- selected verified Armory and talent-grid mappings;
- migrations `0001`–`0008`;
- Ubuntu/Windows verification;
- public-release audit.

## Current helper-definition stage

Implemented:

```text
src/coa_workbench/collector/guild_progression_helper_definition_command.py
src/coa_workbench/collector/guild_progression_helper_definition_index.py
src/coa_workbench/collector/guild_progression_helper_definition_inventory.py
scripts/inventory_guild_progression_helper_definition.py
tests/unit/test_guild_progression_helper_definition_command.py
tests/unit/test_guild_progression_helper_definition_index.py
tests/unit/test_guild_progression_helper_definition_inventory.py
```

The next bounded step is local offline execution against exact private artifacts, validation of all 36 checks and versioning of only the scalar-free public receipt.

No guessed request to `/api/guilds/progression` is allowed.

## Current decision boundary

```text
helper-definition inventory implementation complete: true
helper-definition inventory executed on private artifacts: false
helper-definition receipt versioned: false
helper-definition review complete: false
progression helper identity resolved: false
progression request payload mapping resolved: false
ready for bounded progression route probe: false
pagination semantics verified: false
termination semantics verified: false
completeness verified: false
ready for full guild crawl: false
ready for multi-report character graph: false
ready for performance model: false
ready for encounter-aware roster completion: false
planner scoring allowed: false
```

## Установка и проверка

```text
Python >= 3.12
uv
```

```powershell
uv sync --frozen --extra dev
uv run python scripts/verify_repo.py
```

Запуск:

```powershell
uv run coa-workbench serve
```

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/docs
```

## Branches

```text
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

## Data policy

Versioned:

- code and tests;
- migrations;
- reviewed mappings/reviews;
- canonical documentation;
- approved provisional references;
- scalar-free receipts.

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

Do not commit raw payloads, private receipts, source guild/report IDs, private queries, raw JavaScript, credentials, cookies, tokens, browser profiles, `.env` or unsanitized HAR.

## Документация

- `docs/COA_DOMAIN_BOUNDARY.md` — каноническая CoA-only граница;
- `docs/COA_TARGET_PRODUCT_DEFINITION.md` — целевая формулировка продукта;
- `docs/COA_RAID_UTILITY_BASELINE_2026-08-02.md` — provisional utility baseline;
- `docs/PROJECT_MASTER_CONTEXT.md` — архитектура и долгосрочный контекст;
- `docs/PROJECT_STATE.md` — текущее operational state;
- `docs/CONTINUATION_PROMPT.md` — prompt для продолжения разработки;
- `docs/REAL_LOG_CAPTURE.md` — capture/review/persistence protocol;
- `docs/GUILD_WIDE_COLLECTION_CONTRACT.md` — guild-wide collection gates;
- `evidence/real-data/README.md` — versioned evidence checkpoint;
- `AGENTS.md` — обязательные инструкции агентам.
