# CoA Raid Intelligence Workbench — канонический контекст проекта

Дата полной сверки: **2026-08-04**.

Этот документ определяет долгосрочную цель, архитектуру, truth model и обязательную последовательность развития. Оперативные HEAD, CI и blockers фиксируются в `docs/PROJECT_STATE.md` и всегда перепроверяются live.

## 1. Каноническая предметная область

Проект предназначен **только для Conquest of Azeroth**.

Обязательные документы:

- `docs/COA_DOMAIN_BOUNDARY.md` — что относится и не относится к CoA;
- `docs/COA_TARGET_PRODUCT_DEFINITION.md` — конечный продуктовый результат;
- `docs/COA_RAID_UTILITY_BASELINE_2026-08-02.md` — provisional utility reference, требующий проверки логами.

Не использовать Bronzebeard, Classless Ascension, Mystic Enchants, Hero Architect или другие realm-specific механики как CoA-факты без отдельного exact CoA evidence.

## 2. Миссия

Создать localhost-first evidence-first платформу рейдовой аналитики для CoA, которая:

- максимально полно покрывает доступные данные CoA Ascension Logs;
- связывает reports, encounters, characters, guilds, Armory, talent-grid, rankings и statistics;
- использует CoA BisBeard как build-planning источник;
- анализирует наши и релевантные внешние боевые результаты;
- объясняет ошибки состава и исполнения на конкретных энкаунтерах;
- помогает РЛ формировать динамический состав под фактическую явку;
- объясняет, почему конкретный человек нужен именно текущему составу.

Канонический принцип:

```text
combat-log event = observation
combat-log event != automatic proof of a mechanic
class/spec presence != capability coverage
shared Ascension text != CoA mechanic proof
```

Planner scoring допускает только `corroborated` и `confirmed` mechanics.

## 3. Продуктовый контекст

Гильдия играет в полухардкорном режиме с элементами спокойной игры. Есть ядро примерно из 15–20 постоянных игроков, но фактическая явка меняется.

Система не ищет один неизменный BiS-состав из 25 человек.

Главный сценарий:

```text
кто сегодня пришёл
+
как эти люди реально играют
+
какие билды и роли они реально используют
+
что требует конкретный энкаунтер
+
кого ещё можно позвать
=
объяснимый добор, замена и план рейда
```

## 4. Product contours

### Raid Planner

- составы FLEX / 10 / 25 / 40;
- фактическая явка и доступность;
- class/spec/role/build representation;
- ручные ограничения РЛ;
- несколько допустимых вариантов состава;
- объяснимые рекомендации с provenance.

### Raid Intelligence

- immutable raw capture;
- retrieval observations;
- hashes и schema fingerprints;
- reviewed mappings/extractors;
- deterministic normalization/reconstruction;
- immutable observations;
- player/build/encounter/guild identities;
- supporting и contradicting evidence;
- explicit trust evaluation;
- encounter-aware player and roster analysis.

### Dynamic roster completion

Система должна показывать:

- что закрыто надёжно;
- что закрыто слабо;
- что отсутствует;
- что дублируется;
- кого добавить или заменить;
- почему этот игрок нужен этому составу;
- альтернативы и последствия.

## 5. Evidence architecture

```text
source response
-> immutable raw payload
-> retrieval observation
-> SHA-256 + schema fingerprint
-> structural/field review
-> versioned mapping or extractor
-> exact raw validation
-> explicit promotion/publication
-> normalization/extraction
-> deterministic reconstruction
-> atomic immutable persistence
-> read models
-> hypotheses and evidence
-> trust evaluation
-> explainable recommendation
```

Верхний слой не может переписать нижний. Derived вывод обязан сохранять exact provenance.

## 6. Trust model

```text
legacy_unverified
observed
candidate
corroborated
confirmed
contradicted
rejected
```

Provenance:

```text
raw_log
upstream_derived
companion_addon
local_inference
manual_override
```

Не являются автоматическим gameplay knowledge:

- parser correctness;
- schema verification;
- guild identity verification;
- deterministic filtering;
- successful persistence;
- talent description;
- class/spec presence;
- one combat-log event;
- high parse;
- one successful raid composition;
- correlation between composition and result.

## 7. Источники

### CoA Ascension Logs

Целевое покрытие:

- reports;
- encounters;
- rankings;
- statistics;
- characters;
- Armory;
- talent-grid;
- guild reports;
- guild progression;
- future exact routes discovered and reviewed.

### CoA BisBeard

Используется для talent, item, gear и BiS planning. Не является автоматическим доказательством runtime combat behavior.

### Provisional references

Могут versioned-храниться как research input, если явно отмечены как непроверенные и запрещены для scoring.

## 8. Provisional utility baseline

`docs/COA_RAID_UTILITY_BASELINE_2026-08-02.md` фиксирует supplied artifact:

