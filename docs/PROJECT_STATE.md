# Фактическое состояние проекта

Дата актуализации: 2026-07-27.

## Репозиторий

- Основная стабильная ветка: `main`.
- Активная ветка evidence-refactor: `e2/log-evidence-refactor`.
- Активный интеграционный PR: №3, `e2/log-evidence-refactor → main`, Draft.
- PR №4 с усилением Aura State Engine слит в `e2/log-evidence-refactor`.
- PR №5 с verification runner и GitHub Actions слит в `e2/log-evidence-refactor`.
- Проверки GitHub Actions выполняются на Ubuntu и Windows.

## Реализованный фундамент

- localhost FastAPI-приложение и браузерный конструктор рейда;
- сохранение планов в DuckDB;
- неизменяемый raw archive;
- source registry и безопасный probe;
- schema inspection и fingerprint;
- verified normalization mappings;
- canonical report, encounter, actor, participant и aura events;
- normalization rejects;
- Aura State Engine с обработкой refresh, stacks, duplicate events, нескольких источников и целей;
- интервалы со статусами `active`, `closed`, `incomplete` и provenance metadata;
- trust states, hypotheses, evidence links и versioned weighting policy;
- миграции `0001`–`0006`;
- compatibility-исполнение миграции `0005` без изменения её исходного checksum;
- единый `scripts/verify_repo.py`;
- CI-проверки Ubuntu и Windows.

## Канонические ограничения

- Статические historical mappings имеют статус `legacy_unverified`.
- Они не участвуют в каноническом planner scoring.
- Непроверенный normalization mapping отклоняется.
- Только `corroborated` и `confirmed` механики могут использоваться для рекомендаций.
- Инфраструктура evidence pipeline не является подтверждением игровых механик.

## Воспроизводимая проверка

```bash
uv sync --frozen --extra dev
uv run python scripts/verify_repo.py
```

Verifier запускает Ruff, полный pytest, doctor, CLI smoke tests, trust gates и двукратную инициализацию временной DuckDB. Рабочая `data/warehouse/coa.duckdb` не используется. JSON-отчёт записывается в `artifacts/verification-report.json`.

## Незавершённая контрольная точка

До завершения evidence checkpoint отсутствуют подтверждённые в репозитории результаты следующих этапов:

1. реальный сохранённый payload CoA Logs;
2. verified mapping для его фактической схемы;
3. нормализованный реальный report и encounter;
4. связанные actors, participants и aura events;
5. восстановленные реальные aura intervals;
6. повторяемая механика с независимыми supporting observations;
7. проверенные contradicting observations;
8. канонический вывод, воспроизводимый по dataset, policy и inference versions.

До выполнения этих условий PR №3 остаётся Draft и не сливается в `main`.
