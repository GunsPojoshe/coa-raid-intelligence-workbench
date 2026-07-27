# CoA Raid Intelligence

Локальное браузерное приложение для подготовки рейдовых составов FLEX / 10 / 25 / 40.

## Архитектурный статус

Excel, Power Query и VBA больше не являются частью рабочего продукта. Историческая книга v9 используется только как источник миграции правил и проверочных данных; приложение не открывает, не изменяет и не требует Excel.

```text
Browser → FastAPI → Planner / Catalog / Analytics → DuckDB / Parquet
```

## Запуск

```powershell
uv sync --extra dev
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

## Реализованный вертикальный срез

- локальная FastAPI-служба;
- браузерный конструктор до 40 слотов;
- FLEX / 10 / 25 / 40;
- ActiveSlot рассчитывается в Python;
- проверка повторного игрока и полноты class/spec;
- каталог из 70 пар класс–спек–роль;
- сохранение, открытие, обновление и удаление планов в DuckDB;
- каталог из 45 эффектов, мигрированный из замороженной выгрузки v9;
- расчёт покрытия эффектов текущим составом;
- разрез покрытия по категориям и приоритетам;
- объяснимый Top-3 советник специализаций;
- localhost-only по умолчанию.

## Аналитика покрытия

Канонический источник первого среза:

```text
baseline/tables/EffectsReferenceTable.csv
```

Файл является замороженной CSV-выгрузкой из v9. Рабочее приложение не открывает Excel.

Советник ранжирует специализации по новым отсутствующим эффектам:

```text
Критично     = 100
Важно        = 10
Опционально  = 1
```

Алгоритм `missing-effect-priority-v1` не использует ролевые квоты, потому что целевые ограничения ролей ещё не утверждены. Каждая рекомендация показывает новые эффекты и разложение результата по приоритетам.

API:

```text
GET  /api/catalog/effects
POST /api/plans/preview
```

## Команды

```powershell
uv run coa-workbench doctor --project-root .
uv run coa-workbench validate-config --path config/raid_profiles.yaml
uv run coa-workbench init-db --database data/warehouse/coa.duckdb --migrations migrations
uv run coa-workbench serve
uv run pytest
```

## Что больше не входит в runtime

- Excel workbook как интерфейс;
- формулы Excel как расчётное ядро;
- Power Query;
- VBA;
- изменение `.xlsx` из Python;
- обязательное наличие Microsoft Excel.

Архивные workbook-материалы сохраняются только как evidence миграции и не являются частью пользовательского контура.
