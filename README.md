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
- schema inspection и fingerprint;
- versioned normalization mapping;
- canonical report / encounter / actor / participant / aura events;
- rejects для неполных и неизвестных записей;
- Aura State Engine;
- hypotheses, supporting evidence и contradicting evidence;
- временные и cohort-веса;
- разделение глобальной механики и исполнения конкретной гильдии;
- воспроизводимый verification runner;
- GitHub Actions для Ubuntu и Windows.

Инфраструктура доказательности не означает, что реальные игровые механики уже подтверждены. Для этого нужны реальные нормализованные отчёты и независимые повторяемые observations.

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
uv run coa-workbench inspect-json <payload.json>
uv run coa-workbench normalize-json <payload.json> --mapping <verified-mapping.json>
uv run coa-workbench serve
uv run pytest
```

`normalize-json` требует mapping со статусом `verified` и совпадающим fingerprint входного payload.

## Правила разработки

Постоянные инструкции для Codex и других агентов находятся в `AGENTS.md`.

Перед изменением кода агент обязан проверить фактическую ветку, состояние PR, тесты, миграции и соответствие документации реальному коду.

## Текущий этап

Активный evidence-refactor ведётся через PR №3 в `main`. До завершения контрольной точки он остаётся Draft.

Контрольная точка требует:

1. реальный payload CoA Logs;
2. неизменяемое raw-хранение;
3. зафиксированный fingerprint;
4. verified mapping;
5. нормализованные report, encounter, actors, participants и aura events;
6. восстановленные интервалы аур;
7. минимум одну повторяемую механику с независимыми supporting observations;
8. проверку contradicting evidence;
9. воспроизводимый результат с provenance.
