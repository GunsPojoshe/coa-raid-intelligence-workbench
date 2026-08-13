# CoA Raid Intelligence Workbench — канонический контекст проекта

Дата актуализации: **2026-08-13**.

Этот документ фиксирует долгосрочную цель, архитектуру и truth model. Оперативные working-tree/HEAD/CI сведения находятся в `docs/PROJECT_STATE.md` и всегда перепроверяются live.

## 1. Предметная область

Проект предназначен **только для Conquest of Azeroth**.

Не использовать как CoA-факты без independent exact CoA evidence:

- Bronzebeard-specific mechanics;
- Classless Ascension ability-selection model;
- Mystic Enchants;
- Hero Architect assumptions;
- shared Ascension FAQ/frontend statements с неясным realm scope.

Обязательные domain docs:

```text
docs/COA_DOMAIN_BOUNDARY.md
docs/COA_TARGET_PRODUCT_DEFINITION.md
docs/COA_RAID_UTILITY_BASELINE_2026-08-02.md
```

## 2. Миссия

Создать localhost-first evidence-first платформу рейдовой аналитики, которая связывает реальные combat/report/build observations с encounter requirements и фактической явкой и объясняет:

> Почему конкретный игрок нужен именно текущему составу?

Целевой сценарий:

```text
actual attendance
+
verified player/build/performance evidence
+
encounter requirements
+
relevant external benchmarks
=
explainable roster completion and raid-leader decisions
```

Не строить один вечный BiS-25 roster.

## 3. Truth model

```text
combat-log event = observation
combat-log event != automatic mechanic proof
class/spec presence != verified capability coverage
shared Ascension text != CoA mechanic proof
```

Trust states:

```text
legacy_unverified
observed
candidate
corroborated
confirmed
contradicted
rejected
```

Only `corroborated` and `confirmed` mechanics may enter canonical planner scoring.

## 4. Evidence architecture

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

Derived layers do not rewrite source evidence and must preserve provenance.

## 5. Product contours

### Raid Planner

- FLEX / 10 / 25 / 40;
- actual attendance/availability;
- class/spec/role/build representation;
- manual raid-leader constraints;
- multiple valid roster alternatives;
- provenance-backed explanations.

### Raid Intelligence

- immutable raw capture;
- retrieval observations;
- hashes/fingerprints;
- reviewed mappings/extractors;
- deterministic normalization/reconstruction;
- immutable observations;
- player/build/encounter/guild identities;
- supporting/contradicting evidence;
- explicit trust evaluation;
- encounter-aware analysis.

### Dynamic roster completion

System should explain:

- what is covered reliably;
- weak/uncertain coverage;
- missing requirements;
- excessive duplication;
- who to add/replace;
- why;
- alternatives and consequences.

## 6. Data sources

### CoA Ascension Logs

Target coverage includes reports, encounters, rankings, statistics, characters, Armory, talent-grid, guild reports, guild progression and future exact reviewed routes.

### CoA BisBeard

Planning/reference source for talent/item/gear/BiS research; not automatic proof of runtime combat behavior.

### Provisional references

May be versioned only when clearly marked unverified and blocked from canonical scoring.

## 7. Implemented foundation

- localhost FastAPI planner;
- DuckDB persistence and migrations `0001`–`0008`;
- immutable content-addressed raw archive;
- separate retrieval observations;
- JSON/HAR privacy-safe tooling;
- schema fingerprints and verified mapping gates;
- report/encounter/actor/participant/aura records;
- normalization rejects and aura reconstruction;
- hypothesis/evidence/trust layers;
- repository verifier;
- Ubuntu/Windows CI;
- public-release audit.

## 8. Verified report/guild baseline

```text
public reports: 6454
unique public report IDs: 6454
exact Argentum label reports: 17
guild identity verified: true
private selected baseline: 17 unique reports
full-crawl collection contract reviewed: true
```

Private source IDs/report IDs/source rows remain local-only.

## 9. Guild progression chain — corrected interpretation

Observed route candidate:

```text
/api/guilds/progression
```

Evidence-backed HTTP method candidate:

```text
POST
```

`POST` is not a complete request contract.

The remote history contains completed helper definition/reference/owner inventory/review stages. They remain reproducible historical artifacts, but the old helper identity/owner interpretation is no longer current because a later offline diagnostic proved that the lexical scanner counted helper-like terminal text inside JavaScript template-literal **text** as executable references.

Therefore the historical model:

```text
1 definition
31 references
owner groups 5 vs 7
```

must not be used as current helper-identity evidence.

The local correction, not yet versioned at the 2026-08-13 cleanup checkpoint, introduced a shared lexical scanner and produced provisional corrected observations:

```text
full-chain occurrences: 2
definition candidates: 3
reference candidates: 45
definition overlaps: 3
route-context references: 0
direct transport contexts: 0
request-shape contexts in reviewed references: 29
owner candidates: 21
owner groups: 12
helper identity resolved: false
helper owner binding resolved: false
request payload mapping resolved: false
ready for bounded route probe: false
network requests performed: false
```

These numbers are provisional local results until the analyzer repair, regression tests, aggregate verification, commit and exact-head CI are complete.

## 10. Progression decision boundary

```text
guild identity verified: true
guild filtering completed: true
full crawl collection contract reviewed: true
guild-search route/schema verified: true
guild-search limit truncation verified: true
progression route candidate observed: true
progression usage context reviewed: true
historical helper evidence reproducible: true
historical helper identity/owner interpretation superseded: true
lexical analyzer repair versioned: false
helper identity resolved: false
helper owner binding resolved: false
request payload mapping resolved: false
request shape verified: false
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

No guessed network request to `/api/guilds/progression`.

## 11. Required progression sequence

The project no longer expands owner/alias evidence stages indefinitely. The shortest evidence-backed path is:

```text
stabilize/version lexical analyzer repair
-> trace provenance of the two actual full-chain invocations
-> identify the concrete helper implementation/binding
-> establish exact argument -> request payload mapping
-> review exact bounded request contract
-> perform one bounded progression route probe
-> review response schema
-> pagination/termination/completeness evidence
-> full guild crawl promotion
-> multi-report character identity graph
-> verified build/capability observations
-> encounter requirement models
-> player reliability/performance corpus
-> dynamic attendance-aware roster completion
```

A narrow offline diagnostic is acceptable only when it chooses between concrete implementation paths. No false gate may be raised by inference.

## 12. Development operating model

The agent performs all GitHub/repository operations available through its tools. The user should not be used as a manual GitHub operator.

When access to the user's Windows filesystem is genuinely required, use one bundled local action with a compact result/handoff. Private/raw files may be inspected for analysis; the restriction is on publication/versioning, not on private reading.

Focused tests are used during iteration. One aggregate verifier is required before a meaningful push, followed by exact-head GitHub CI.

## 13. Data/Git policy

Versioned:

- code/tests;
- migrations;
- reviewed mappings/reviews;
- canonical docs;
- approved provisional references;
- scalar-free public receipts.

Local/private:

```text
data/raw/
data/warehouse/
data/normalized/
data/reconstructed/
data/extracted/
data/exchange/in/
data/exchange/out/
```

Never publish secrets, cookies, tokens, browser profiles, unsanitized HAR, private source IDs/report IDs, private queries, private receipts, raw JavaScript, raw owner chains or raw private contexts unless an explicit reviewed publication contract permits the exact field.

## 14. Branch policy

Active structure:

```text
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

Temporary merged/closed/stage branches are disposable and should be deleted promptly. See the audited list in `docs/PROJECT_STATE.md`.
