# CoA Raid Intelligence Workbench

Локальное браузерное приложение для подготовки рейдовых составов и evidence-first анализа Classless / Ascension WoW.

## Цель

Проект объединяет:

1. **Raid Planner** — конструктор FLEX / 10 / 25 / 40, валидация состава и хранение планов в DuckDB.
2. **Raid Intelligence** — воспроизводимый сбор и анализ наблюдений с `coa.ascensionlogs.gg`.

Канонический принцип:

```text
combat-log event = observation
combat-log event != proof of a general game mechanic
```

В planner scoring допускаются только механики со статусом `corroborated` или `confirmed`.

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
-> SHA-256 + schema fingerprint
-> reviewed mapping
-> verified parser normalization
-> deterministic reconstruction
-> immutable observations
-> supporting / contradicting evidence
-> corroborated / confirmed mechanic
-> planner scoring
```

## Текущий статус

Актуализировано **31 июля 2026 года**.

```text
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

Green baseline перед documentation refresh:

```text
commit: 00bae9ac4deb457eebc41cd50bdff6305bf3fe42
workflow: Verify repository
run: #372
Ubuntu: success
Windows: success
```

### Реализованный фундамент

- localhost FastAPI runtime и browser raid constructor;
- class/spec/role catalog и Python validation;
- DuckDB persistence и CRUD raid plans;
- immutable raw archive и retrieval observations;
- JSON/HAR safe import и privacy-safe inventory;
- schema fingerprints и verified mapping gates;
- canonical report/encounter/actor/participant/aura records;
- Aura State Engine;
- hypotheses, evidence links и trust policies;
- migrations `0001`–`0008`;
- Ubuntu/Windows repository verification.

## Завершённый report/encounter slice

```text
normalized:
  reports:       2
  encounters:   15
  actors:       31
  participants: 31
  aura_events:   0
  rejects:       0

reconstructed:
  reports:       1
  encounters:   14
  actors:       31
  participants: 31
  aura_events:   0
  rejects:       0

persisted through 0007:
  canonical entity observations: 77
  transaction committed: true
```

## Combatants persistence

Exact payload candidate extraction была вручную промотирована и сохранена как immutable parser observations через migration `0008_combatants_observation_persistence`.

```text
persisted observations: 1343
actor/build observations: 1339
linked actors: 11
persistence runs: 1
integrity checks: 14/14
core actor mutations: 0
```

Read models доступны для parser observations и actor/build observations. Это не подтверждает companion-addon provenance, nested identifier semantics, игровые механики или planner scoring.

## Exhaustive public-report manifest

Промотированный pagination contract использует:

```text
route: /api/reports/public
limit: 25
sortBy: created_at
sortOrder: desc
```

Завершённый scalar-free receipt:

```text
file: evidence/real-data/argentum-public-report-manifest.json
pages: 259
reports: 6454
unique report IDs: 6454
duplicates: 0
terminal page reports: 4
integrity checks: 19/19
```

Guild-field summary:

```text
reports with non-null guild ID and non-empty guild name: 1171
distinct guild identity pairs: 88
exact Argentum label reports: 17
distinct non-null guild IDs for exact label: 1
```

Это разрешает **ручную проверку guild identity**, но не подтверждает её автоматически:

```text
guild identity verified: false
ready for guild identity review: true
ready for guild filtering: false
ready for full guild crawl: false
planner scoring allowed: false
```

## Текущая граница

Разрешено:

- воспроизводить exact reviewed parser slices;
- читать persisted combatants parser/build observations;
- использовать exhaustive manifest receipt как доказательство completeness captured snapshot;
- локально проверять 17 exact `Argentum` rows и связанный с ними один guild ID;
- версионировать scalar-free evidence receipts.

Не разрешено:

- считать label `Argentum` достаточным подтверждением source guild identity;
- включать guild filtering до отдельного review/promotion receipt;
- публиковать private manifest scalars;
- изменять core actor rows из addon-derived data;
- считать nested IDs или display names глобально уникальными;
- использовать observed/parser data в planner scoring;
- считать report slice завершённым по aura evidence.

## Ближайший bounded этап

1. локально проверить 17 exact `Argentum` manifest rows;
2. проверить согласованность единственного non-null guild ID;
3. при наличии достаточного evidence выпустить scalar-free guild-identity review/promotion receipt;
4. только затем включить deterministic guild filtering;
5. сформировать guild report manifest и начать per-report capture.

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

## Data policy

В Git версионируются код, tests, migrations, reviewed mappings, документация и scalar-free receipts.

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

Не коммитить raw payloads, HAR, DuckDB/WAL, private batches, cookies, Authorization headers, tokens, browser profiles, `.env` или абсолютные локальные пути с username.

## Документация

- `docs/PROJECT_MASTER_CONTEXT.md` — архитектура и trust model;
- `docs/PROJECT_STATE.md` — изменяемое фактическое состояние;
- `docs/REAL_LOG_CAPTURE.md` — capture/normalization/persistence protocol;
- `docs/CONTINUATION_PROMPT.md` — стартовый контекст;
- `docs/GUILD_WIDE_COLLECTION_CONTRACT.md` — guild-wide collection boundary;
- `evidence/real-data/README.md` — versioned evidence checkpoint;
- `AGENTS.md` — инструкции агентам.
