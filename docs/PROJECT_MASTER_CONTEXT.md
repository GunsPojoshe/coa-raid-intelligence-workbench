# CoA Raid Intelligence Workbench — канонический контекст проекта

Дата полной сверки: **2026-07-30**.

Этот документ определяет цель, архитектуру, truth model, границы доверия и текущее направление проекта. Изменяемые counts, HEAD и CI находятся в `docs/PROJECT_STATE.md` и всегда перепроверяются по GitHub.

## 1. Миссия

Создать localhost-first браузерное приложение для:

- подготовки рейдов FLEX / 10 / 25 / 40;
- хранения и проверки планов;
- сбора реальных наблюдений с `coa.ascensionlogs.gg`;
- воспроизводимого evidence-first анализа;
- формирования объяснимых рекомендаций только из достаточно подтверждённых механик.

Главный принцип:

```text
combat-log event = observation
combat-log event != automatic proof of a general mechanic
```

## 2. Продуктовые контуры

### 2.1 Raid Planner

Пользователь должен иметь возможность:

- собирать состав до 40 персонажей;
- выбирать класс, специализацию и роль;
- видеть структурные ошибки;
- сохранять, открывать, изменять и удалять планы;
- получать рекомендации с provenance и понятной причиной.

### 2.2 Raid Intelligence

Система должна:

- получать доступные source observations;
- сохранять raw responses неизменяемо;
- фиксировать hashes и schema fingerprints;
- нормализовать только reviewed schemas;
- восстанавливать временное состояние;
- формировать hypotheses;
- хранить supporting и contradicting evidence;
- отделять global mechanic от guild/player execution;
- использовать в planner только `corroborated` и `confirmed` mechanics.

## 3. История этапов

```text
E0  Excel baseline — закрыт без merge как основной runtime
E1  localhost web — Browser -> FastAPI -> Python -> DuckDB
E2  evidence-first foundation — PR #3, Draft
E3  real log capture and normalization — PR #7, Draft
```

Active branch chain:

```text
main
└── e2/log-evidence-refactor        PR #3 -> main
    └── e3/real-log-capture         PR #7 -> e2
```

## 4. Архитектура

### Product runtime

```text
Browser
-> localhost FastAPI
-> planner / catalog / persistence API
-> DuckDB
```

### Evidence pipeline

```text
source response
-> immutable raw payload
-> retrieval observation
-> SHA-256 + schema fingerprint
-> structural review
-> field/scope review
-> versioned mapping
-> exact raw validation
-> manual promotion/publication
-> canonical normalization
-> deterministic reconstruction
-> immutable entity observations
-> hypotheses and evidence
-> trust evaluation
-> planner scoring
```

### Layer boundary

Система разделяет:

1. raw source payload;
2. safe transport/capture facts;
3. upstream-derived fields;
4. canonical parser records;
5. deterministic local reconstruction;
6. immutable observations;
7. local hypotheses;
8. supporting/contradicting evidence;
9. corroborated/confirmed mechanics;
10. planner output.

Верхний слой не может переписать нижний.

## 5. Trust model

Основные состояния:

```text
legacy_unverified
observed
candidate
corroborated
confirmed
contradicted
rejected
```

Canonical planner scoring разрешён только для:

```text
corroborated
confirmed
```

Provenance хранится раздельно:

```text
raw_log
upstream_derived
companion_addon
local_inference
manual_override
```

Запрещено:

- выводить общую механику из одного event;
- считать одинаковые display names одной механикой;
- считать source class/spec доказательством provider capability;
- приравнивать parser correctness к mechanic confirmation;
- автоматически повышать trust после mapping promotion;
- скрывать contradicting evidence;
- смешивать game versions без явной версии.

## 6. Реализованный product foundation

- localhost FastAPI service;
- browser raid constructor;
- FLEX / 10 / 25 / 40;
- Python composition validation;
- class/spec/role catalog;
- DuckDB raid-plan persistence;
- CRUD plans;
- request IDs и diagnostic logs;
- localhost-only bind.

Legacy static catalog остаётся forensic/regression layer и не входит в canonical scoring.

## 7. Реализованный evidence foundation

