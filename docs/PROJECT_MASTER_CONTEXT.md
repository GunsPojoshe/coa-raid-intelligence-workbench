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

Report/encounter parser slice:

```text
normalized: 2 reports, 15 encounters, 31 actors, 31 participants, 0 aura events
reconstructed: 1 report, 14 encounters, 31 actors, 31 participants
persisted through 0007: 77 canonical entity observations
```

The slice is not complete for aura evidence.

## 9. Combatants observations

Candidate extraction was manually promoted and persisted through migration `0008_combatants_observation_persistence`.

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

Pagination evidence promoted exact `limit=25` for terminal search and exhaustive manifest capture.

Versioned receipt:

```text
evidence/real-data/argentum-public-report-manifest.json
```

Captured snapshot:

```text
route: /api/reports/public
pages: 259
reports: 6454
unique report IDs: 6454
duplicates: 0
terminal page reports: 4
integrity checks: 19/19
sentinel stability: verified
```

Guild fields:

```text
reports with both guild fields: 1171
distinct guild identity pairs: 88
exact Argentum label reports: 17
distinct non-null guild IDs for exact label: 1
```

Decision boundary:

```text
manifest complete: true
guild identity verified: false
ready for guild identity review: true
ready for guild filtering: false
ready for full guild crawl: false
planner scoring allowed: false
```

The manifest proves completeness of one captured public snapshot, not the semantic identity of the target guild.

## 11. Guild identity contract

A source guild identity may be promoted only after local review of the exact private manifest bound by SHA-256.

Required evidence:

- all exact `Argentum` rows map to one non-null source guild ID;
- no conflicting guild names are observed for that ID within the reviewed snapshot, or conflicts are explicitly explained;
- available independent source evidence is inspected;
- title, uploader and nickname are not used as primary identity proof;
- the published receipt is scalar-free and does not expose the raw guild ID;
- reviewer and decision are explicit.

Until promotion, guild filtering and guild-wide crawl remain disabled.

## 12. Aura boundary

Separate real fixtures for report `2987`, spell `968746` verify technical normalizer/Aura State Engine behavior but not magnitude, stacking, scope, provider equivalence or criticality. The current report slice still has zero aura events.

## 13. Data and Git policy

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

Never commit secrets, cookies, tokens, Authorization headers, browser profiles or unsanitized HAR.

## 14. Verification contract

```powershell
uv sync --frozen --extra dev
uv run python scripts/verify_repo.py
```

Storage changes require clean and repeated DuckDB initialization. Collector changes require deterministic fake-response tests before bounded real capture.

## 15. Current blockers

- guild identity behind the exact `Argentum` label is not reviewed/promoted;
- guild filtering and full guild crawl are disabled;
- multi-report character identity is not established;
- companion-addon provenance and nested combatants semantics are unverified;
- no aura events in the bounded report slice;
- no new corroborated mechanic;
- planner scoring remains closed.

## 16. Next bounded plan

1. Review the 17 exact `Argentum` private manifest rows.
2. Verify their one non-null guild ID against independent available source evidence.
3. Produce a scalar-free guild-identity review receipt.
4. Promote identity only through an explicit manual decision.
5. Then implement deterministic guild filtering and a guild report manifest.
6. Continue per-report/aura capture and multi-report character identity review.
7. Promote gameplay mechanics only after supporting and contradicting evidence thresholds.

## 17. Completion criteria for E3

PR #7 remains Draft until reviewed guild identity/crawl boundaries, reviewed combatants observations, aura observations and intervals for the bounded slice, independent supporting observations, contradicting evidence review, reproducible provenance, and green Ubuntu/Windows verification are present.
