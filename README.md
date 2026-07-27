# CoA Raid Intelligence

Локальное браузерное приложение для подготовки и последующего интеллектуального анализа рейдовых составов FLEX / 10 / 25 / 40.

## Текущий архитектурный статус

Рабочий пользовательский контур:

```text
Browser → FastAPI → Planner / Catalog → DuckDB
```

Excel, Power Query и VBA не входят в runtime. Историческая книга v9 и производные CSV используются только как legacy-материал для миграции, аудита и forensic-сравнения.

Текущая разработка в ветке `e2/log-evidence-refactor` переводит игровую аналитику на evidence-first модель:

```text
Raw observation
→ canonical normalization
→ aura-state reconstruction
→ hypothesis
→ supporting / contradicting evidence
→ corroborated / confirmed mechanic
→ planner scoring
```

Combat-log события являются наблюдениями. Они не считаются автоматическим доказательством общей игровой механики.

## Источник данных и доверие

Основной источник наблюдений:

```text
https://coa.ascensionlogs.gg
```

Маршруты, JSON-поля, типы событий, Spell ID и игровые связи нельзя придумывать. Реальный payload сначала сохраняется неизменяемо, получает SHA-256 и fingerprint схемы. Нормализация разрешена только через явно проверенный mapping с совпадающим fingerprint.

Канонический planner scoring может использовать только механики со статусами:

```text
corroborated
confirmed
```

Наблюдения, candidate-гипотезы и legacy-связи не должны попадать в канонический расчёт.

## Legacy-аналитика

В репозитории сохраняются:

- каталог из 70 legacy-пар класс–спек–роль;
- каталог из 45 эффектов из замороженной CSV-выгрузки v9;
- прежний алгоритм `legacy-missing-effect-priority-v1`.

Эти данные классифицированы как:

```text
legacy_unverified
```

По умолчанию legacy coverage и Top-N отключены. Они доступны только для forensic-сравнения при явном флаге:

```text
COA_ENABLE_LEGACY_EFFECTS=1
```

Даже при включённом флаге результат остаётся неканоническим.

## Реализованный localhost-baseline

- локальная FastAPI-служба;
- браузерный конструктор до 40 слотов;
- FLEX / 10 / 25 / 40;
- ActiveSlot рассчитывается в Python;
- проверка повторного игрока и полноты class/spec;
- каталог классов, специализаций и ролей;
- сохранение, открытие, обновление и удаление планов в DuckDB;
- localhost-only по умолчанию;
- request ID и диагностический журнал.

## Evidence-refactor в разработке

В ветке `e2/log-evidence-refactor` развиваются:

- реестр источника `coa.ascensionlogs.gg`;
- безопасный probe проверяемых маршрутов;
- неизменяемый raw archive с SHA-256;
- импорт локального JSON и HAR;
- schema inspection и fingerprint;
- versioned normalization mapping;
- canonical report / encounter / actor / participant / aura events;
- rejects для неполных и неизвестных записей;
- Aura State Engine;
- модель hypotheses, supporting evidence и contradicting evidence;
- временные и cohort-веса;
- разделение глобальной механики и гильдейского исполнения.

Этот контур ещё не означает, что реальные игровые механики уже подтверждены. До загрузки и анализа реальных логов он является инфраструктурой доказательности.

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

Запуск приложения:

```powershell
uv run coa-workbench serve
```

По умолчанию приложение доступно только на этом компьютере:

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

## Правила разработки для Codex и других агентов

Постоянные инструкции находятся в:

```text
AGENTS.md
```

Перед изменением кода агент обязан проверить фактическую ветку, состояние репозитория, тесты, миграции и соответствие документации коду.

## Что не входит в runtime

- Excel workbook как интерфейс;
- формулы Excel как расчётное ядро;
- Power Query;
- VBA;
- изменение `.xlsx` из Python;
- обязательное наличие Microsoft Excel.

Архивные workbook-материалы сохраняются только как legacy evidence миграции и не являются источником канонической игровой истины.

## Активная ветка и PR

Текущий evidence-рефакторинг:

```text
branch: e2/log-evidence-refactor
PR: #3 → main
status: Draft
```

PR №3 не должен переводиться в Ready и сливаться до достижения контрольной точки evidence pipeline.
