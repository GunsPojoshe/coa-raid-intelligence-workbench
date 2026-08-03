# Real-data evidence checkpoint

Дата актуализации: **2026-08-04**.

Этот каталог содержит versioned scalar-free receipts и trust boundaries для real CoA Logs pipeline. Private payload contents, source scalar rows, private queries, private reviews/decisions and DuckDB remain local-only.

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
argentum-guild-limit-semantics-capture.json
argentum-guild-limit-semantics-review.json
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

## Reviewed guild route and response schema

```text
capture: argentum-guild-route-semantics-capture.json
review: argentum-guild-route-semantics-review.json
route: /api/guilds/search
route review integrity checks: 22/22
response envelope: guilds, success
guild fields: id, name, realm, report_count
limit parameter accepted: true
```

The route/schema checkpoint verified the request shape and response schema. Its single-result evidence did not verify limit truncation, pagination, termination or completeness.

## Bounded multi-result limit capture

```text
receipt: argentum-guild-limit-semantics-capture.json
capture version: guild-limit-semantics-capture-v1
capture SHA-256: 690d7d93d5e9c592877a4fa049d2638b0a5a523430f9205777ce4fa06e624e58
attempts: 3
completed attempts: 3
HTTP 200 responses: 3
observed result counts: [1, 7]
integrity checks: 15/15
ready for limit-semantics review: true
```

Observed bounded cases:

```text
private query + limit 1
private query + limit 25
same private query + repeated limit 25
```

Verified capture relations:

```text
low limit saturated: true
multi-result response observed: true
high limit respected: true
high-limit repeat stable: true
source-ID order stable by hash: true
low result is exact high-result prefix by ID hash: true
response schema consistent: true
```

The capture itself preserves `limit_truncation_semantics_verified=false` and only authorizes a separate review.

## Explicit limit-semantics review

```text
receipt: argentum-guild-limit-semantics-review.json
review version: guild-limit-semantics-review-v1
integrity checks: 30/30
source capture hash bound: true
source route-review hash bound across LF/CRLF: true
limit truncation semantics verified: true
ready for bounded pagination-semantics capture: true
```

The public review contains no query value, request URL, source guild ID, raw record or raw payload.

## Current decision boundary

```text
guild route template verified: true
guild query shapes verified: true
guild response schema verified: true
limit parameter accepted: true
limit truncation semantics verified: true
ready for bounded pagination-semantics capture: true
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

## Next evidence sequence

```text
bounded pagination-semantics capture
-> explicit pagination review
-> termination/completeness evidence and review
-> API-versus-private-baseline set comparison
-> explicit full-crawl promotion only if every gate passes
```

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

Never commit credentials, cookies, tokens, Authorization headers, browser profiles, `.env`, unsanitized HAR, source guild IDs, report IDs, private query values or source-scalar private batches.
