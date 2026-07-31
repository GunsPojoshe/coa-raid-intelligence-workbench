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

Parser result, identity decision, report filtering and collection contract review never become gameplay claims automatically.

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

## Completed report and combatants pipeline

```text
normalized: 2 reports, 15 encounters, 31 actors, 31 participants, 0 aura events
reconstructed: 1 report, 14 encounters, 31 actors, 31 participants
persisted canonical observations through 0007: 77
combatants observations through 0008: 1343
actor/build observations: 1339
linked actors: 11
combatants integrity checks: 14/14
```

## Completed public-report manifest

```text
receipt: evidence/real-data/argentum-public-report-manifest.json
route: /api/reports/public
page: 1..259
limit: 25
reports: 6454
unique report IDs: 6454
duplicates: 0
integrity checks: 19/19
exact Argentum label reports: 17
distinct non-null guild IDs: 1
```

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

The source guild ID remains private.

## Completed deterministic guild filtering

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

The exact selected records remain local-only.

## Reviewed full-crawl collection contract

Implementation:

```text
src/coa_workbench/collector/guild_full_crawl_contract.py
scripts/build_guild_full_crawl_contract.py
tests/unit/test_guild_full_crawl_contract.py
```

Receipt:

```text
evidence/real-data/argentum-guild-full-crawl-contract.json
```

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

The 17-report private set is the comparison baseline. Contract review does not authorize full crawl.

## Route-semantics capture protocol

A bounded route-semantics capture must:

1. use only an observed route candidate;
2. record exact route template and query parameters;
3. archive the complete raw response before interpretation;
4. compute payload SHA-256 and schema fingerprint;
5. inventory collection shape, fields, types and nullability;
6. inventory pagination fields without assigning unobserved semantics;
7. verify deterministic termination and completeness;
8. publish a scalar-free route-semantics decision;
9. keep automatic full crawl disabled until explicit promotion.

Observed route shapes remain candidates:

```text
/api/guilds/progression
/api/guilds/search?q=<value>
/api/guilds/search?q=<value>&limit=<value>
```

## API-versus-baseline comparison

Any future guild API report set must be compared with the private verified 17-report baseline and partitioned into:

```text
matching_reports
missing_from_guild_api
extra_in_guild_api
conflicting_report_records
```

Rules:

- deduplicate by source report ID;
- preserve contradicting evidence;
- keep report IDs private;
- do not mark partial results complete;
- preserve failed requests as observations;
- require exact contract/checkpoint binding for resume;
- keep retries bounded.

## Current boundary

```text
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

## Aura capture gap

The bounded report slice contains no aura events. Separate fixtures validate technical Aura State Engine behavior but not magnitude, stacking, scope, provider equivalence or criticality.

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