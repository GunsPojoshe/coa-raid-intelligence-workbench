# Real CoA Logs capture and persistence protocol

Дата актуализации: **2026-08-03**.

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

Parser result, identity decision, report filtering, collection contract review and route/schema review never become gameplay claims automatically.

## Core capture contract

- archive complete body before interpretation;
- keep raw payload immutable and content-addressed;
- separate retrieval observations from payload identity;
- preserve transport failures and contradicting evidence;
- use bounded timeout/retry and endpoint-isolated execution;
- never publish cookie/header values, source IDs or raw source rows;
- unknown hash/fingerprint means reject and review.

Production parser use requires exact payload hash, schema fingerprint, reviewed selectors/types/nullability, deterministic dry run and explicit promotion.

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

## Completed public manifest, identity and filtering

```text
public reports: 6454
unique report IDs: 6454
public-manifest integrity checks: 19/19
identity-decision integrity checks: 16/16
guild identity verified: true
selected guild reports: 17
unique selected report IDs: 17
filter integrity checks: 14/14
```

The source guild ID and report IDs remain private.

## Reviewed full-crawl contract

```text
receipt: evidence/real-data/argentum-guild-full-crawl-contract.json
integrity checks: 12/12
full crawl collection contract reviewed: true
verified private baseline reports: 17
```

Contract review does not authorize full crawl.

## Completed bounded guild route capture

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

Observed query shapes:

```text
/api/guilds/search?q=<target>&limit=1
/api/guilds/search?q=<target>&limit=25
/api/guilds/search?q=<target>
```

## Completed route shape and schema review

```text
receipt: evidence/real-data/argentum-guild-route-semantics-review.json
review version: guild-route-semantics-review-v1
integrity checks: 22/22
route template verified: true
query shapes verified: true
limit parameter accepted: true
response envelope verified: true
guild record schema verified: true
ready for bounded limit-semantics capture: true
```

Verified schema:

```text
top-level object: guilds, success

guild record:
  id: integer
  name: string
  realm: string
  report_count: string
```

All observed cases returned one identical record. Therefore this review does not prove limit truncation, pagination, termination or completeness.

## Next capture protocol: bounded multi-result limit probe

1. Use only the verified guild-search route template.
2. Use a privacy-safe query expected to return multiple records.
3. Compare at least two accepted limit values.
4. Archive complete raw responses before interpretation.
5. Preserve payload, schema, ordered-record-set and source-ID-set hashes.
6. Publish only scalar-free counts, field inventories and decisions.
7. Do not infer pagination, termination or completeness from limit behavior alone.
8. Keep automatic full crawl disabled.

## API-versus-baseline comparison

A future guild API report set must be compared with the private verified 17-report baseline and partitioned into:

```text
matching_reports
missing_from_guild_api
extra_in_guild_api
conflicting_report_records
```

This comparison remains blocked until route, limit, pagination, termination and completeness gates are independently reviewed.

## Current boundary

```text
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

## Aura capture gap

The bounded report slice contains no aura events. Separate fixtures validate technical Aura State Engine behavior but not magnitude, stacking, scope, provider equivalence or criticality.

## Verification

```powershell
uv sync --frozen --extra dev
uv run python scripts/verify_repo.py
```

Live-network behavior is not a unit test. Use deterministic fake responses for collector tests.

## Data policy

Versioned: mappings, code/tests, migrations, documentation and scalar-free receipts.

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
