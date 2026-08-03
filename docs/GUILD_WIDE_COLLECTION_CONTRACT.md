# Guild-wide report collection contract

## Goal

Prepare a reproducible guild-wide corpus for a future `BiS 25` roster calculation.

```text
guild label: Argentum
candidate characters: 30-40
final roster: 25
```

This document defines collection and trust boundaries, not a scoring policy.

## Verified foundation

```text
1 persisted report
14 persisted encounters
31 report actors
31 participants
1343 persisted combatants parser observations
1339 actor-linked build observations
11 exact combatants actor links
```

## Completed phases

### 1. Public pagination and exhaustive manifest

```text
receipt: evidence/real-data/argentum-public-report-manifest.json
route: /api/reports/public
limit: 25
pages: 259
reports: 6454
unique report IDs: 6454
duplicates: 0
integrity checks: 19/19
exact Argentum label reports: 17
```

### 2. Guild identity and deterministic filtering

```text
identity receipt: evidence/real-data/argentum-guild-identity-decision.json
identity integrity checks: 16/16
guild identity verified: true

filtered receipt: evidence/real-data/argentum-guild-report-manifest.json
selected reports: 17
unique selected report IDs: 17
filter integrity checks: 14/14
```

The source guild ID and report IDs remain private.

### 3. Full-crawl collection contract

```text
receipt: evidence/real-data/argentum-guild-full-crawl-contract.json
integrity checks: 12/12
full crawl collection contract reviewed: true
verified comparison baseline reports: 17
```

The contract requires immutable raw capture, exact payload SHA-256, schema fingerprint, reviewed fields, pagination/termination/completeness proof and explicit set comparison.

### 4. Bounded guild-search capture

```text
receipt: evidence/real-data/argentum-guild-route-semantics-capture.json
attempts: 3
completed attempts: 3
HTTP 200 responses: 3
integrity checks: 13/13
observed result counts: [1]
payload/schema/source-ID-set hashes stable: true
pagination object observed: false
```

Observed query shapes:

```text
/api/guilds/search?q=<target>&limit=1
/api/guilds/search?q=<target>&limit=25
/api/guilds/search?q=<target>
```

### 5. Route shape and response schema review

```text
receipt: evidence/real-data/argentum-guild-route-semantics-review.json
integrity checks: 22/22
route template verified: true
query shapes verified: true
limit parameter accepted: true
response envelope verified: true
guild record schema verified: true
ready for bounded limit-semantics capture: true
```

Verified response schema:

```text
top-level: object
keys: guilds, success

guild record:
  id: integer
  name: string
  realm: string
  report_count: string
```

This review proves route shape and schema only. Because all cases returned one identical record, it does not prove limit truncation behavior.

## Next bounded phase: multi-result limit probe

The next probe must:

1. use only the verified `/api/guilds/search` route template;
2. use a privacy-safe query expected to return multiple guild records;
3. compare at least two accepted `limit` values;
4. archive complete raw responses before interpretation;
5. preserve ordered record-set, source-ID-set, payload and schema hashes;
6. publish only scalar-free counts and decisions;
7. reject any attempt to infer pagination, termination or completeness from limit behavior alone.

A one-result response cannot verify limit truncation semantics.

## Set-comparison contract

Any future guild-API-derived report set must be compared with the private verified 17-report baseline and partitioned into:

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

## Remaining phases

```text
bounded multi-result limit probe
-> pagination semantics review
-> termination/completeness review
-> API-versus-baseline set comparison
-> explicit full-crawl promotion, only if all gates pass
-> per-report capture
-> multi-report character graph
-> performance corpus
-> BiS 25 optimization
```

## Current boundary

```text
guild identity verified: true
guild filtering completed: true
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

Planner scoring remains disabled. Route/schema review authorizes only the next bounded evidence probe.
