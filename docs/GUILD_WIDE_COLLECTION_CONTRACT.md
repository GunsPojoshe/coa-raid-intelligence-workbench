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

Exhaustive public snapshot:

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

## Phase status

### 1. Pagination evidence — completed

Verified page/limit/offset relations, `hasPrevious`, `hasMore`, exact `limit=25`, terminal transition, successor behavior, sentinels and cross-page report-ID uniqueness.

### 2. Public report manifest — completed

Verified pages `1..259`, 6454 expected/observed reports, 6454 unique IDs, zero duplicates, exact private-manifest SHA binding and scalar-free public receipt.

### 3. Snapshot identity review — completed

Verified 17 exact target-label rows, one non-null candidate source ID, zero conflicting non-empty names and 10/10 integrity checks.

### 4. Independent guild-search evidence — completed

Reviewed mapping:

```text
$.guilds[].id           -> guild_id
$.guilds[].name         -> guild_name
$.guilds[].realm        -> realm
$.guilds[].report_count -> report_count
```

Private evidence confirms one search result, source-ID equality with the snapshot candidate and name equality after Unicode casefold. Public receipts expose neither raw payload nor source guild ID.

Guild API route semantics remain unverified.

### 5. Explicit guild identity decision — completed

```text
receipt: evidence/real-data/argentum-guild-identity-decision.json
explicit operator promotion: true
integrity checks: 16/16
independent source identity verified: true
guild identity verified: true
ready for guild filtering: true
contains raw payload: false
contains source scalar values: false
```

### 6. Deterministic guild report filtering — completed

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

Verified result:

```text
source reports: 6454
selected reports: 17
unique selected report IDs: 17
duplicate selected occurrences: 0
integrity checks: 14/14
guild filtering completed: true
guild report manifest deduplicated: true
contains source scalar values: false
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

Exact report IDs and rows remain local-only in the private guild manifest.

### 7. Full-crawl collection contract review — open

The current verified baseline is the 17-report set obtained from the exhaustive public manifest by exact verified source guild ID.

The next contract must bind all three receipts:

```text
evidence/real-data/argentum-public-report-manifest.json
evidence/real-data/argentum-guild-identity-decision.json
evidence/real-data/argentum-guild-report-manifest.json
```

Required contract decisions:

- identify the exact purpose of any guild API route;
- separate route discovery from route semantics verification;
- define bounded capture limits and stop conditions;
- require immutable raw payload archive before interpretation;
- require exact payload SHA-256 and schema fingerprint;
- define pagination, termination and completeness evidence;
- require deterministic comparison with the verified 17-report baseline;
- preserve missing, extra and conflicting reports;
- define partial-failure and resume behavior;
- require explicit operator promotion before automatic full crawl;
- keep report IDs and source guild ID private.

Until the contract is reviewed:

```text
full crawl collection contract reviewed: false
guild API route semantics verified: false
ready for full guild crawl: false
```

### 8. Guild API route semantics — blocked by contract review

Before using guild API routes for exhaustive collection:

- verify exact request parameters and response contract;
- capture immutable raw payloads;
- review pagination and completeness semantics;
- bind mappings/extractors to exact hashes/fingerprints;
- compare the API-derived report set with the verified public-manifest filter;
- preserve discrepancies and contradicting evidence;
- publish a scalar-free route/collection decision receipt.

### 9. Bounded per-report evidence capture — blocked

For every selected report admitted by the reviewed contract:

- capture report, encounter and combatants payloads;
- normalize only through reviewed mappings/extractors;
- persist immutable observations;
- never mutate core identities implicitly;
- preserve failed captures and incomplete coverage;
- record coverage against the 17-report baseline.

### 10. Multi-report character graph — blocked

- verify stable source actor/character identifiers across reports;
- preserve aliases and rename history;
- detect collisions and split identities;
- never use nickname alone as primary identity;
- target a reviewed pool of 30-40 unique candidate characters.

### 11. Performance and benchmark corpus — blocked

- collect versioned boss, difficulty, role and time-cohort observations;
- separate performance, consistency, sample confidence and composition utility;
- build comparable distributions before scores;
- keep guild execution distinct from global mechanic evidence.

### 12. BiS 25 optimization — blocked

- select 25 from a verified 30-40 character pool;
- enforce role, encounter, utility, defensive and availability constraints;
- publish confidence, reasons, reserves and composition risks;
- keep scoring policy versioned and auditable;
- use only evidence admitted by the trust model.

## Current boundary

Completed:

```text
guild identity verified
deterministic guild filtering
17-report deduplicated scalar-free guild manifest
```

Open now:

```text
full-crawl collection contract review
```

Blocked now:

```text
guild API route semantic promotion
full guild crawl
multi-report character aggregation
performance scoring
global benchmark scoring
BiS 25 roster optimization
```

Planner scoring remains disabled. Identity verification and filtering authorize neither full crawl nor scoring.