# Фактическое состояние проекта

Дата актуализации: **2026-07-31**.

Документ фиксирует operational state. Перед работой перепроверять GitHub, код, local private artifacts, versioned receipts и CI.

## Репозиторий

```text
repository: GunsPojoshe/coa-raid-intelligence-workbench
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

PR #7 остаётся open, Draft и mergeable. Фактический HEAD и новый CI перепроверять после каждого commit.

Последний полностью зелёный baseline до filtering implementation:

```text
commit: 297895c5ce3b26ce2911befd9addf474ef3e1138
Verify repository run: #464
public-release-audit: success
Ubuntu: success
Windows: success
reported tests: 300 passed
```

Run #476 подтвердил 303 passed, doctor и DuckDB checks, но Ubuntu завершился failure из-за одного `ruff format --diff` нарушения. Форматирование исправлено. Последующие commits требуют нового CI.

## Trust boundary

```text
combat-log event = observation
combat-log event != automatic proof of a general mechanic
```

Parser/schema verification, guild identity verification, report filtering и contract review не подтверждают игровую механику. Canonical planner scoring допускает только `corroborated` и `confirmed` mechanics.

## Реализованный фундамент

- localhost FastAPI raid planner и DuckDB plans;
- immutable content-addressed raw archive;
- separate retrieval observations;
- JSON/HAR privacy-safe tooling;
- schema fingerprints и reviewed mappings;
- report/encounter/actor/participant/aura records;
- normalization rejects и Aura State Engine;
- hypotheses, supporting/contradicting evidence и trust policies;
- migrations `0001`–`0008`;
- repository verifier, Ubuntu/Windows CI и public-release audit.

## Report/encounter checkpoint

```text
normalized: 2 reports, 15 encounters, 31 actors, 31 participants, 0 aura events
reconstructed: 1 report, 14 encounters, 31 actors, 31 participants, 0 field conflicts
persisted through 0007: 77 canonical entity observations
```

## Combatants checkpoint

```text
migration: 0008_combatants_observation_persistence
persisted observations: 1343
actor/build observations: 1339
distinct linked actors: 11
integrity checks: 14/14
core actor mutations: 0
```

## Exhaustive public-report manifest

```text
receipt: evidence/real-data/argentum-public-report-manifest.json
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

## Explicit guild identity decision — completed

```text
receipt: evidence/real-data/argentum-guild-identity-decision.json
integrity checks: 16/16
explicit operator promotion: true
cross-endpoint source-ID equality: true
cross-endpoint name casefold equality: true
independent source identity verified: true
guild identity verified: true
ready for guild filtering: true
```

The source guild ID remains private.

## Deterministic verified-ID filtering — completed

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

Selection contract:

```text
filter field: /reports/*/guild_id
operation: equals_verified_private_source_guild_id
deduplication key: /reports/*/id
order: source_manifest_order
```

## Full-crawl collection contract — reviewed

Implementation:

```text
src/coa_workbench/collector/guild_full_crawl_contract.py
scripts/build_guild_full_crawl_contract.py
tests/unit/test_guild_full_crawl_contract.py
```

Versioned scalar-free receipt:

```text
evidence/real-data/argentum-guild-full-crawl-contract.json
```

Verified contract facts:

```text
contract version: guild-full-crawl-contract-v1
source public reports: 6454
selected guild reports: 17
integrity checks: 12/12
full crawl collection contract reviewed: true
ready for bounded route-semantics capture: true
guild API route semantics verified: false
automatic full guild crawl allowed: false
ready for full guild crawl: false
planner scoring allowed: false
```

The contract requires exact route/query verification, immutable raw capture, payload SHA-256, schema fingerprint, pagination/termination/completeness proof and deterministic comparison with the verified 17-report baseline. Missing, extra and conflicting reports must be retained as evidence.

## Current boundaries

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

Contract review opens only bounded route-semantics evidence capture. It does not authorize full crawl.

## Data and Git policy

Versioned:

- source code and tests;
- migrations;
- reviewed mappings;
- canonical documentation;
- scalar-free evidence receipts.

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

1. Latest HEAD requires green Ubuntu, Windows and public-release-audit CI.
2. Guild API exact route/query semantics remain unverified.
3. Guild API response schema, pagination, termination and completeness remain unverified.
4. API-derived report set has not been compared with the verified 17-report baseline.
5. Multi-report character identity has not been reviewed.
6. The bounded report slice contains no aura events.
7. No new gameplay mechanic has independent supporting and contradicting evidence.
8. Planner scoring remains disabled.

## Next bounded task

Perform bounded guild API route-semantics capture under the reviewed contract:

1. use only observed route candidates;
2. record exact route and query parameters;
3. archive complete raw responses before interpretation;
4. produce payload SHA-256 and schema fingerprints;
5. inventory response collections and pagination fields without assigning unobserved semantics;
6. verify deterministic termination/completeness before any full crawl promotion;
7. compare future API report membership with the private 17-report baseline;
8. preserve all discrepancies;
9. keep full crawl, graph, performance and scoring false.

## Completion gate

PR #7 remains Draft until reviewed identity/filtering/crawl boundaries, reviewed combatants observations, aura observations and intervals for the bounded slice, independent supporting observations, contradicting evidence review, reproducible provenance, and green Ubuntu/Windows verification are present.