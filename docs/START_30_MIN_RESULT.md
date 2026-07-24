# Результат первого implementation slice

## Выполнено

1. **Evidence freeze**
   - исходная книга v9 скопирована в архив без изменения байтов;
   - SHA-256: `d2f719c2875ad5aa1b1413daee54aaa36e4d52068bfe2a898df8fcb8b296eb83`;
   - проектные документы также включены в source manifest.

2. **Инвентаризация workbook**
   - 16 листов;
   - 4 355 формульных ячеек;
   - 9 Excel-таблиц;
   - 70 комбинаций класс–специализация;
   - 45 концептуальных эффектов;
   - defined names отсутствуют.

3. **Известные ошибки baseline**
   - 282 сохранённых `#NAME?`:
     - `ТЕХ_Расчет`: 140;
     - `КАТАЛОГ СПЕКОВ`: 70;
     - `ТЕХ_Подсказки`: 70;
     - `СРАВНЕНИЕ СПЕКОВ`: 2;
   - openpyxl сообщает, что при сохранении удалит extension-based Data Validation / Conditional Formatting; поэтому архив v9 является строго read-only;
   - количество timeline-событий остаётся несогласованным: 12 148 016 в книге против 12 147 472 в проектной документации, разница 544.

4. **Версионированный legacy export**
   - все 9 таблиц выгружены в UTF-8 CSV;
   - для каждого CSV рассчитан SHA-256;
   - повторный CLI-запуск подтвердил идентичные hashes.

5. **Python skeleton**
   - CLI: `doctor`, `validate-config`, `freeze-baseline`, `init-db`;
   - форматная модель FLEX / 10 / 25 / 40;
   - единый 40-элементный `ActiveSlot` mask;
   - конфигурация профилей без выдуманных ролевых ограничений;
   - пустой Endpoint Registry до фактической проверки маршрутов.

6. **Storage contract**
   - первая миграция содержит 21 таблицу для raw, canonical, evidence, plans, snapshots, jobs и review issues;
   - SQL прошёл статический parse через SQLite как синтаксическую дополнительную проверку;
   - реальный DuckDB integration test подготовлен и условно пропущен, поскольку пакет DuckDB отсутствует в текущем runtime.

7. **Тесты**
   - 8 passed;
   - 1 skipped (`duckdb` dependency unavailable);
   - проверены форматы, ActiveSlot, конфигурация, frozen baseline, таблицы и migration contract.

## Осознанно не выполнено

- v9 не пересохранена и не изменена;
- заполненный эталонный состав на 25 не выдуман: загруженная книга хранит 25 строк, но считает 0 игроков;
- FLEX range и role min/max не зафиксированы без утверждённых правил;
- ошибки `#NAME?` не исправлялись до появления regression fixture;
- API routes не объявлены рабочими без скриптов, URL и примеров payload.

## Следующий issue

`E0-001 — Approved 25-player regression fixture`

После его приёмки можно безопасно создавать workbook v10 с 40 физическими строками, `RaidFormat`, `TargetSize`, `ActiveSlot` и проверкой неизменности результата для формата 25.
