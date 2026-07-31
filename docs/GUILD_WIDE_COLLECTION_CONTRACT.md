# Guild-wide report collection contract

## Goal

Prepare a reproducible guild-wide corpus for a future `BiS 25` roster calculation.

Operator target:

```text
guild label: Argentum
candidate characters: 30-40
final roster: 25
```

This document defines collection boundaries, not a scoring policy.

## Verified foundation

Current exact evidence includes:

```text
1 persisted report
14 persisted encounters
31 report actors
31 participants
1343 persisted combatants parser observations
1339 actor-linked build observations
11 exact combatants actor links
```

The exhaustive public snapshot is versioned at:

```text
evidence/real-data/argentum-public-report-manifest.json
```

Manifest facts:

```text
route: /api/reports/public
limit: 25
pages: 259
reports: 6454
unique report IDs: 6454
duplicates: 0
integrity checks: 19/19
```

Guild-field facts:

```text
reports with both guild fields: 1171
distinct guild identity pairs: 88
exact Argentum label reports: 17
distinct non-null guild IDs for exact label: 1
```

The snapshot is exhaustive for its captured terminal contract. The source guild identity for the operator target remains unresolved.

## Phase status

### 1. Pagination evidence — completed

Verified:

- page, limit and offset relations;
- `hasPrevious` and `hasMore` semantics;
- promoted exact `limit=25` contract;
- deterministic terminal transition;
- successor empty-page behavior;
- start/end sentinel stability;
- cross-page report-ID uniqueness.

### 2. Public report manifest — completed

Verified:

- pages `1..259` captured;
- terminal page contains four reports;
- 6454 expected and observed reports;
- 6454 unique IDs;
- zero duplicate occurrences;
- private manifest bound by SHA-256;
- scalar-free public receipt.

### 3. Guild identity binding — open

Required:

- review the 17 exact `Argentum` rows in the private manifest;
- verify that all map to the same non-null source guild ID;
- check that the ID is not associated with another non-empty guild name in the same snapshot, or document conflicts;
- inspect independent source identity evidence where available;
- do not infer identity from title, uploader or nickname;
- publish a scalar-free manual review/promotion receipt without exposing the raw ID.

Until this phase is explicitly promoted:

```text
guild identity verified: false
guild filtering allowed: false
full guild crawl allowed: false
```

### 4. Guild report filtering — blocked by identity review

After identity promotion:

- filter by the verified source guild ID, not by name alone;
- produce a deterministic deduplicated guild report list;
- preserve raw archive references, observation IDs and payload hashes;
- record captured time and completeness boundaries;
- issue a scalar-free guild report manifest receipt.

### 5. Per-report evidence capture — blocked

For every selected guild report:

- capture report, encounter and combatants payloads;
- normalize only through reviewed mappings/extractors;
- persist immutable observations;
- never mutate core identities implicitly.

### 6. Multi-report character graph — blocked

- verify stable source actor/character identifiers across reports;
- preserve aliases and rename history;
- detect collisions and split identities;
- never use nickname alone as primary identity.

### 7. Performance and benchmark corpus — blocked

- collect versioned boss, difficulty, role and time-cohort observations;
- separate performance, consistency, sample confidence and composition utility;
- build distributions before scores.

### 8. BiS 25 optimization — blocked

- select 25 from a verified 30-40 character pool;
- enforce role, encounter, utility and availability constraints;
- publish confidence, reasons, reserves and composition risks;
- keep scoring policy versioned and auditable.

## Current boundary

Open now:

```text
local guild identity review
scalar-free identity decision receipt
```

Blocked now:

```text
guild filtering
full guild crawl
multi-report character aggregation
performance scoring
global benchmark scoring
BiS 25 roster optimization
```

Planner scoring remains disabled. Manifest completeness is not a scoring authorization.