- source registry;
- safe probes;
- immutable content-addressed archive;
- payload body deduplication;
- separate retrieval observations;
- JSON/HAR import;
- deterministic safe HAR inventory;
- gzip JSON inspection;
- schema fingerprints;
- versioned mappings;
- verified mapping gate;
- canonical report/encounter/actor/participant/aura records;
- rejects;
- Aura State Engine;
- hypotheses и evidence links;
- trust/weighting policy;
- migrations `0001`–`0007`;
- repository verifier;
- Ubuntu/Windows CI.

## 8. Raw archive contract

Raw payload:

- сохраняется до semantic interpretation;
- immutable;
- адресуется по SHA-256;
- одинаковое содержимое хранится один раз;
- повторное получение создаёт новую observation;
- JSON получает schema fingerprint;
- request URL и metadata сохраняются только в sanitized форме.

Cookies допускаются только в process memory.

## 9. Mapping and normalization contract

Mapping создаётся только после просмотра exact payload.

Обязательные свойства:

- source code и endpoint/route;
- exact schema fingerprint;
- versioned mapping ID;
- reviewed payload hash;
- explicit collection and field selectors;
- provenance type;
- review metadata;
- status `verified` для production parser use.

Unknown payload hash или fingerprint:

```text
reject -> review queue
```

Нельзя применять «похожий» mapping автоматически.

## 10. Verified HTTP/capture profile

Versioned profile:

```text
coa-fetch-context-v1
```

Проверен полный same-origin header set и persistent same-origin session с in-memory cookie jar.

Не доказано:

- минимальное подмножество headers;
- отсутствие cookie dependency;
- независимость от request order;
- необходимость browser TLS impersonation.

Endpoint isolation, bounded retries, incomplete-body handling и progressive safe outputs обязательны.

## 11. Verified Armory and discovery gates

Production-ready mappings:

```text
config/mappings/coa_armory_character_v1.json
config/mappings/coa_armory_talent_grid_v1.json
config/mappings/coa_public_report_discovery_v1.json
```

Они подтверждают extraction для exact reviewed schemas, но не gameplay semantics.

Public report discovery ограничен одним явно запрошенным page и `limit <= 5`. Pagination/category semantics остаются unverified.

## 12. Current report slice

Observed routes:

```text
/api/reports/{template}
/api/reports/{template}/encounters/{template}
/api/reports/{template}/encounters/{template}/combatants-info
```

Exact bindings:

```text
report_detail
payload:     161739896f0b8321f884bcc24d1896efb894a9c6e05166269189f9871c64cba9
fingerprint: 3d533a4178b67957bbd31544ddf5484bd5959635ebd5edcdd0c7689a4bace216

encounter_detail
payload:     955437d6c9c287cc7db280dd2388b88603af2785508061b95c7811dcd272fe22
fingerprint: 567f36824efb37a29b835df01ce9b1fcc79eae57d6230202d16a6265c6ca0e85

combatants_info
payload:     45672e0f0ff9eb461c575bdd38385795daa6326378bc3f8ad51474276140dc14
fingerprint: 41d6d15422c668f83d2ccae1ec0ff2969671861f9e43b21cb371578961c5f8ff
```

No separate `/roster` route was observed.

## 13. Completed report/encounter pipeline

Published mappings:

```text
config/mappings/coa_report_detail_v1.json
config/mappings/coa_encounter_detail_v1.json
```

Verified parser contracts:

```text
mapping count:  2
field contracts:54
```

Normalization:

```text
2 reports
15 encounters
31 actors
31 participants
0 aura events
0 rejects
```

Deterministic reconstruction:

```text
1 report
14 encounters
31 actors
31 participants
0 aura events
0 rejects
1 duplicate report merged
1 duplicate encounter merged
0 field conflicts
9/9 linkage checks
```

Persistence through migration `0007_selected_parser_persistence`:

```text
1 report
14 encounters
31 actors
31 participants
77 canonical entity observations
2 normalization mappings
2 normalization runs
2 observation batches
0 rejects
```

The report slice is not complete because aura events are absent.

## 14. Combatants-info current state

Deep review:

```text
12 bounded scope candidates
10 present scopes
4/4 required scopes
56 direct fields
2 missing optional scopes
```

Manual selection:

```text
8 groups
37 selected fields
19 deferred fields
1 exact actor linkage path
```

