# CoA Raid Intelligence

Локальное браузерное приложение для подготовки и интеллектуального анализа рейдовых составов FLEX / 10 / 25 / 40.

## Архитектура

```text
Browser → FastAPI → Planner / Catalog / Evidence Pipeline → DuckDB
```

Приложение работает локально на компьютере пользователя. Браузер является основным интерфейсом, Python содержит доменную логику, DuckDB хранит планы и аналитические данные.

## Каноническая модель данных

```text
Raw observation
→ schema fingerprint
→ verified normalization
→ aura-state reconstruction
→ mechanic hypothesis
→ supporting / contradicting evidence
→ corroborated / confirmed mechanic
→ planner scoring
```

Событие журнала боя является наблюдением, а не автоматическим доказательством общей игровой механики.

Основной источник наблюдений:

```text
https://coa.ascensionlogs.gg
```

Маршруты, JSON-поля, типы событий, Spell ID и игровые связи нельзя придумывать. Реальный payload сначала сохраняется неизменяемо, получает SHA-256 и fingerprint схемы. Нормализация разрешена только через проверенный mapping с совпадающим fingerprint.

Канонический planner scoring использует только механики со статусами:

```text
corroborated
confirmed
```

Наблюдения, неподтверждённые гипотезы и исторические статические связи не участвуют в каноническом расчёте.

## Реализовано

- локальная FastAPI-служба;
- браузерный конструктор до 40 слотов;
- FLEX / 10 / 25 / 40;
- расчёт активных слотов и проверок состава в Python;
- каталог классов, специализаций и ролей;
- сохранение, открытие, обновление и удаление планов в DuckDB;
- localhost-only по умолчанию;
- request ID и диагностический журнал;
- реестр источника `coa.ascensionlogs.gg`;
- безопасный probe зарегистрированных маршрутов;
- неизменяемый raw archive с SHA-256;
- импорт локального JSON и HAR;
- безопасный deterministic HAR inventory;
- schema inspection и fingerprint;
- versioned normalization mapping;
- canonical report / encounter / actor / participant / aura events;
- rejects для неполных и неизвестных записей;
- Aura State Engine;
- hypotheses, supporting evidence и contradicting evidence;
- временные и cohort-веса;
- разделение глобальной механики и исполнения конкретной гильдии;
- воспроизводимый verification runner;
- GitHub Actions для Ubuntu и Windows;
- реальный aura checkpoint на encounters `64795` и `64796`;
- exact comparison reconstructed intervals с `debuff_sources`;
- SPA HTML/asset capture и API-route discovery;
- Armory API collector и character-search fallback;
- безопасный Armory HAR importer;
- воспроизводимая HTTP access matrix через GitHub Actions.

Инфраструктура доказательности не означает, что реальные игровые механики уже подтверждены. Для этого нужны реальные нормализованные отчёты и независимые повторяемые observations.

## Проверенное наблюдение по HTTP-доступу

Обычный `urllib` profile и только browser-like headers возвращали `403` для:

```text
/api/reports/public
/api/characters/search
/api/armory/by-name/...
```

Полный same-origin fetch-context profile вернул `200` для всех трёх маршрутов:

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

Проверен полный профиль, но ещё не доказано, какой отдельный header является минимально необходимым и нужна ли cookie, установленная первым успешным API-response. Подробности и ограничения находятся в `docs/PROJECT_STATE.md`.

## Целевой поток автоматического получения логов

Не требуется вручную скачивать и разбирать каждый полный лог.

```text
public reports discovery
→ фильтр phase/location/difficulty/category
→ до 5 reports на категорию
→ encounters
→ нужные analytical endpoints
→ immutable raw archive
→ fingerprint
→ endpoint-specific parser
→ canonical normalization
```

Предпочтение отдаётся специализированным payloads: report, encounters, roster/combatants, aura timeline/detail/uptimes, casts и debuff sources. Полный event stream используется только когда агрегированные endpoints не позволяют проверить конкретную временную или причинную гипотезу.

Много однотипных raw files ожидаемо. Один versioned parser применяется ко всем payloads совпадающей проверенной схемы. Неизвестный fingerprint отклоняется и отправляется на review.

## Запуск

Требования:

```text
Python 3.12+
uv
```

Установка зафиксированных зависимостей:

```powershell
uv sync --frozen --extra dev
```

Полная проверка проекта:

```powershell
uv run python scripts/verify_repo.py
```

Запуск приложения:

```powershell
uv run coa-workbench serve
```

Адрес приложения:

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

`normalize-json` требует mapping со статусом `verified` и совпадающим fingerprint входного payload.

## Правила разработки

Постоянные инструкции для Codex и других агентов находятся в `AGENTS.md`.

Перед изменением кода агент обязан проверить фактическую ветку, состояние PR, тесты, миграции и соответствие документации реальному коду.

Raw HAR, payloads, DuckDB, browser profiles, cookies, authorization headers и access tokens не коммитятся.

## Текущий этап

Активная работа ведётся в Draft PR №7 из `e3/real-log-capture` в `e2/log-evidence-refactor`. Родительский PR №3 остаётся Draft.

Ближайший bounded slice:

1. централизовать проверенный fetch-context profile и persistent same-host cookie jar;
2. покрыть Armory collector unit tests;
3. получить real immutable `armory/character`, `captures` и `talent-grid` payloads;
4. выполнить safe structural inventory и reviewed mappings;
5. автоматизировать выбор до 5 reports на категорию и сбор необходимых encounter endpoints;
6. нормализовать полный report/encounter/roster с actors и participants;
7. повторить evidence checks на других spells/reports и проверить contradicting observations;
8. запустить полный verifier и CI.

Полное фактическое состояние и handoff-промпт находятся в:

```text
docs/PROJECT_STATE.md
docs/CONTINUATION_PROMPT.md
```
