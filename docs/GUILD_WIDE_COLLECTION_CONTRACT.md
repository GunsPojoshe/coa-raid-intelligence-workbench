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

Receipt:

```text
evidence/real-data/argentum-guild-identity-decision.json
```

Verified boundary:

```text
explicit operator promotion: true
integrity checks: 16/16
independent source identity verified: true
guild identity verified: true
ready for guild filtering: true
contains raw payload: false
contains source scalar values: false
```

Still false:

```text
guild API route semantics verified
ready for full guild crawl
ready for multi-report character graph
ready for performance model
ready for BiS 25 scoring
planner scoring allowed
```

### 6. Deterministic guild report filtering — implemented, execution pending

Implementation:

```text
src/coa_workbench/collector/verified_guild_report_filter.py
scripts/filter_verified_guild_reports.py
tests/unit/test_verified_guild_report_filter.py
```

Required behavior:

- use the verified source guild ID from the private identity decision;
- never filter by name alone;
- revalidate public/private manifest and decision SHA bindings;
- preserve source-manifest order;
- deduplicate by `/reports/*/id`;
- reject conflicting selected names;
- keep report IDs and rows in the private output only;
- emit a scalar-free receipt with counts and hashes;
- keep full crawl and scoring disabled.

Expected outputs:

```text
private:
  data/extracted/report-discovery/argentum-guild-report-manifest.private.json

scalar-free receipt:
  data/exchange/out/argentum-guild-report-manifest.json
```

Filtering is not complete until the local receipt is produced and reviewed.

### 7. Guild API route semantics and full crawl — separately blocked

Before using guild API routes for exhaustive collection:

- verify exact request parameters and response contract;
- capture immutable raw payloads;
- review pagination and completeness semantics;
- bind mappings/extractors to exact hashes/fingerprints;
- compare the API-derived report set with the verified public-manifest filter;
- preserve discrepancies and contradicting evidence;
- publish a scalar-free route/collection decision receipt.

### 8. Per-report evidence capture — blocked

For every selected report:

- capture report, encounter and combatants payloads;
- normalize only through reviewed mappings/extractors;
- persist immutable observations;
- never mutate core identities implicitly;
- preserve failed captures and incomplete coverage.

### 9. Multi-report character graph — blocked

- verify stable source actor/character identifiers across reports;
- preserve aliases and rename history;
- detect collisions and split identities;
- never use nickname alone as primary identity;
- target a reviewed pool of 30-40 unique candidate characters.

### 10. Performance and benchmark corpus — blocked

- collect versioned boss, difficulty, role and time-cohort observations;
- separate performance, consistency, sample confidence and composition utility;
- build comparable distributions before scores;
- keep guild execution distinct from global mechanic evidence.

### 11. BiS 25 optimization — blocked

- select 25 from a verified 30-40 character pool;
- enforce role, encounter, utility, defensive and availability constraints;
- publish confidence, reasons, reserves and composition risks;
- keep scoring policy versioned and auditable;
- use only evidence admitted by the trust model.

## Current boundary

Open now:

```text
deterministic local guild filtering
scalar-free guild report manifest receipt review
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

Planner scoring remains disabled. Identity verification authorizes filtering only.
