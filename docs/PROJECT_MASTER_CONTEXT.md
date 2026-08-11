# CoA Raid Intelligence Workbench — канонический контекст проекта

Дата актуализации: **2026-08-12**.

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

Provenance examples:

```text
raw_log
upstream_derived
companion_addon
local_inference
manual_override
```

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

Target coverage includes:

- reports;
- encounters;
- rankings;
- statistics;
- characters;
- Armory;
- talent-grid;
- guild reports;
- guild progression;
- future exact reviewed routes.

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

## 9. Guild progression chain

Observed route candidate:

```text
/api/guilds/progression
```

Evidence-backed HTTP method candidate:

```text
POST
```

`POST` is not a complete request contract.

Completed/versioned bounded stages:

```text
usage-context review
helper call-site inventory/review
helper-definition inventory: 36/36
helper-definition review: 42/42
helper-reference inventory: 40/40
helper-reference review: 46/46
```

Current verified helper-reference review boundary:

```text
references: 31
route-context references: 0
direct transport contexts: 0
request-shape contexts: 17
helper identity resolved: false
helper owner binding resolved: false
request payload mapping resolved: false
request shape sufficient for bounded probe: false
ready for helper-owner inventory: true
ready for bounded route probe: false
network requests performed: false
```

At the 2026-08-12 handoff a helper-owner inventory implementation had been prepared and validated **locally only**, not versioned and not executed against the real private evidence. Exact operational details are in `docs/PROJECT_STATE.md` and `docs/E3_GUILD_PROGRESSION_EVIDENCE_STATUS.md`.

## 10. Progression decision boundary

```text
guild identity verified: true
guild filtering completed: true
full crawl collection contract reviewed: true
guild-search route/schema verified: true
guild-search limit truncation verified: true
progression route candidate observed: true
progression usage context reviewed: true
helper definition inventory/review complete: true
helper reference inventory/review complete: true
helper owner inventory implementation versioned: false
helper owner inventory real execution complete: false
helper owner review complete: false
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

```text
version and verify helper-owner inventory implementation
-> execute offline helper-owner inventory on exact private evidence
-> validate/version scalar-free owner receipt
-> explicit helper-owner review
-> establish exact helper identity + owner binding + payload/request shape
-> bounded progression route probe
-> response schema review
-> pagination/termination/completeness evidence
-> compare full API set with known private baseline
-> explicit full-crawl promotion
-> multi-report character identity graph
-> verified build/capability observations
-> encounter requirement models
-> player reliability/performance corpus
-> dynamic attendance-aware roster completion
```

No false gate may be raised by inference.

## 12. Data/Git policy

Versioned:

- code/tests;
- migrations;
- reviewed mappings/reviews;
- canonical docs;
- approved provisional references;
- scalar-free public receipts.

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

Never commit secrets, cookies, tokens, browser profiles, unsanitized HAR, source IDs, report IDs, private queries, private receipts, raw JavaScript, raw owner chains or raw private contexts.

## 13. Development environment

Windows automation standard is PowerShell 7+ (`pwsh`). VS Code PowerShell extension is supported, but the active runtime must be verified. See `docs/WINDOWS_DEVELOPMENT_ENVIRONMENT.md`.

## 14. Branches

```text
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

PR #7 remains Draft until evidence gates are explicitly closed.
