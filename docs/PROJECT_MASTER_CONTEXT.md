# CoA Raid Intelligence Workbench — канонический контекст проекта

Дата полной сверки: **2026-08-03**.

Этот документ определяет цель, архитектуру, truth model и границы доверия. Изменяемые counts, HEAD и CI фиксируются в `docs/PROJECT_STATE.md` и всегда перепроверяются.

## 1. Миссия

Создать localhost-first браузерное приложение для подготовки рейдов FLEX / 10 / 25 / 40, хранения планов, сбора реальных наблюдений с `coa.ascensionlogs.gg` и explainable recommendations только из достаточно подтверждённых механик.

```text
combat-log event = observation
combat-log event != automatic proof of a general mechanic
```

## 2. Product contours

### Raid Planner

- составы до 40 персонажей;
- класс, специализация и роль;
- структурная валидация;
- CRUD планов в DuckDB;
- рекомендации с provenance.

### Raid Intelligence

- immutable raw capture;
- hashes и schema fingerprints;
- reviewed mappings;
- canonical parser records;
- deterministic reconstruction;
- immutable observations;
- supporting/contradicting evidence;
- planner use только для `corroborated` и `confirmed` mechanics.

## 3. Этапы и ветки

```text
E0  Excel baseline — закрыт как основной runtime
E1  localhost web
E2  evidence-first foundation — PR #3, Draft
E3  real log capture and normalization — PR #7, Draft
```

```text
main
└── e2/log-evidence-refactor        PR #3 -> main
    └── e3/real-log-capture         PR #7 -> e2
```

## 4. Evidence architecture

```text
source response
-> immutable raw payload
-> retrieval observation
-> SHA-256 + schema fingerprint
-> structural/field review
-> versioned mapping or extractor design
-> exact raw validation
-> manual promotion/publication
-> normalization/extraction
-> deterministic reconstruction
-> atomic immutable persistence
-> read models
-> hypotheses and evidence
-> trust evaluation
-> planner scoring
```

Верхний слой не может переписать нижний.

## 5. Trust model

```text
legacy_unverified
observed
candidate
corroborated
confirmed
contradicted
rejected
```

Planner scoring разрешён только для `corroborated` и `confirmed`.

Provenance:

```text
raw_log
upstream_derived
companion_addon
local_inference
manual_override
```

Parser correctness, identity verification, filtering, collection contract review and route/schema review do not confirm gameplay semantics.

## 6. Реализованный фундамент

- localhost FastAPI raid planner;
- DuckDB plans and CRUD;
- immutable raw archive and retrieval observations;
- JSON/HAR privacy-safe tooling;
- schema fingerprints and verified mapping gates;
- report/encounter/actor/participant/aura records;
- migrations `0001`–`0008`;
- repository verifier and Ubuntu/Windows CI.

## 7. Report and combatants baseline

```text
normalized: 2 reports, 15 encounters, 31 actors, 31 participants, 0 aura events
reconstructed: 1 report, 14 encounters, 31 actors, 31 participants
persisted through 0007: 77 canonical entity observations
combatants through 0008: 1343 parser observations
actor/build observations: 1339
linked actors: 11
combatants checks: 14/14
```

## 8. Public manifest, identity and filtering

```text
public reports: 6454
unique public report IDs: 6454
public-manifest checks: 19/19
identity-decision checks: 16/16
guild identity verified: true
selected guild reports: 17
unique selected report IDs: 17
filter checks: 14/14
```

The source guild ID and report IDs remain private. The private 17-report set is the verified comparison baseline.

## 9. Full-crawl collection contract

```text
receipt: evidence/real-data/argentum-guild-full-crawl-contract.json
integrity checks: 12/12
full crawl collection contract reviewed: true
```

The contract requires exact route/query verification, immutable raw response capture, payload SHA-256, schema fingerprint, reviewed collection shape, pagination/termination/completeness proof and deterministic comparison with the private baseline.

## 10. Guild route capture and review

Capture:

```text
receipt: evidence/real-data/argentum-guild-route-semantics-capture.json
attempts: 3
completed attempts: 3
HTTP 200 responses: 3
integrity checks: 13/13
observed result counts: [1]
```

Review:

```text
receipt: evidence/real-data/argentum-guild-route-semantics-review.json
integrity checks: 22/22
route template verified: true
query shapes verified: true
response schema verified: true
limit parameter accepted: true
ready for bounded limit-semantics capture: true
```

Verified response fields:

```text
id: integer
name: string
realm: string
report_count: string
```

All bounded cases returned one identical record. The review therefore does not verify limit truncation, pagination, termination or completeness.

## 11. Current decision boundary

```text
guild identity verified: true
guild filtering completed: true
full crawl collection contract reviewed: true
guild route template verified: true
guild query shapes verified: true
guild response schema verified: true
limit parameter accepted: true
ready for bounded limit-semantics capture: true
limit truncation semantics verified: false
pagination semantics verified: false
termination semantics verified: false
completeness verified: false
guild API route semantics verified: false
automatic full guild crawl allowed: false
ready for full guild crawl: false
ready for multi-report character graph: false
ready for performance model: false
ready for BiS 25 scoring: false
planner scoring allowed: false
```

## 12. Next bounded plan

1. design a bounded multi-result guild-search probe;
2. use a privacy-safe query expected to return multiple records;
3. compare at least two accepted `limit` values;
4. archive and fingerprint exact responses;
5. publish only scalar-free counts, hashes and decisions;
6. verify truncation behavior without overclaiming pagination or completeness;
7. keep full crawl, graph, performance and scoring closed;
8. proceed to pagination/termination/completeness and set comparison only through separate explicit reviews.

## 13. Aura boundary

Separate fixtures validate technical Aura State Engine behavior but not magnitude, stacking, scope, provider equivalence or criticality. The current report slice still has zero aura events.

## 14. Data and Git policy

Versioned: code/tests, migrations, mappings and review decisions, documentation and scalar-free receipts.

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

Never commit secrets, cookies, tokens, Authorization headers, browser profiles, unsanitized HAR, source guild IDs, report IDs, private decisions or private manifests.

## 15. Verification contract

```powershell
uv sync --frozen --extra dev
uv run python scripts/verify_repo.py
```

Storage changes require clean and repeated DuckDB initialization. Collector changes require deterministic fake-response tests before bounded real capture.

## 16. Completion criteria for E3

PR #7 remains Draft until reviewed identity/filtering/crawl boundaries, reviewed combatants observations, aura observations and intervals for the bounded slice, independent supporting observations, contradicting evidence review, reproducible provenance, and green Ubuntu/Windows verification are present.
