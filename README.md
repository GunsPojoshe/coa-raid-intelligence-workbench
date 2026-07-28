# CoA Raid Intelligence Workbench

Локальное браузерное приложение для подготовки рейдовых составов и evidence-first анализа Classless / Ascension WoW.

## Главная цель

Система объединяет:

- конструктор рейда FLEX / 10 / 25 / 40;
- хранение планов в DuckDB;
- автоматический сбор наблюдений с `coa.ascensionlogs.gg`;
- immutable raw archive;
- schema fingerprinting;
- verified normalization;
- Aura State Engine;
- hypotheses, supporting и contradicting evidence;
- trust-aware planner scoring;
- объяснимые рекомендации с provenance.

Канонический принцип:

```text
combat-log event = observation
combat-log event != proof of a general game mechanic
```

Полный контекст проекта находится в:

```text
docs/PROJECT_MASTER_CONTEXT.md
```

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
-> immutable raw observation
-> SHA-256 + schema fingerprint
-> reviewed verified mapping
-> canonical normalized records
-> deterministic state reconstruction
-> mechanic hypothesis
-> supporting / contradicting evidence
-> corroborated / confirmed mechanic
-> planner scoring
```

Только `corroborated` и `confirmed` mechanics допускаются в canonical scoring.

## Реализовано

### Product foundation

- localhost FastAPI runtime;
- браузерный конструктор до 40 слотов;
- FLEX / 10 / 25 / 40;
- class/spec/role catalog;
- Python validation;
- DuckDB persistence;
- create/read/update/delete raid plans;
- request IDs и diagnostic logging;
- localhost-only bind по умолчанию.

### Evidence foundation

- source registry;
- safe source probe;
- immutable raw archive;
- deduplicated payload body + separate observations;
- JSON/HAR import;
- privacy-safe deterministic HAR inventory;
- archived gzip JSON inspection;
- schema fingerprinting;
- verified mapping gate;
- canonical report/encounter/actor/participant/aura records;
- rejects;
- Aura State Engine;
- hypotheses и evidence links;
- trust/weighting policies;
- migrations `0001`–`0006`;
- reproducible repository verifier;
- GitHub Actions Ubuntu + Windows.

### Real observations

- verified full same-origin HTTP profile `coa-fetch-context-v1`;
- real Armory identity for `Gunspojoshe / Vol'Jin`;
- real immutable `armory_api_by_name` payload;
- real immutable `armory_api_captures` payload;
- real aura normalization checkpoints for encounters `64795` and `64796`;
- exact reconstructed interval comparison with `debuff_sources` for spell `968746`.

Текущие ограничения и hashes описаны в `docs/PROJECT_STATE.md` и `docs/PROJECT_MASTER_CONTEXT.md`.

## Проверенный HTTP profile

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

Проверен только полный profile. Не доказано минимальное подмножество headers и необходимость cookie/order dependency для fresh Armory-first session.

## Текущий этап

Активная работа:

```text
PR #7: e3/real-log-capture -> e2/log-evidence-refactor
PR #3: e2/log-evidence-refactor -> main
```

Оба PR остаются Draft.

Ближайший bounded plan:

1. исправить Ruff blockers и вернуть green CI;
2. добавить endpoint-isolated Armory capture;
3. получить `armory/character/{id}` и `talent-grid/{class}` payloads;
4. выполнить safe structural review и mappings;
5. автоматизировать bounded report discovery;
6. нормализовать полный report/encounter/roster slice;
7. расширить supporting и contradicting evidence;
8. интегрировать только corroborated/confirmed mechanics в planner.

## Требования

```text
Python >= 3.12
uv
```

Locked environment:

```powershell
uv sync --frozen --extra dev
```

Полная проверка:

```powershell
uv run python scripts/verify_repo.py
```

Запуск приложения:

```powershell
uv run coa-workbench serve
```

Адрес:

```text
http://127.0.0.1:8000
```

OpenAPI:

```text
http://127.0.0.1:8000/docs
```

## Основные команды

```powershell
uv run coa-workbench doctor --project-root .
uv run coa-workbench validate-config --path config/raid_profiles.yaml
uv run coa-workbench init-db --database data/warehouse/coa.duckdb --migrations migrations
uv run coa-workbench probe-source public_home
uv run coa-workbench import-json <payload.json>
uv run coa-workbench import-har <browser-export.har>
uv run coa-workbench inventory-har <browser-export.har> --output <inventory.json>
uv run coa-workbench inspect-json <payload.json>
uv run coa-workbench inspect-archived <payload-path-or-hash>
uv run coa-workbench normalize-json <payload.json> --mapping <verified-mapping.json>
uv run coa-workbench serve
uv run pytest
```

## Privacy

Никогда не коммитить:

- HAR;
- raw payloads;
- local DuckDB;
- cookies;
- Authorization headers;
- tokens;
- browser profiles;
- unsanitized private query values;
- absolute local paths containing usernames.

## Документация

```text
AGENTS.md
README.md
docs/PROJECT_MASTER_CONTEXT.md
docs/PROJECT_STATE.md
docs/CONTINUATION_PROMPT.md
docs/REAL_LOG_CAPTURE.md
docs/ADR_012_LOG_EVIDENCE_TRUTH_MODEL.md
```
