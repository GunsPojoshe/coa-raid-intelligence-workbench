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

### 1. Pagination evidence

Verified page/limit/offset relations, `hasPrevious`, `hasMore`, exact `limit=25`, terminal transition, successor behavior, sentinels and cross-page report-ID uniqueness.

### 2. Exhaustive public report manifest

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
distinct non-null guild IDs for exact label: 1
```

### 3. Guild identity verification

```text
receipt: evidence/real-data/argentum-guild-identity-decision.json
explicit operator promotion: true
integrity checks: 16/16
independent source identity verified: true
guild identity verified: true
ready for guild filtering: true
```

### 4. Deterministic guild report filtering

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
filter operation: equals_verified_private_source_guild_id
deduplication key: /reports/*/id
selection order: source_manifest_order
```

### 5. Full-crawl collection contract review

Implementation:

```text
src/coa_workbench/collector/guild_full_crawl_contract.py
scripts/build_guild_full_crawl_contract.py
tests/unit/test_guild_full_crawl_contract.py
```

Versioned receipt:

```text
evidence/real-data/argentum-guild-full-crawl-contract.json
```

The contract is bound to:

```text
argentum-public-report-manifest.json
argentum-guild-identity-decision.json
argentum-guild-report-manifest.json
```

Verified contract boundary:

```text
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

The verified 17-report public-manifest-filtered set is the comparison baseline.

## Route-semantics evidence requirements

Before any guild API full crawl:

1. verify exact route template and query parameters;
2. archive complete raw response before interpretation;
3. bind the response to exact payload SHA-256 and schema fingerprint;
4. review collection shape, field types and nullability;
5. verify pagination, offset, page and limit relations if present;
6. verify deterministic termination and successor behavior;
7. verify completeness and capture-time boundaries;
8. publish an explicit scalar-free route-semantics decision.

Observed route shapes remain candidates only:

```text
/api/guilds/progression
/api/guilds/search?q=<value>
/api/guilds/search?q=<value>&limit=<value>
```

No unverified route may be treated as complete or production-ready.

## Set-comparison contract

Any future guild-API-derived report set must be compared with the verified private 17-report baseline and partitioned into:

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

### Guild API route semantics — open for bounded capture

The reviewed contract permits bounded evidence capture only. It does not permit automatic full crawl.

### Full guild crawl — blocked

Blocked until exact route semantics, pagination, termination, completeness and set comparison are explicitly promoted.

### Per-report evidence capture — blocked

After route/full-crawl promotion, capture report, encounter and combatants payloads under reviewed mappings, preserve failures and track coverage against the 17-report baseline.

### Multi-report character graph — blocked

Verify stable identifiers across reports, preserve aliases, detect collisions and never use nickname alone as primary identity.

### Performance and benchmark corpus — blocked

Build comparable versioned distributions before player scores. Separate strength, consistency, confidence and composition utility.

### BiS 25 optimization — blocked

Select 25 from a verified 30-40 character pool under role, encounter, utility, defensive and availability constraints.

## Current boundary

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

Planner scoring remains disabled. Contract review authorizes evidence collection only, not full crawl or scoring.