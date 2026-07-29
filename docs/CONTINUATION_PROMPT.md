# Стартовый PROMPT для продолжения CoA Raid Intelligence Workbench

Скопируй этот документ в новый ChatGPT/Codex-чат или попроси агента прочитать его из репозитория.

---

Ты продолжаешь разработку проекта **CoA Raid Intelligence Workbench**.

## Обязательный порядок начала

До изменения кода:

1. Проверь repository `GunsPojoshe/coa-raid-intelligence-workbench`.
2. Проверь текущие branch, HEAD и working tree.
3. Проверь PR #7 и его base branch.
4. Проверь PR #3.
5. Проверь latest GitHub Actions run и exact failure, если он есть.
6. Прочитай полностью:
   - `AGENTS.md`;
   - `docs/PROJECT_MASTER_CONTEXT.md`;
   - `docs/PROJECT_STATE.md`;
   - `docs/REAL_LOG_CAPTURE.md`;
   - `docs/ADR_012_LOG_EVIDENCE_TRUTH_MODEL.md`;
   - `evidence/real-data/README.md`.
7. Сверь claims с кодом и versioned receipts.
8. Не доверяй старым HEAD/test counts без проверки.

## Branch chain

```text
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

Green baseline перед documentation refresh:

```text
commit: 2b92b3d02339a3748d146c1b15a6718f84494e6f
Verify repository run #280
Ubuntu: success
Windows: success
```

Фактический HEAD и CI перепроверить.

## Миссия

Создать localhost-first browser application для:

- подготовки рейдов FLEX / 10 / 25 / 40;
- хранения планов в DuckDB;
- автоматического сбора observations с `coa.ascensionlogs.gg`;
- evidence-first вывода игровых механик;
- explainable planner recommendations.

Канонический pipeline:

```text
immutable raw payload
-> exact SHA-256 + schema fingerprint
-> structural and field review
-> reviewed mapping
-> exact raw validation
-> manual promotion/publication
-> canonical normalization
-> deterministic reconstruction
-> immutable observations
-> hypothesis + supporting/contradicting evidence
-> corroborated/confirmed mechanic
-> planner scoring
```

Combat-log event является observation, а не доказательством общей mechanic.

## Trust rules

Нельзя придумывать:

- routes и query parameters;
- JSON fields;
- pagination behavior;
- event types и Spell IDs;
- class/spec/provider mappings;
- semantic meaning по route или display name;
- stacking, overwrite, coexistence или scope без evidence.

Normalization разрешена только для exact reviewed hash/fingerprint и mapping со статусом `verified`.

В planner scoring допускаются только `corroborated` и `confirmed`. Contradicting evidence сохраняется всегда.

## Privacy and Git

Пользователь разрешает использовать весь локальный приватный контекст для анализа. Это не разрешает коммитить секреты.

Versioned:

- code/tests;
- migrations;
- reviewed mappings;
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

Никогда не коммить cookies, tokens, Authorization headers, browser profiles, `.env` secrets или unsanitized HAR.

## Подтверждённый фундамент

- localhost FastAPI app;
- raid constructor and DuckDB plans;
- immutable raw archive and retrieval observations;
- JSON/HAR safe import/inventory;
- schema fingerprints;
- verified mapping gates;
- canonical report/encounter/actor/participant/aura records;
- Aura State Engine;
- hypotheses/evidence/trust policies;
- migrations `0001`–`0007`;
- repository verifier and Ubuntu/Windows CI;
- verified Armory mappings;
- verified public-report discovery mapping;
- observed report/encounter/combatants routes;
- published report and encounter mappings;
- normalized, reconstructed and persisted selected-parser report slice.

## Completed report/encounter slice

Published mappings:

```text
config/mappings/coa_report_detail_v1.json
config/mappings/coa_encounter_detail_v1.json
```

Normalized:

```text
2 reports
15 encounters
31 actors
31 participants
0 aura events
0 rejects
```

Reconstructed:

```text
1 report
14 encounters
31 actors
31 participants
0 aura events
0 rejects
0 field conflicts
9/9 linkage checks
```

Persisted through migration `0007`:

```text
1 report
14 encounters
31 actors
31 participants
77 canonical entity observations
2 normalization mappings
2 normalization runs
2 observation batches
```

## Current combatants-info checkpoint

Exact binding:

```text
payload:     45672e0f0ff9eb461c575bdd38385795daa6326378bc3f8ad51474276140dc14
fingerprint: 41d6d15422c668f83d2ccae1ec0ff2969671861f9e43b21cb371578961c5f8ff
```

Completed review/design:

```text
12 bounded scope candidates
10 present scopes
56 direct fields
8 selected groups
37 selected fields
19 deferred fields
6 storage-aware design units
```

Candidate extraction:

```text
1350 source matches
1343 output observations
7 exact instance-context duplicates removed
11 stable actor links
11 exact actor-name matches
12/12 integrity checks
0 core mutations
```

Versioned scalar-free receipt:

```text
evidence/real-data/observed-combatants-info-candidate-extraction.json
```

Current boundary:

```text
actor merge verified for exact payload: true
route context verified:              true
automatic persistence:               false
can promote:                          false
normalization allowed:                false
planner scoring allowed:              false
```

## Первая bounded задача нового агента

Не повторяй capture, field selection или mapping design.

Выполни **manual candidate-extraction validation and persistence design**:

1. Validate exact versioned extraction receipt and private extraction SHA-256.
2. Confirm the six design result counts and all 12 integrity checks.
3. Define an explicit manual promotion packet for parser observations only.
4. Decide whether migration `0007` already represents all six entity types without loss of provenance.
5. If sufficient, implement atomic/idempotent persistence into `canonical_entity_observation`.
6. If insufficient, add one new deterministic migration; do not edit `0007`.
7. Do not mutate core `actor` rows.
8. Produce a scalar-free persistence receipt.
9. Keep companion-addon provenance, nested semantics, gameplay mechanics and scoring unverified.

Expected design units:

```text
coa-combatants-actor-enrichment-v1        11 observations
coa-combatants-instance-context-v1         4 observations
coa-combatants-talent-container-v1        11 observations
coa-combatants-classless-talent-rank-v1  564 observations
coa-combatants-hero-build-entry-v1       564 observations
coa-combatants-gear-slot-v1              189 observations
```

## Следующие этапы

```text
manual extraction validation
-> reviewed promotion packet
-> atomic immutable persistence
-> deterministic read model
-> aura endpoint review/capture
-> aura normalization and interval reconstruction
-> independent supporting/contradicting evidence
-> mechanic trust promotion
-> planner integration
```

## Completion gate

PR #7 остаётся Draft до:

- reviewed combatants persistence;
- aura events for the bounded report slice;
- reconstructed intervals;
- independent supporting observations;
- contradicting evidence review;
- reproducible versioned provenance;
- green Ubuntu and Windows CI.

## Формат отчёта

После каждой задачи сообщай:

- verified facts;
- local-only observations;
- outdated claims corrected;
- files and migrations changed;
- exact tests/commands;
- CI state;
- remaining boundaries;
- next bounded task.

Не называй scaffolding, parser correctness или verified schema mapping подтверждённой gameplay mechanic.
