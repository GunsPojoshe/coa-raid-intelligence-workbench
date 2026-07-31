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

Parser result never becomes a gameplay claim automatically.

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

Exact report/encounter mappings are published and selected-parser results are persisted through migration `0007_selected_parser_persistence`:

```text
normalized: 2 reports, 15 encounters, 31 actors, 31 participants, 0 aura events
reconstructed: 1 report, 14 encounters, 31 actors, 31 participants
persisted canonical observations: 77
rejects: 0
```

## Completed combatants persistence

Exact combatants binding:

```text
payload:     45672e0f0ff9eb461c575bdd38385795daa6326378bc3f8ad51474276140dc14
fingerprint: 41d6d15422c668f83d2ccae1ec0ff2969671861f9e43b21cb371578961c5f8ff
```

Migration and receipt:

```text
migrations/0008_combatants_observation_persistence.sql
evidence/real-data/observed-combatants-info-persistence.json
```

```text
persisted observations: 1343
actor/build observations: 1339
linked actors: 11
integrity checks: 14/14
core actor mutations: 0
transaction committed: true
```

The private database contains source scalars and remains local. Read models are parser observation views, not canonical gameplay/build projections.

## Completed public-report pagination and manifest

The production bounded discovery default remains conservative. An explicit reviewed promotion permits exact `limit=25` use for terminal search and manifest capture.

Manifest request:

```text
GET /api/reports/public
page=1..259
limit=25
sortBy=created_at
sortOrder=desc
```

Capture implementation uses bounded concurrency only for the promoted manifest path. Each worker has a separate HTTP session; raw archive writes are serialized; checkpoint state is flushed progressively. Start/end sentinels and aggregate integrity gates remain mandatory.

Versioned receipt:

```text
evidence/real-data/argentum-public-report-manifest.json
```

Result:

```text
completed pages: 259
reports: 6454
unique report IDs: 6454
duplicates: 0
terminal page reports: 4
integrity checks: 19/19
sentinel stability: verified
receipt contains source scalar values: false
private manifest contains source scalar values: true
```

Guild fields:

```text
reports with both guild fields: 1171
distinct guild identity pairs: 88
exact Argentum label reports: 17
distinct non-null guild IDs for exact label: 1
```

This proves captured snapshot completeness and consistency. It does not prove target guild identity.

## Guild identity review protocol

Input:

- versioned scalar-free manifest receipt;
- exact local private manifest whose SHA-256 matches the receipt;
- optional independent source identity evidence.

Required review:

1. recompute the private manifest SHA-256;
2. isolate exact normalized `guild_name == "Argentum"` rows;
3. confirm the receipt counts (`17` rows, `1` distinct non-null guild ID);
4. check whether that ID appears with another non-empty guild name in the same snapshot;
5. inspect independent source evidence where available;
6. do not infer identity from report title, uploader or nickname;
7. record reviewer, evidence hashes, counts, conflict flags and decision;
8. publish only a scalar-free receipt and keep the raw guild ID local.

Possible decisions:

```text
verified_target_identity
insufficient_evidence
conflicting_evidence
rejected_identity
```

Only `verified_target_identity` may enable deterministic guild filtering. Identity verification does not enable performance or planner scoring.

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

Never commit credentials, cookies, tokens, browser profiles, `.env`, unsanitized HAR or source-scalar private batches.

## E3 acceptance boundary

E3 remains Draft until reviewed guild identity/crawl boundaries, reviewed combatants observations, aura observations and intervals for the bounded slice, independent supporting observations, contradicting evidence review, versioned provenance, and green Ubuntu/Windows CI are present.
