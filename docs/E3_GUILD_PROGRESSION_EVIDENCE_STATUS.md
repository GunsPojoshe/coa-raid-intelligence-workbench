# E3 guild progression evidence status

Дата актуализации: **2026-08-13**.

## Corrected frontend evidence

Offline review of the exact archived SPA asset corrected the historical progression interpretation.

The exact literal `/api/guilds/progression` appears once in frontend cache-exclusion configuration and is not directly requested.

Observed direct progression frontend contracts:

```text
GET /api/guilds/progression/rankings                 (2 callsites)
GET /api/guilds/progression/full-clears              (1 callsite)
GET /api/guilds/progression/rankings/{bossId}        (1 callsite)
```

All four observed direct progression calls use GET. No direct POST progression call was observed.

Observed parameter-key sets:

```text
rankings:
  [bracket]
  [bracket,difficulty,location,phaseId,realm]
  explicit empty params-object branch: true

full-clears:
  [bracket,difficulty,location,page,phaseId,realm]

rankings/{bossId}:
  [bracket,difficulty,page,phaseId,realm]
```

## Versioned evidence

```text
evidence/real-data/argentum-guild-progression-frontend-request-contract.json
```

Exact archived SPA payload SHA-256:

```text
da381a27e44be6cad3f60c4326251c7cbdd1ea8b31c5ccd5d8be03331855dacc
```

The review is offline-only, publishes no raw JavaScript/private source values, and performed no network request.

## Historical helper chain

Previous definition/reference/owner receipts remain audit history but are superseded for choosing the progression HTTP contract.

The former `POST /api/guilds/progression` assumption and former opaque owner-group relationships must not be used as current route evidence.

## Decision boundary

```text
legacy exact-prefix direct endpoint: false
bounded rankings GET contract observed: true
response semantics verified: false
pagination semantics verified: false
termination semantics verified: false
completeness verified: false
ready for full guild crawl: false
planner scoring allowed: false
```

The next progression stage is a single bounded validation of the observed rankings contract, followed by immutable response archiving and schema/pagination review before collection is expanded.
