# Real CoA Logs capture and persistence protocol

Дата актуализации: **2026-07-31**.

## Purpose

Безопасный воспроизводимый путь от real response `coa.ascensionlogs.gg` до canonical observations:

```text
HTTP response
-> immutable raw payload
-> retrieval observation manifest
-> SHA-256 + schema fingerprint
-> structural/field review
-> candidate mapping or extractor design
-> exact raw validation
-> manual promotion/publication
-> normalization/extraction
-> deterministic reconstruction
-> atomic immutable persistence
-> scalar-free receipt
```

Parser result, identity decision and report filtering never become gameplay claims automatically.

## HTTP capture contract

Use versioned profile:

```text
coa-fetch-context-v1
```

Requirements:

- persistent same-origin session;
- in-memory cookie jar only;
- bounded timeout and retry;
- endpoint-isolated execution;
- progressive checkpointing;
- archive complete body before interpretation;
- distinguish HTTP status from complete body read;
- preserve transport errors;
- never store cookie/header values.

HAR fallback remains sensitive and local-only.

## Raw archive contract

Raw payload is immutable, content-addressed by SHA-256, gzip-compressed when JSON, deduplicated by body hash, and linked to separate retrieval observations and sanitized request metadata.

Do not alter archived bytes to satisfy tests.

## Mapping/extractor contract

Production parser use requires:

```text
exact archived payload
+ exact payload hash
+ exact schema fingerprint
+ explicit reviewed selectors/types/nullability
+ reviewer metadata
+ deterministic dry run
+ explicit manual promotion
```

Unknown hash/fingerprint means reject and review. Verified parser compatibility does not confirm mechanic semantics.

## Completed report/encounter pipeline

Observed routes:

```text
/api/reports/{template}
/api/reports/{template}/encounters/{template}
/api/reports/{template}/encounters/{template}/combatants-info
```

No separate `/roster` route was observed.

```text
normalized: 2 reports, 15 encounters, 31 actors, 31 participants, 0 aura events
reconstructed: 1 report, 14 encounters, 31 actors, 31 participants
persisted canonical observations through 0007: 77
rejects: 0
```

## Completed combatants persistence

```text
payload:     45672e0f0ff9eb461c575bdd38385795daa6326378bc3f8ad51474276140dc14
fingerprint: 41d6d15422c668f83d2ccae1ec0ff2969671861f9e43b21cb371578961c5f8ff
migration: migrations/0008_combatants_observation_persistence.sql
receipt: evidence/real-data/observed-combatants-info-persistence.json
persisted observations: 1343
actor/build observations: 1339
linked actors: 11
integrity checks: 14/14
core actor mutations: 0
```

The private database contains source scalars and remains local. Read models are parser observation views, not canonical gameplay/build projections.

## Completed public-report manifest

```text
receipt: evidence/real-data/argentum-public-report-manifest.json
route: /api/reports/public
page: 1..259
limit: 25
sortBy: created_at
sortOrder: desc
reports: 6454
unique report IDs: 6454
duplicates: 0
terminal page reports: 4
integrity checks: 19/19
sentinel stability: verified
exact Argentum label reports: 17
distinct non-null guild IDs for exact label: 1
```

The public receipt is scalar-free. The exact report records remain in the private manifest.

## Completed guild identity decision

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

## Completed deterministic guild filtering

Implementation:

```text
src/coa_workbench/collector/verified_guild_report_filter.py
scripts/filter_verified_guild_reports.py
tests/unit/test_verified_guild_report_filter.py
```

Versioned receipt:

```text
evidence/real-data/argentum-guild-report-manifest.json
```

Selection contract:

```text
filter field: /reports/*/guild_id
operation: equals_verified_private_source_guild_id
deduplication key: /reports/*/id
selection order: source_manifest_order
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
contains raw payload: false
contains source scalar values: false
report IDs published: false
source guild ID published: false
```

The exact selected records remain in:

```text
data/extracted/report-discovery/argentum-guild-report-manifest.private.json
```

This private file is local-only.

## Full-crawl collection gate

Filtering is not full crawl. Before a guild API route may be used for exhaustive collection:

1. verify exact route and query parameters;
2. capture immutable raw payloads;
3. review response schema and source scalars;
4. verify pagination, termination and completeness semantics;
5. bind every claim to exact hashes/fingerprints;
6. compare guild-API-derived and public-manifest-derived report sets;
7. retain missing, extra and conflicting reports;
8. publish a scalar-free collection decision receipt;
9. keep automatic full crawl disabled until explicit promotion.

Current boundary:

```text
full crawl collection contract reviewed: false
guild API route semantics verified: false
ready for full guild crawl: false
ready for multi-report character graph: false
ready for performance model: false
ready for BiS 25 scoring: false
planner scoring allowed: false
```

## Aura capture gap

The bounded report slice contains no aura events. Separate fixtures for report `2987`, spell `968746` validate technical Aura State Engine behavior but not magnitude, stacking, scope, provider equivalence or criticality.

Future aura work must archive exact payloads, review fields/types, publish verified mappings, normalize events, reconstruct intervals, and compare supporting/contradicting observations.

## Verification

```powershell
uv sync --frozen --extra dev
uv run python scripts/verify_repo.py
```

Run focused deterministic tests for collector/storage changes. Never use live-network behavior as a unit test.

## Data policy

Versioned:

- mappings;
- code/tests;
- migrations;
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

Never commit credentials, cookies, tokens, browser profiles, `.env`, unsanitized HAR, source guild IDs, report IDs or source-scalar private batches.

## E3 acceptance boundary

E3 remains Draft until reviewed identity/filtering/crawl boundaries, reviewed combatants observations, aura observations and intervals for the bounded slice, independent supporting observations, contradicting evidence review, versioned provenance, and green Ubuntu/Windows CI are present.