Storage-aware design:

```text
6 dedicated extractor units
all target immutable canonical_entity_observation
core actor mutation disabled
```

Candidate extraction for exact payload:

```text
1350 source matches
1343 output observations
7 exact instance-context duplicates removed
11 stable actor links
11 exact actor-name matches
12/12 integrity checks
0 core mutations
```

Design units:

```text
actor enrichment:       11 observations
instance context:         4 observations
talent container:        11 observations
classless talent rank:  564 observations
hero build entry:       564 observations
gear slot:              189 observations
```

What this proves:

- exact archive/manifest/route verification;
- exact stable actor linkage;
- selected parser field presence/types;
- deterministic record hashes and counts;
- safe extraction without core mutation.

What it does not prove:

- companion-addon provenance;
- global uniqueness of nested IDs;
- talent/gear gameplay meaning;
- provider/effect relationships;
- automatic persistence or promotion;
- planner usability.

## 15. Aura checkpoint

Separate real fixtures for report `2987`, spell `968746` verify technical normalizer/Aura State Engine behavior:

```text
encounter 64795: 6 events -> 3 intervals
encounter 64796: 3 events -> 2 intervals
0 rejects
0 anomalies
```

They do not confirm magnitude, stacking, overwrite, scope, provider equivalence or criticality.

## 16. Storage model

Core tables include report, encounter, actor, participant and aura records.

Migration `0007` adds selected-parser persistence metadata and immutable canonical entity observations. Parser observations preserve:

- source payload and mapping references;
- batch/run identity;
- entity type and stable identity;
- observation JSON;
- trust status;
- deterministic provenance.

Candidate combatants observations must remain immutable and must not mutate core actors until a separate reviewed projection policy exists.

## 17. Data and Git policy

The user authorizes full use of local private data for development while the repository is private. The default repository policy still minimizes sensitive and bulky data.

Versioned:

- code and tests;
- migrations;
- mappings and review decisions;
- documentation;
- scalar-free receipts.

Local-only by default:

```text
data/raw/
data/warehouse/
data/normalized/
data/reconstructed/
data/extracted/
data/exchange/in/
data/exchange/out/
```

Never commit secrets, tokens, cookies, Authorization headers, browser profiles or unsanitized HAR.

## 18. Verification contract

Canonical command:

```powershell
uv sync --frozen --extra dev
uv run python scripts/verify_repo.py
```

Verifier covers Ruff, pytest, doctor, CLI/trust checks and clean temporary DuckDB migration initialization. Storage changes require repeatability tests. Collector changes require deterministic fake-response tests before bounded real capture.

## 19. Current blockers

- combatants extraction not manually promoted;
- 1343 candidate observations not persisted;
- no actor build observation read model;
- companion-addon provenance unverified;
- nested ID semantics unverified;
- no aura events in current report slice;
- no new corroborated mechanic;
- planner scoring correctly remains closed.

## 20. Next bounded plan

1. Validate the exact candidate extraction receipt as a manual gate.
2. Define promotion and persistence contracts for six immutable observation types.
3. Reuse migration `0007` where sufficient; add a migration only for a proven storage gap.
4. Persist atomically and idempotently without core actor mutation.
5. Add deterministic observation queries/read models.
6. Capture/review aura-related report endpoints.
7. Gather independent supporting and contradicting observations.
8. Promote gameplay mechanics only after explicit evidence thresholds.

## 21. Completion criteria for E3

PR #7 remains Draft until:

- real payloads and exact fingerprints are reproducible;
- required mappings are reviewed and verified;
- report/encounter/actors/participants are persisted;
- combatants observations have reviewed persistence;
- aura events and intervals exist for the bounded report slice;
- independent supporting observations exist;
- contradicting evidence is evaluated;
- outputs carry versioned provenance;
- Ubuntu and Windows verification remain green.

## 22. Canonical documents

```text
AGENTS.md
docs/PROJECT_MASTER_CONTEXT.md
docs/PROJECT_STATE.md
docs/CONTINUATION_PROMPT.md
docs/REAL_LOG_CAPTURE.md
docs/ADR_012_LOG_EVIDENCE_TRUTH_MODEL.md
evidence/real-data/README.md
```
