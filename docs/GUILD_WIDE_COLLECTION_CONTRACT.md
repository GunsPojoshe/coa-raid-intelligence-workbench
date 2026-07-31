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

Receipt:

```text
evidence/real-data/argentum-guild-identity-snapshot-review.json
```

Verified:

```text
17 exact target-label rows
one non-null candidate source ID
17 reports associated with that candidate ID
zero conflicting non-empty guild names
10/10 integrity checks
snapshot internal identity consistent: true
```

This is internal snapshot consistency, not independent identity verification.

### 4. Independent guild-search evidence — completed as candidate review

Profiled application-asset recovery exposed three guild route candidates. Search access required a reviewed SPA fetch context.

Observed route shapes:

```text
/api/guilds/progression
/api/guilds/search?q=<value>
/api/guilds/search?q=<value>&limit=<value>
```

Schema inventory and mapping review verified one search result with:

```text
$.guilds[].id           -> guild_id
$.guilds[].name         -> guild_name
$.guilds[].realm        -> realm
$.guilds[].report_count -> report_count
```

Private evidence shows:

```text
search results: 1
source ID matches snapshot candidate: 1
name matches Argentum after Unicode casefold: 1
cross-endpoint identity candidate observed: true
```

Public receipts contain no raw guild ID or raw payload.

Guild API route semantics remain unverified. The result is an independent identity candidate, not automatic promotion.

### 5. Explicit guild identity decision — implemented, awaiting local receipt

Implementation:

```text
scripts/decide_guild_identity.py
src/coa_workbench/collector/guild_identity_decision.py
```

The decision requires:

```text
--promote-identity
```

It revalidates the public/private manifest, snapshot review, search mapping, cross-endpoint ID equality, name casefold equality and scalar-free boundary.

Until the decision receipt is produced and reviewed:

```text
guild identity verified: false
guild filtering allowed: false
full guild crawl allowed: false
```

A successful decision may open only:

```text
guild identity verified: true
guild filtering allowed: true
```

It must not open:

```text
guild API route semantics verified
full guild crawl
multi-report character graph
performance model
BiS 25 scoring
planner scoring
```

### 6. Guild report filtering — blocked by explicit decision receipt

After verified identity promotion:

- filter by the verified source guild ID, not by name;
- recompute the bound private manifest;
- produce a deterministic deduplicated guild report list;
- preserve report IDs only in private artifacts;
- preserve source manifest hashes and time boundary;
- issue a scalar-free guild report manifest receipt;
- do not infer full-crawl completeness from filtering alone.

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
explicit local guild identity decision
scalar-free identity decision receipt review
```

Blocked now:

```text
guild filtering
guild API route semantic promotion
full guild crawl
multi-report character aggregation
performance scoring
global benchmark scoring
BiS 25 roster optimization
```

Planner scoring remains disabled. Manifest completeness, schema mapping and identity candidacy are not scoring authorization.