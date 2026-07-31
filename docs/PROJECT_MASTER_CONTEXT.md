# CoA Raid Intelligence Workbench — канонический контекст проекта

Дата полной сверки: **2026-07-31**.

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
- раздельные global mechanic и guild/player execution;
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
-> versioned mapping or dedicated extractor design
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

Запрещено:

- выводить общую механику из одного event;
- считать display name или label достаточной identity binding;
- считать parser correctness mechanic confirmation;
- автоматически повышать trust после mapping/persistence;
- скрывать contradicting evidence;
- смешивать game versions без явной версии.

## 6. Реализованный фундамент

- localhost FastAPI raid planner;
- DuckDB plans and CRUD;
- immutable raw archive and retrieval observations;
- JSON/HAR privacy-safe tooling;
- schema fingerprints and verified mapping gates;
- report/encounter/actor/participant/aura records;
- rejects and Aura State Engine;
- hypotheses, evidence links and weighting policies;
- migrations `0001`–`0008`;
- repository verifier and Ubuntu/Windows CI.

## 7. Mapping and capture contract

Production parser use requires:

```text
exact archived payload
+ exact payload hash
+ exact schema fingerprint
+ reviewed selectors/types/nullability
+ reviewer metadata
+ deterministic dry run
+ explicit promotion
```

Unknown hash/fingerprint means reject and review. A verified mapping proves parser compatibility, not gameplay semantics.

## 8. Report and combatants baseline

```text
normalized: 2 reports, 15 encounters, 31 actors, 31 participants, 0 aura events
reconstructed: 1 report, 14 encounters, 31 actors, 31 participants
persisted through 0007: 77 canonical entity observations
combatants through 0008: 1343 parser observations, 1339 actor/build observations, 11 linked actors, 14/14 checks
```

Combatants parser reproducibility does not prove addon provenance, nested identifier semantics, gameplay meaning or planner suitability.

## 9. Public-report manifest

```text
receipt: evidence/real-data/argentum-public-report-manifest.json
route: /api/reports/public
limit: 25
pages: 259
reports: 6454
unique report IDs: 6454
duplicates: 0
integrity checks: 19/19
exact Argentum label reports: 17
distinct non-null guild IDs for exact label: 1
```

This proves completeness of one captured public snapshot, not target identity or guild API completeness.

## 10. Guild identity decision

```text
receipt: evidence/real-data/argentum-guild-identity-decision.json
integrity checks: 16/16
explicit operator promotion: true
cross-endpoint source-ID equality: true
name casefold equality: true
guild identity verified: true
ready for guild filtering: true
```

The source guild ID remains private. Identity verification does not verify guild API route semantics or full crawl.

## 11. Verified guild report manifest

```text
receipt: evidence/real-data/argentum-guild-report-manifest.json
source reports: 6454
selected reports: 17
unique selected report IDs: 17
duplicate selected occurrences: 0
integrity checks: 14/14
guild filtering completed: true
guild report manifest deduplicated: true
report IDs published: false
source guild ID published: false
```

Filtering uses exact typed equality against the source guild ID loaded from the private identity decision. The private 17-report set is the verified baseline.

## 12. Full-crawl collection contract

```text
receipt: evidence/real-data/argentum-guild-full-crawl-contract.json
contract version: guild-full-crawl-contract-v1
source public reports: 6454
selected guild reports: 17
integrity checks: 12/12
full crawl collection contract reviewed: true
ready for bounded route-semantics capture: true
guild API route semantics verified: false
automatic full guild crawl allowed: false
ready for full guild crawl: false
```

The contract requires:

- exact route and query parameters;
- immutable raw response capture;
- payload SHA-256 and schema fingerprint;
- reviewed collection shape, types and nullability;
- pagination, termination and completeness proof;
- deterministic comparison with the verified 17-report baseline;
- preservation of missing, extra and conflicting reports;
- explicit scalar-free route-semantic promotion.

Contract review opens bounded evidence capture only.

## 13. Current decision boundary

```text
guild identity verified: true
guild filtering completed: true
guild report manifest deduplicated: true
full crawl collection contract reviewed: true
ready for bounded route-semantics capture: true
guild API route semantics verified: false
automatic full guild crawl allowed: false
ready for full guild crawl: false
ready for multi-report character graph: false
ready for performance model: false
ready for BiS 25 scoring: false
planner scoring allowed: false
```

## 14. Aura boundary

Separate real fixtures validate technical Aura State Engine behavior but not magnitude, stacking, scope, provider equivalence or criticality. The current report slice still has zero aura events.

## 15. Data and Git policy

Versioned:

- code/tests;
- migrations;
- mappings and review decisions;
- documentation;
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

Never commit secrets, cookies, tokens, Authorization headers, browser profiles, unsanitized HAR, source guild IDs, report IDs, private decisions or private manifests.

## 16. Verification contract

```powershell
uv sync --frozen --extra dev
uv run python scripts/verify_repo.py
```

Storage changes require clean and repeated DuckDB initialization. Collector changes require deterministic fake-response tests before bounded real capture.

## 17. Current blockers and next plan

Blockers:

- latest HEAD requires green CI;
- exact guild API route/query semantics are unverified;
- response schema, pagination, termination and completeness are unverified;
- API report membership has not been compared with the private 17-report baseline;
- multi-report character identity is not established;
- no new corroborated mechanic;
- planner scoring remains closed.

Next plan:

1. perform bounded route-semantics capture under the reviewed contract;
2. archive and fingerprint exact responses;
3. review collection and pagination structure;
4. verify termination and completeness before full-crawl promotion;
5. compare future API membership with the private 17-report baseline;
6. preserve all discrepancies;
7. build character identity and performance layers only after their own gates.

## 18. Completion criteria for E3

PR #7 remains Draft until reviewed identity/filtering/crawl boundaries, reviewed combatants observations, aura observations and intervals for the bounded slice, independent supporting observations, contradicting evidence review, reproducible provenance, and green Ubuntu/Windows verification are present.