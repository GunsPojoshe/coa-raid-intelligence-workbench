# Фактическое состояние проекта

Дата актуализации: **2026-08-03**.

Документ фиксирует operational state. Перед работой перепроверять GitHub, код, local private artifacts, versioned receipts и CI.

## Репозиторий

```text
repository: GunsPojoshe/coa-raid-intelligence-workbench
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

PR #7 остаётся open, Draft и mergeable. Фактический HEAD и новый CI перепроверять после каждого commit.

Последний подтверждённый зелёный baseline перед versioning review receipt:

```text
commit: 93f4e801a7251382bedc60f4deda1b84ec7bbda0
Verify repository run: #513
public-release-audit: success
Ubuntu: success
Windows: success
Ruff lint/format: success
pytest: 318 passed
Doctor: success
clean/repeated DuckDB initialization: success
```

Новые documentation/evidence commits требуют отдельной проверки CI.

## Trust boundary

```text
combat-log event = observation
combat-log event != automatic proof of a general mechanic
```

Parser/schema verification, guild identity verification, filtering, collection contract review и route/schema review не подтверждают игровую механику. Canonical planner scoring допускает только `corroborated` и `confirmed` mechanics.

## Реализованный фундамент

- localhost FastAPI raid planner и DuckDB plans;
- immutable content-addressed raw archive;
- JSON/HAR privacy-safe tooling;
- schema fingerprints и reviewed mappings;
- report/encounter/actor/participant/aura records;
- migrations `0001`–`0008`;
- repository verifier, Ubuntu/Windows CI и public-release audit.

## Report/encounter и combatants checkpoint

```text
normalized: 2 reports, 15 encounters, 31 actors, 31 participants, 0 aura events
reconstructed: 1 report, 14 encounters, 31 actors, 31 participants, 0 field conflicts
persisted through 0007: 77 canonical entity observations
combatants through 0008: 1343 parser observations
actor/build observations: 1339
linked actors: 11
combatants integrity checks: 14/14
```

## Public manifest, identity and filtering

```text
public reports: 6454
unique public report IDs: 6454
public-manifest integrity checks: 19/19
identity-decision integrity checks: 16/16
guild identity verified: true
selected guild reports: 17
unique selected report IDs: 17
filter integrity checks: 14/14
```

The source guild ID and report IDs remain private.

## Full-crawl collection contract — reviewed

```text
receipt: evidence/real-data/argentum-guild-full-crawl-contract.json
integrity checks: 12/12
full crawl collection contract reviewed: true
verified private baseline reports: 17
```

The contract requires exact route/query verification, immutable raw capture, payload SHA-256, schema fingerprint, pagination/termination/completeness proof and deterministic comparison with the private 17-report baseline.

## Bounded route-semantics capture — completed

```text
receipt: evidence/real-data/argentum-guild-route-semantics-capture.json
attempts: 3
completed attempts: 3
HTTP 200 responses: 3
integrity checks: 13/13
observed result counts: [1]
payload hash stable: true
schema fingerprint stable: true
source ID set stable by hash: true
pagination object observed: false
```

Observed cases:

```text
/api/guilds/search?q=<target>&limit=1
/api/guilds/search?q=<target>&limit=25
/api/guilds/search?q=<target>
```

## Route shape and response schema review — completed

```text
receipt: evidence/real-data/argentum-guild-route-semantics-review.json
review version: guild-route-semantics-review-v1
integrity checks: 22/22
route template verified: true
query shapes verified: true
response envelope verified: true
guild record schema verified: true
limit parameter accepted: true
ready for bounded limit-semantics capture: true
```

Verified record fields:

```text
id: integer
name: string
realm: string
report_count: string
```

All three cases returned the same single record. Therefore truncation, pagination, termination and completeness remain unverified.

## Current boundaries

```text
guild identity verified: true
guild filtering completed: true
guild report manifest deduplicated: true
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

## Data and Git policy

Versioned: source code/tests, migrations, reviewed mappings, canonical documentation and scalar-free evidence receipts.

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

Never commit source guild IDs, report IDs, report rows, private manifests, private decisions, DuckDB, credentials, cookies, tokens, Authorization headers, browser profiles, `.env` or unsanitized HAR.

## Current blockers

1. Current documentation/evidence HEAD requires fresh green Ubuntu, Windows and public-release-audit CI.
2. Limit truncation semantics remain unverified because every observed query returned one record.
3. Pagination, termination and completeness remain unverified.
4. API-derived report membership has not been compared with the private 17-report baseline.
5. Multi-report character identity has not been reviewed.
6. The bounded report slice contains no aura events.
7. No new gameplay mechanic has independent supporting and contradicting evidence.
8. Planner scoring remains disabled.

## Next bounded task

Design and execute a separate bounded multi-result `limit` probe:

1. use an observed guild-search route only;
2. choose a privacy-safe query expected to return multiple records;
3. compare at least two accepted limit values;
4. archive complete raw responses before interpretation;
5. preserve payload hashes, schema fingerprints and ordered record-set hashes;
6. publish only scalar-free counts and decisions;
7. verify truncation behavior without overclaiming pagination or completeness;
8. keep full crawl, graph, performance and scoring false.

## Completion gate

PR #7 remains Draft until reviewed identity/filtering/crawl boundaries, reviewed combatants observations, aura observations and intervals for the bounded slice, independent supporting observations, contradicting evidence review, reproducible provenance, and green Ubuntu/Windows verification are present.
