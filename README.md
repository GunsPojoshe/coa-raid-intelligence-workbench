# CoA Raid Intelligence Workbench

Локальное браузерное приложение для подготовки рейдовых составов и evidence-first анализа Classless / Ascension WoW.

## Цель

Проект объединяет два контура:

1. **Raid Planner** — конструктор рейда FLEX / 10 / 25 / 40, валидация состава и хранение планов в DuckDB.
2. **Raid Intelligence** — воспроизводимый сбор и анализ наблюдений с `coa.ascensionlogs.gg` без подмены фактов источника локальными выводами.

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
-> mechanic hypothesis
-> supporting / contradicting evidence
-> corroborated / confirmed mechanic
-> planner scoring
```

## Текущий подтверждённый статус

Operational baseline актуализирован **30 июля 2026 года**.

Активная ветка и PR:

```text
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

Последний green baseline перед обновлением документации:

```text
commit: 2b92b3d02339a3748d146c1b15a6718f84494e6f
workflow: Verify repository
run: #280
Ubuntu: success
Windows: success
```

### Реализованный product foundation

- localhost FastAPI runtime;
- браузерный конструктор до 40 слотов;
- FLEX / 10 / 25 / 40;
- class/spec/role catalog;
- Python validation;
- create/read/update/delete raid plans;
- DuckDB persistence;
- request IDs и diagnostic logging;
- localhost-only bind по умолчанию.

### Реализованный evidence foundation

- source registry и safe probes;
- immutable content-addressed raw archive;
- отдельные retrieval observations при дедупликации payload body;
- JSON/HAR import и privacy-safe inventory;
- schema inspection и fingerprints;
- versioned verified mappings;
- canonical report/encounter/actor/participant/aura records;
- normalization rejects;
- Aura State Engine;
- hypotheses и evidence links;
- trust/weighting policies;
- migrations `0001`–`0007`;
- repository verifier;
- GitHub Actions на Ubuntu и Windows.

### Реальные данные, прошедшие gates

- verified Armory character и talent-grid mappings;
- verified bounded public-report discovery mapping;
- archive-only SPA route inventory;
- immutable capture трёх report-slice endpoints;
- verified mappings:
  - `config/mappings/coa_report_detail_v1.json`;
  - `config/mappings/coa_encounter_detail_v1.json`;
- selected-parser normalization;
- deterministic reconstruction;
- selected-parser persistence в локальный DuckDB;
- bounded structural review и candidate extraction для `combatants-info`.

Report/encounter pipeline завершён для exact reviewed payloads:

```text
normalized input:
  reports:      2
  encounters:  15
  actors:      31
  participants:31
  aura_events: 0
  rejects:     0

reconstructed output:
  reports:      1
  encounters:  14
  actors:      31
  participants:31
  aura_events: 0
  rejects:     0

persisted:
  canonical entity observations: 77
  transaction committed: true
```

Combatants candidate extraction для exact payload:

```text
source matches:       1350
output observations:  1343
deduplicated matches: 7
linked actors:        11
integrity checks:     12/12
core mutations:       0
```

Этот результат подтверждает parser/linkage для exact payload. Он **не** подтверждает companion-addon provenance, nested collection semantics, игровые механики или planner scoring.

## Observed report routes

```text
/api/reports/{template}
/api/reports/{template}/encounters/{template}
/api/reports/{template}/encounters/{template}/combatants-info
```

Отдельный `/roster` route не наблюдался.

Exact bindings:

```text
report_detail
payload:      161739896f0b8321f884bcc24d1896efb894a9c6e05166269189f9871c64cba9
fingerprint:  3d533a4178b67957bbd31544ddf5484bd5959635ebd5edcdd0c7689a4bace216

encounter_detail
payload:      955437d6c9c287cc7db280dd2388b88603af2785508061b95c7811dcd272fe22
fingerprint:  567f36824efb37a29b835df01ce9b1fcc79eae57d6230202d16a6265c6ca0e85

combatants_info
payload:      45672e0f0ff9eb461c575bdd38385795daa6326378bc3f8ad51474276140dc14
fingerprint:  41d6d15422c668f83d2ccae1ec0ff2969671861f9e43b21cb371578961c5f8ff
```

## Текущая граница

Разрешено:

- использовать published report/encounter mappings для exact reviewed hashes/fingerprints;
- воспроизводить normalized и reconstructed parser slice;
- выполнять локальные parser-observation queries;
- использовать scalar-free evidence receipts в Git.

Не разрешено:

- автоматически сохранять combatants candidate extraction;
- изменять core actor rows из nested addon data;
- считать `cao_id`, `entry_id`, slot или display name глобально уникальными;
- интерпретировать talents/gear как подтверждённые gameplay semantics;
- включать observed/candidate data в planner scoring;
- считать report slice полным: в нём пока нет aura events.

## Ближайший bounded этап

1. проверить candidate extraction как manual validation packet;
2. создать отдельный promotion/persistence gate для шести immutable combatants observation types;
3. сохранить их без core actor mutation;
4. добавить deterministic query/read model для actor build observations;
5. отдельно исследовать aura endpoints и довести report slice до aura observations;
6. только после независимых supporting/contradicting observations повышать trust игровых механик.

## Установка и проверка

Требования:

```text
Python >= 3.12
uv
```

```powershell
uv sync --frozen --extra dev
uv run python scripts/verify_repo.py
```

Запуск приложения:

```powershell
uv run coa-workbench serve
```

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/docs
```

Основные команды:

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
uv run pytest
```

## Data policy

Локально разрешено использовать полный приватный контекст для разработки и проверки. В Git по умолчанию версионируются только код, reviewed mappings, документация и scalar-free receipts.

Не коммитить без отдельного осознанного решения:

- raw payloads и HAR;
- DuckDB и WAL;
- normalized/reconstructed/extracted private batches;
- cookies, Authorization headers, tokens и browser profiles;
- `.env` и private query values;
- абсолютные локальные пути с username.

Gitignored local paths:

```text
data/raw/
data/warehouse/
data/normalized/
data/reconstructed/
data/extracted/
data/exchange/in/
data/exchange/out/
```

## Документация

- `docs/PROJECT_MASTER_CONTEXT.md` — каноническая архитектура и правила проекта;
- `docs/PROJECT_STATE.md` — изменяемое фактическое состояние;
- `docs/REAL_LOG_CAPTURE.md` — capture/normalization/persistence protocol;
- `docs/CONTINUATION_PROMPT.md` — стартовый контекст для нового агента;
- `docs/ADR_012_LOG_EVIDENCE_TRUTH_MODEL.md` — truth model;
- `evidence/real-data/README.md` — versioned scalar-free evidence checkpoint;
- `AGENTS.md` — обязательные инструкции разработчикам и агентам.
