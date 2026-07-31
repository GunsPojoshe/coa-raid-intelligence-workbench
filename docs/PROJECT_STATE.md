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

PR #7 остаётся open, Draft и mergeable. Фактический HEAD и новый CI перепроверять после каждого documentation/evidence commit.

Последний полностью зелёный baseline до filtering implementation:

```text
commit: 297895c5ce3b26ce2911befd9addf474ef3e1138
Verify repository run: #464
public-release-audit: success
Ubuntu: success
Windows: success
reported tests: 300 passed
```

Run #476 на более новом HEAD подтвердил 303 passed, doctor и DuckDB checks, но Ubuntu завершился failure из-за одного `ruff format --diff` нарушения в `scripts/filter_verified_guild_reports.py`. Форматирование исправлено отдельным commit; новый HEAD требует нового CI.

## Trust boundary

```text
combat-log event = observation
combat-log event != automatic proof of a general mechanic
```

Normalization разрешена только при exact immutable payload, exact SHA-256, exact schema fingerprint и reviewed mapping/extractor.

Parser/schema verification, guild identity verification и report filtering не подтверждают игровую механику. Canonical planner scoring допускает только `corroborated` и `confirmed` mechanics.

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

Read models:

```text
combatants_parser_observation_v1
combatants_actor_build_observation_v1
```

Companion-addon provenance, nested semantics, gameplay meaning and planner use remain unverified.

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
contains raw payload: false
contains source scalar values: false
independent source identity verified: true
guild identity verified: true
ready for guild filtering: true
```

The source guild ID remains private and is not published in Git.

## Deterministic verified-ID filtering — completed

Implementation:

```text
src/coa_workbench/collector/verified_guild_report_filter.py
scripts/filter_verified_guild_reports.py
tests/unit/test_verified_guild_report_filter.py
```

Versioned scalar-free receipt:

```text
evidence/real-data/argentum-guild-report-manifest.json
```

Verified result:

```text
manifest kind: verified_guild_report_manifest
manifest version: verified-guild-report-manifest-v1
source reports: 6454
selected reports: 17
unique selected report IDs: 17
duplicate selected occurrences: 0
integrity checks: 14/14
guild filtering completed: true
guild report manifest deduplicated: true
contains raw payload: false
contains source scalar values: false
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

The exact selected report IDs and report records remain in the local private manifest.

## Current boundaries

```text
guild identity verified: true
ready for guild filtering: true
guild filtering completed: true
guild report manifest deduplicated: true
full crawl collection contract reviewed: false
guild API route semantics verified: false
ready for full guild crawl: false
ready for multi-report character graph: false
ready for performance model: false
ready for BiS 25 scoring: false
planner scoring allowed: false
```

Filtering proves membership in the reviewed captured public snapshot. It does not prove guild API completeness or authorize full crawl.

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

1. The latest HEAD requires green Ubuntu, Windows and public-release-audit CI.
2. Full-crawl collection contract has not been reviewed against the verified 17-report manifest.
3. Guild API route semantics, parameters, pagination and completeness remain unverified.
4. Multi-report character identity has not been reviewed.
5. The bounded report slice contains no aura events.
6. No new gameplay mechanic has independent supporting and contradicting evidence.
7. Planner scoring remains disabled.

## Next bounded task

Review and implement the next gate without opening full crawl automatically:

1. bind the collection contract to the verified identity decision and 17-report manifest;
2. define the public-manifest-filtered report set as the current verified baseline;
3. specify exact route-semantics evidence required before any guild API full crawl;
4. require comparison of API-derived and public-manifest-derived report sets;
5. preserve missing, extra and conflicting reports as evidence;
6. allow only bounded per-report capture after the contract is reviewed;
7. keep graph, performance and scoring gates false.

## Completion gate

PR #7 remains Draft until the relevant E3 checkpoint includes reviewed identity/filtering/crawl boundaries, reviewed combatants observations, aura observations and intervals for the bounded slice, independent supporting observations, contradicting evidence review, reproducible provenance, and green Ubuntu/Windows verification.