```text
source SHA-256: adbb2f7f06d750ddad4d981cca3f22b3141f471e8f9819e87f528f357fabdddd
class cards: 28
class/spec associations: 87
unique specialization labels: 67
utility rows: 187
observed in 30-log sample: 132
zero observations in sample: 55
```

Это не полный проверенный каталог 69 специализаций и не planner input.

## 9. Реализованный фундамент

- localhost FastAPI raid planner;
- DuckDB plans and CRUD;
- immutable content-addressed raw archive;
- separate retrieval observations;
- JSON/HAR privacy-safe tooling;
- schema fingerprints and verified mapping gates;
- canonical report/encounter/actor/participant/aura records;
- normalization rejects и Aura State Engine;
- hypotheses, evidence links and weighting policies;
- migrations `0001`–`0008`;
- repository verifier;
- Ubuntu/Windows CI;
- public-release audit.

## 10. Verified report and guild baseline

```text
public reports: 6454
unique public report IDs: 6454
exact Argentum label reports: 17
guild identity verified: true
private selected baseline: 17 unique reports
full-crawl collection contract reviewed: true
```

Source guild ID, report IDs and private rows remain local-only.

## 11. Armory boundary

Reviewed mappings currently establish selected reproducible extraction for:

- character identity, realm, class, race and level;
- upstream role and active specialization index;
- resolved talent-rank records;
- selected compact stat summaries;
- talent-grid tree identity;
- talent IDs, spell IDs, display fields, coordinates, node type and connections.

They do not prove runtime magnitude, stacking, scope, provider equivalence or planner criticality.

## 12. Guild-search checkpoint

Verified:

```text
route: /api/guilds/search
response keys: guilds, success
guild fields: id, name, realm, report_count
limit result counts: 1 / 7 / 7
limit truncation semantics verified: true
```

This proves bounded search-list truncation only.

## 13. Progression checkpoint

The archived SPA asset contains one `/api/guilds/progression` candidate.

Reviewed evidence:

```text
call class: generic_helper_call
HTTP method candidate: POST
method evidence: method_property_literal
method candidate unambiguous: true
helper identity resolved: false
request payload mapping resolved: false
request shape sufficient for bounded probe: false
ready for bounded route probe: false
```

`POST` is not a complete request contract.

## 14. Helper-definition inventory stage

Implemented:

```text
src/coa_workbench/collector/guild_progression_helper_definition_command.py
src/coa_workbench/collector/guild_progression_helper_definition_index.py
src/coa_workbench/collector/guild_progression_helper_definition_inventory.py
scripts/inventory_guild_progression_helper_definition.py
tests/unit/test_guild_progression_helper_definition_command.py
tests/unit/test_guild_progression_helper_definition_index.py
tests/unit/test_guild_progression_helper_definition_inventory.py
```

Contract:

- offline-only;
- exact archived SPA asset;
- exact bound call-site/recovery artifacts;
- bounded definition and alias search;
- raw definitions private;
- scalar-free public receipt;
- `36` integrity checks;
- no automatic downstream promotion.

## 15. Current decision boundary

```text
guild identity verified: true
guild filtering completed: true
full crawl collection contract reviewed: true
guild-search route/schema verified: true
guild-search limit truncation verified: true
progression route candidate observed: true
progression usage context reviewed: true
progression helper/call-site reviewed: true
progression HTTP method candidate: POST
progression method candidate unambiguous: true
helper-definition inventory implementation complete: true
helper-definition inventory executed on private artifacts: false
helper-definition public receipt validated: false
helper-definition receipt versioned: false
helper-definition review complete: false
progression helper identity resolved: false
progression request payload mapping resolved: false
progression request shape verified: false
ready for bounded progression route probe: false
progression route semantics verified: false
pagination semantics verified: false
termination semantics verified: false
completeness verified: false
automatic full guild crawl allowed: false
ready for full guild crawl: false
ready for multi-report character graph: false
ready for performance model: false
ready for encounter-aware roster completion: false
planner scoring allowed: false
```

## 16. Обязательная дальнейшая последовательность

```text
sync local branch by fast-forward
-> run offline helper-definition inventory
-> inspect private candidates and 36 checks
-> validate/version scalar-free public receipt
-> implement explicit helper-definition review
-> bounded progression probe only after exact helper/payload verification
-> response schema review
-> pagination/termination/completeness evidence
-> compare API report set with private 17-report baseline
-> explicit full-crawl promotion
-> multi-report character identity graph
-> verified build and capability observations
-> encounter requirement models
-> player reliability and performance corpus
-> dynamic attendance-aware roster completion
```

## 17. Data and Git policy

Versioned:

- code/tests;
- migrations;
- reviewed mappings and decisions;
- canonical documentation;
- approved provisional references;
- scalar-free receipts.

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

Never commit secrets, cookies, tokens, Authorization headers, browser profiles, unsanitized HAR, source guild IDs, report IDs, private queries, private receipts, raw JavaScript or raw archive content.

## 18. Branches

```text
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

PR #7 remains Draft until evidence gates are explicitly closed.
