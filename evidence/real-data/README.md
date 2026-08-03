# Real-data evidence checkpoint

Дата актуализации: **2026-08-03**.

Этот каталог содержит versioned scalar-free receipts и trust boundaries для real CoA Logs pipeline. Private payload contents, source scalar rows, private reviews/decisions and DuckDB remain local-only.

## Major versioned artifacts

```text
observed-combatants-info-candidate-extraction.json
observed-combatants-info-candidate-promotion.json
observed-combatants-info-persistence.json
argentum-report-pagination-limit-promotion.json
argentum-public-report-manifest.json
argentum-guild-identity-decision.json
argentum-guild-report-manifest.json
argentum-guild-full-crawl-contract.json
argentum-guild-route-semantics-capture.json
argentum-guild-route-semantics-review.json
```

Additional receipts document failed or incomplete bounded attempts. They remain classified evidence, not successful route-semantic or gameplay decisions.

## Combatants evidence chain

```text
exact candidate extraction
-> manual parser-only promotion
-> atomic immutable persistence through migration 0008
-> deterministic parser and actor/build read models
```

```text
persisted observations: 1343
actor/build observations: 1339
linked actors: 11
integrity checks: 14/14
core actor mutations: 0
```

This proves parser extraction and persistence reproducibility. It does not verify companion-addon provenance, gameplay meaning, canonical build projection or planner scoring.

## Public-report, identity and filtering baseline

```text
public reports: 6454
unique public report IDs: 6454
public-manifest integrity checks: 19/19
exact Argentum label reports: 17
identity-decision integrity checks: 16/16
guild identity verified: true
filtered reports: 17
unique filtered report IDs: 17
filter integrity checks: 14/14
```

The source guild ID, report IDs and source rows remain private.

## Full-crawl collection contract

```text
receipt: argentum-guild-full-crawl-contract.json
contract version: guild-full-crawl-contract-v1
source public reports: 6454
selected guild reports: 17
integrity checks: 12/12
full crawl collection contract reviewed: true
```

The private verified 17-report set is the comparison baseline. Missing, extra and conflicting reports must remain visible evidence.

## Bounded guild route-semantics capture

```text
receipt: argentum-guild-route-semantics-capture.json
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

Observed query cases:

```text
/api/guilds/search?q=<target>&limit=1
/api/guilds/search?q=<target>&limit=25
/api/guilds/search?q=<target>
```

## Reviewed guild route shape and response schema

```text
receipt: argentum-guild-route-semantics-review.json
review version: guild-route-semantics-review-v1
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

All three bounded cases returned the same single record. Therefore the review does not prove truncation, pagination, termination or completeness.

## Preserved decision boundaries

```text
guild route template verified: true
guild query shapes verified: true
guild response schema verified: true
limit parameter accepted: true
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

Route/schema review authorizes only a separate bounded multi-result probe for `limit` behavior. It does not authorize full crawl or scoring.

## Next evidence artifact

The next artifact must use a bounded query expected to return multiple guild records and compare at least two accepted limit values. It must preserve raw responses privately and publish only scalar-free counts, hashes, schemas and an explicit decision. A one-result response cannot verify limit truncation semantics.

## Local-only artifacts

```text
data/raw/
data/warehouse/
data/normalized/
data/reconstructed/
data/extracted/
data/exchange/in/
data/exchange/out/
```

Never commit credentials, cookies, tokens, Authorization headers, browser profiles, `.env`, unsanitized HAR, source guild IDs, report IDs or source-scalar private batches.
