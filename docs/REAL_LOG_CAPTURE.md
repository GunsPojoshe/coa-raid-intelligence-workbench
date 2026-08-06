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

Parser result, identity decision, report filtering, collection contract review, route/schema review и successful capture никогда не становятся gameplay claims автоматически.

## Core capture contract

- archive complete body before interpretation;
- keep raw payload immutable and content-addressed;
- separate retrieval observations from payload identity;
- preserve transport failures and contradicting evidence;
- use bounded timeout/retry and endpoint-isolated execution;
- never publish cookie/header values, source IDs, query values, URLs or raw source rows;
- unknown hash/fingerprint means reject and review;
- partial capture may not be marked complete;
- capture readiness and semantic promotion are separate stages.

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

## Implemented bounded multi-result limit capture

Implementation:

```text
src/coa_workbench/collector/guild_limit_semantics_capture.py
scripts/capture_guild_limit_semantics.py
tests/unit/test_guild_limit_semantics_capture.py
```

### Request contract

Exactly three requests:

```text
case 1: private query + low limit
case 2: private query + high limit
case 3: private query + identical high-limit repeat
```

Default limits:

```text
low limit: 1
high limit: 25
```

### Transport contract

- verified route template only: `/api/guilds/search`;
- HTTPS same-origin only;
- `spa_fetch_context`-compatible public headers;
- no Authorization, cookies or credentials;
- redirects disabled;
- automatic retries disabled;
- bounded connection/total timeout;
- bounded maximum response bytes;
- immutable archive before interpretation;
- separate raw endpoint code per request case;
- preserve transport/HTTP failures as observations.

### Review-readiness contract

Capture may set `ready_for_limit_semantics_review=true` only when:

- all three responses complete and valid;
- all three conform to the reviewed response schema;
- low result count equals low limit;
- high result count is greater than low and not greater than high;
- high-limit repeat has identical payload/schema/ordered-record evidence;
- high-limit repeat has identical source-ID-order hash;
- low-limit source-ID hash sequence is an exact prefix of high-limit sequence.

A successful capture must still keep:

```text
limit truncation semantics verified: false
pagination semantics verified: false
termination semantics verified: false
completeness verified: false
ready for full guild crawl: false
planner scoring allowed: false
```

Semantic promotion requires a separate review receipt bound to the exact public capture hash.

### Privacy contract

Private/local-only:

```text
query value
request URLs
source IDs
raw guild records
raw payloads
error text
private capture receipt
```

Public receipt may contain only:

```text
attempt counts
completion counts
result counts
limit values
payload/schema/record-set hashes
field inventories
boolean integrity decisions
preserved trust boundaries
```

### CLI

```powershell
uv run --no-sync python scripts/capture_guild_limit_semantics.py --query "<PRIVATE_MULTI_RESULT_QUERY>"
```

Defaults:

```text
route review:
  evidence/real-data/argentum-guild-route-semantics-review.json

private output:
  data/extracted/report-discovery/argentum-guild-limit-semantics-capture.private.json

public output:
  data/exchange/out/argentum-guild-limit-semantics-capture.json

raw archive:
  data/raw

database:
  data/warehouse/coa.duckdb
```

Exit codes:

```text
0 = ready for separate limit-semantics review
2 = bounded capture completed but evidence is insufficient
other = input/execution failure
```

Only the public output may be uploaded/versioned.

## Required review after capture

The separate review must:

1. validate exact capture kind/version;
2. bind to exact route-review hash;
3. bind to exact public capture SHA-256;
4. verify all integrity checks independently;
5. verify result-count relations;
6. verify stable high-limit repeat;
7. verify low-prefix relation by hashes;
8. verify public privacy boundary;
9. preserve pagination/termination/completeness false;
10. explicitly promote or reject limit truncation semantics.

Capture alone is never promotion.

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

Never commit credentials, cookies, tokens, browser profiles, `.env`, unsanitized HAR, source guild IDs, report IDs, private query values or source-scalar private batches.

## E3 acceptance boundary

E3 remains Draft until reviewed identity/filtering/crawl boundaries, reviewed combatants observations, aura observations and intervals for the bounded slice, independent supporting observations, contradicting evidence review, versioned provenance, and green Ubuntu/Windows CI are present.
