# Фактическое состояние проекта

Дата актуализации: 2026-07-28.

## Репозиторий

- Основная стабильная ветка: `main`.
- Родительская ветка evidence-refactor: `e2/log-evidence-refactor`.
- Активная ветка real-log capture: `e3/real-log-capture`.
- Активный Draft PR: №7, `e3/real-log-capture → e2/log-evidence-refactor`.
- PR №4 с усилением Aura State Engine слит в `e2/log-evidence-refactor`.
- PR №5 с verification runner и GitHub Actions слит в `e2/log-evidence-refactor`.
- Проверки GitHub Actions выполняются на Ubuntu и Windows.

## Реализованный фундамент

- localhost FastAPI-приложение и браузерный конструктор рейда;
- сохранение планов в DuckDB;
- неизменяемый raw archive;
- безопасная детерминированная инвентаризация HAR и инспекция архивированного gzip JSON;
- source registry и безопасный probe;
- schema inspection и fingerprint;
- verified normalization mappings;
- canonical report, encounter, actor, participant и aura events;
- normalization rejects;
- Aura State Engine с обработкой refresh, stacks, duplicate events, нескольких источников и целей;
- различение полного encounter и ограниченного окна наблюдения aura timeline;
- интервалы со статусами `active`, `closed`, `incomplete` и provenance metadata;
- явные причины границ `window_start`, `window_end`, `removed` и `encounter_end`;
- trust states, hypotheses, evidence links и versioned weighting policy;
- миграции `0001`–`0006`;
- compatibility-исполнение миграции `0005` без изменения её исходного checksum;
- единый `scripts/verify_repo.py`;
- CI-проверки Ubuntu и Windows.

## Реальный evidence checkpoint: aura normalization

На локально сохранённых immutable payloads отчёта CoA Logs подтверждены два воспроизводимых single-encounter пути для spell `968746` (`Ninja's Focus`).

### Encounter 64795 — полный timeline

```text
report 2987
encounter 64795
aura_timeline -> canonical events -> Aura State Engine -> debuff_sources intervals
```

Проверенный результат:

- schema fingerprint: `2994424cb95c2a7e1997651226b7942367ebe77003e0f4614aae5da4920f8b98`;
- mapping: `coa-aura-timeline-single-encounter-v1`, status `verified`;
- `buff_applied -> APPLIED`;
- `buff_removed -> REMOVED`;
- одна пустая baseline-строка корректно исключена;
- 6 canonical aura events;
- 3 восстановленных интервала;
- 3 эталонных интервала `debuff_sources`;
- точное совпадение интервалов;
- 0 rejects;
- 0 anomalies;
- provenance сохраняет hash и archive path обоих payloads.

### Encounter 64796 — оконный timeline

```text
report 2987
encounter 64796
window 10382–38265 ms
full encounter duration 117215 ms
observed window duration 27883 ms
```

Проверенный результат:

- schema fingerprint: `d8b6dd869d6adf8f3433f9e285b8270cd1aa8d640839c915a42c80b2211cbf0b`;
- baseline в `10382` с `active_targets=1` восстановлен как начало интервала с причиной `window_start`;
- `buff_removed` в `14970` корректно закрывает первый интервал;
- `buff_applied` в `29458` открывает второй интервал;
- отсутствие remove внутри окна корректно закрывает второй интервал на `38265` с причиной `window_end`;
- 3 canonical aura events, включая синтетическое boundary event;
- 2 восстановленных интервала;
- 2 эталонных интервала `debuff_sources`;
- точное совпадение интервалов;
- 0 rejects;
- 0 anomalies.

Оба наблюдения подтверждают корректность reviewed mapping и реконструкции для полного и оконного single-encounter aura timeline. Это corroborating evidence для технической нормализации, но не для игровой механики эффекта.

Checkpoint не подтверждает числовое описание `Ninja's Focus`, его обязательность, stacking, overwrite, эквивалентность похожим эффектам или стратегическую критичность.

## Канонические ограничения

- Статические historical mappings имеют статус `legacy_unverified`.
- Они не участвуют в каноническом planner scoring.
- Непроверенный normalization mapping отклоняется.
- Только `corroborated` и `confirmed` механики могут использоваться для рекомендаций.
- Инфраструктура evidence pipeline не является подтверждением игровых механик.
- Verified schema mapping не повышает trust state игровой механики автоматически.
- Corroborated normalizer behavior не считается corroborated mechanic behavior.

## Воспроизводимая проверка

```bash
uv sync --frozen --extra dev
uv run python scripts/verify_repo.py
```

Verifier запускает Ruff, полный pytest, doctor, CLI smoke tests, trust gates и двукратную инициализацию временной DuckDB. Рабочая `data/warehouse/coa.duckdb` не используется. JSON-отчёт записывается в `artifacts/verification-report.json`.

Реальный aura checkpoint воспроизводится командой:

```bash
python scripts/validate_aura_capture.py \
  --timeline <timeline-payload-hash> \
  --reference <debuff-sources-payload-hash> \
  --encounter-id <encounter-id>
```

Последняя проверка ветки после поддержки window boundaries: GitHub Actions run №26, Ubuntu и Windows — success.

## Незавершённая контрольная точка

Выполнено частично:

1. реальный immutable payload CoA Logs — выполнено локально;
2. verified mapping фактической single-encounter aura schema — выполнено;
3. нормализованные реальные encounter и aura events — выполнено для двух aura payloads;
4. восстановленные реальные aura intervals — выполнено для полного и оконного timeline;
5. независимое точное сравнение с готовыми `debuff_sources` intervals — выполнено для двух encounters;
6. повторяемость normalizer behavior на разных encounters и temporal shapes — выполнено.

До полного evidence checkpoint остаются:

1. нормализация полного реального report/encounter/roster с actors и participants;
2. повторение проверки на других spells и reports;
3. гипотезы stacking, overwrite и coexistence;
4. независимые supporting observations игровых механик;
5. проверенные contradicting observations;
6. критичность эффекта по описанию, распространённости и редкости провайдеров;
7. канонический вывод, воспроизводимый по dataset, policy и inference versions.

До выполнения этих условий PR №3 остаётся Draft и не сливается в `main`.
