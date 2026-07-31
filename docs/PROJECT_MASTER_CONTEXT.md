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

Planner scoring разрешён только для:

```text
corroborated
confirmed
```

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

Product:

- localhost FastAPI;
- browser raid constructor;
- FLEX / 10 / 25 / 40;
- Python validation;
- DuckDB plans и CRUD;
- diagnostics и localhost-only bind.

Evidence:

- source registry и safe probes;
- immutable raw archive;
- separate retrieval observations;
- JSON/HAR tooling;
- schema fingerprints;
- verified mapping gate;
- canonical report/encounter/actor/participant/aura records;
- rejects и Aura State Engine;
- hypotheses, evidence links и weighting policies;
- migrations `0001`–`0008`;
- repository verifier и Ubuntu/Windows CI.

## 7. Mapping and capture contract

A mapping/extractor may enter production parser use only after:

```text
exact archived payload
+ exact payload SHA-256
+ exact schema fingerprint
+ reviewed selectors/types/nullability
+ manual reviewer metadata
+ successful deterministic dry run
+ explicit promotion
```

Unknown hash/fingerprint means reject and review. A verified mapping proves parser compatibility, not gameplay semantics.

## 8. Current report slice

Observed routes:

```text
/api/reports/{template}
/api/reports/{template}/encounters/{template}
/api/reports/{template}/encounters/{template}/combatants-info
```

No separate `/roster` route was observed.

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

```text
normalized: 2 reports, 15 encounters, 31 actors, 31 participants, 0 aura events
reconstructed: 1 report, 14 encounters, 31 actors, 31 participants
persisted through 0007: 77 canonical entity observations
```

The slice is not complete for aura evidence.

## 9. Combatants observations

```text
persisted parser observations: 1343
actor/build observations: 1339
distinct linked actors: 11
integrity checks: 14/14
core actor mutations: 0
```

Read models:

```text
combatants_parser_observation_v1
combatants_actor_build_observation_v1
```

This proves exact parser/persistence reproducibility. It does not prove companion-addon provenance, nested identifier semantics, gameplay meaning or planner suitability.

## 10. Public-report manifest

Versioned receipt:

```text
evidence/real-data/argentum-public-report-manifest.json
```

```text
route: /api/reports/public
limit: 25
pages: 259
reports: 6454
unique report IDs: 6454
duplicates: 0
terminal page reports: 4
integrity checks: 19/19
sentinel stability: verified
exact Argentum label reports: 17
distinct non-null guild IDs for exact label: 1
```

The manifest proves completeness of one captured public snapshot, not target identity or guild API completeness.

## 11. Guild identity decision

Versioned receipt:

```text
evidence/real-data/argentum-guild-identity-decision.json
```

Verified evidence:

- 17 exact `Argentum` rows share one non-null source guild ID;
- no conflicting non-empty name exists for that ID in the snapshot;
- one independent guild-search result has the same source ID;
- names match after Unicode casefold;
- explicit operator promotion was required;
- public receipt contains no raw payload or source scalars.

Boundary:

```text
guild identity verified: true
ready for guild filtering: true
guild API route semantics verified: false
ready for full guild crawl: false
planner scoring allowed: false
```

## 12. Verified guild report manifest

Versioned receipt:

```text
evidence/real-data/argentum-guild-report-manifest.json
```

Selection contract:

```text
filter: exact typed equality on verified private source guild ID
deduplication: /reports/*/id
order: source manifest order
```

Verified result:

```text
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

This proves deterministic membership in the reviewed captured public snapshot. It does not prove guild API route semantics, full-crawl completeness, character identity, performance or planner suitability.

## 13. Full-crawl contract boundary

Before any full guild crawl:

- bind the collection contract to the verified identity decision and 17-report manifest;
- verify exact guild API route parameters and response schema;
- verify pagination, termination and completeness semantics;
- archive exact raw responses and preserve hashes/fingerprints;
- compare API-derived and public-manifest-derived report sets;
- retain missing, extra and conflicting reports as evidence;
- publish an explicit scalar-free collection decision receipt.

Until then:

```text
full crawl collection contract reviewed: false
guild API route semantics verified: false
ready for full guild crawl: false
ready for multi-report character graph: false
ready for performance model: false
ready for BiS 25 scoring: false
planner scoring allowed: false
```

## 14. Aura boundary

Separate real fixtures for report `2987`, spell `968746` verify technical normalizer/Aura State Engine behavior but not magnitude, stacking, scope, provider equivalence or criticality. The current report slice still has zero aura events.

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

- latest HEAD still requires green CI;
- full-crawl contract and guild API semantics are unverified;
- multi-report character identity is not established;
- companion-addon provenance and nested combatants semantics are unverified;
- no aura events in the bounded report slice;
- no new corroborated mechanic;
- planner scoring remains closed.

Next bounded plan:

1. review the full-crawl collection contract against the verified 17-report manifest;
2. define exact evidence requirements for route semantics and completeness;
3. permit bounded per-report capture only after contract review;
4. compare any guild API result set with the verified public-manifest filter;
5. preserve discrepancies;
6. build character identity and performance layers only after their own gates.

## 18. Completion criteria for E3

PR #7 remains Draft until reviewed guild identity/filtering/crawl boundaries, reviewed combatants observations, aura observations and intervals for the bounded slice, independent supporting observations, contradicting evidence review, reproducible provenance, and green Ubuntu/Windows verification are present.