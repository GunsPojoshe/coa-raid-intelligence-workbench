# Real-data evidence checkpoint

Дата актуализации: **2026-08-04**.

Каталог содержит versioned scalar-free receipts и explicit trust boundaries. Private payloads, source rows, queries, raw JavaScript contexts, private receipts and DuckDB remain local-only.

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
argentum-guild-asset-profiled-recovery.json
argentum-guild-route-semantics-capture.json
argentum-guild-route-semantics-review.json
argentum-guild-limit-semantics-capture.json
argentum-guild-limit-semantics-review.json
argentum-guild-progression-usage-context.json
argentum-guild-progression-usage-review.json
```

Incomplete or failed receipts remain evidence of an attempt, not a successful semantic promotion.

## Identity and filtering baseline

```text
public reports: 6454
unique report IDs: 6454
public-manifest checks: 19/19
exact Argentum label reports: 17
identity-decision checks: 16/16
guild identity verified: true
filtered reports: 17
filter checks: 14/14
```

Private 17-report set is the future completeness comparison baseline. Source guild ID and report IDs are not published.

## Guild-search route and limit evidence

```text
route: /api/guilds/search
response envelope: guilds, success
guild fields: id, name, realm, report_count
route review checks: 22/22
limit result counts: 1 / 7 / 7
limit capture checks: 15/15
limit review checks: 30/30
limit truncation semantics verified: true
```

This verifies stable truncation of guild-search results. It does not verify guild-report pagination or full-crawl completeness.

## Progression usage-context inventory

```text
receipt: argentum-guild-progression-usage-context.json
SHA-256: e19cc1a72175bd838b151b8438861af1aece14ba2a30f94da8f6989ce7be3d59
inventory version: guild-progression-usage-context-inventory-v1
integrity checks: 23/23
network requests performed: false
raw archive only: true
occurrences: 1
call styles: literal_reference
method candidates: []
method unambiguous: false
```

The public inventory contains hashes and classification only. Raw JavaScript context remains local in the private inventory.

## Explicit progression usage review

```text
receipt: argentum-guild-progression-usage-review.json
SHA-256: 063abc51579e3942c4b33766fa9d1f9ba336a921a78bc15a5849971025a77198
review version: guild-progression-usage-context-review-v1
integrity checks: 30/30
usage context reviewed: true
actual invocation observed: false
method resolved: false
ready for bounded route probe: false
```

Blocked because the SPA evidence contains only a literal route reference:

```text
http_method_unresolved
literal_reference_without_call_site
invocation_shape_unresolved
```

No HTTP method, request shape, response schema, pagination, termination or completeness semantics were promoted.

## Current decision boundary

```text
progression route candidate observed: true
progression usage context reviewed: true
progression method resolved: false
ready for bounded progression route probe: false
guild API route semantics verified: false
pagination semantics verified: false
termination semantics verified: false
completeness verified: false
automatic full guild crawl allowed: false
ready for full guild crawl: false
planner scoring allowed: false
```

## Next evidence sequence

```text
offline helper/call-site recovery from archived SPA asset
-> scalar-free helper inventory
-> explicit helper/call-site review
-> bounded network probe only after exact method/request resolution
-> response schema review
-> pagination/termination/completeness evidence
-> API-versus-private-baseline set comparison
-> explicit full-crawl promotion
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

Never commit credentials, cookies, tokens, Authorization headers, browser profiles, `.env`, unsanitized HAR, source guild IDs, report IDs, private query values, private recovery receipts or raw JavaScript contexts.
