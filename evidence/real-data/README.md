# Real-data evidence checkpoint

Дата актуализации: **2026-08-04**.

Каталог содержит versioned scalar-free receipts и explicit trust boundaries. Private payloads, source rows, queries, raw JavaScript contexts, raw callees, private receipts and DuckDB remain local-only.

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
argentum-guild-progression-callsite.json
argentum-guild-progression-callsite-review.json
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

## Progression usage-context evidence

```text
inventory: argentum-guild-progression-usage-context.json
inventory SHA-256: e19cc1a72175bd838b151b8438861af1aece14ba2a30f94da8f6989ce7be3d59
inventory checks: 23/23
review: argentum-guild-progression-usage-review.json
review SHA-256: 063abc51579e3942c4b33766fa9d1f9ba336a921a78bc15a5849971025a77198
review checks: 30/30
network requests: 0
route occurrences: 1
classification: literal_reference
ready for bounded route probe: false
```

The public inventory contains hashes and classification only. Raw JavaScript context remains local.

## Progression helper/call-site inventory

```text
receipt: argentum-guild-progression-callsite.json
SHA-256: ad8a5addf9ac9dd566284e0bc395ac40100986d0f14f0a49e9519a6aef28d351
inventory version: guild-progression-helper-callsite-inventory-v1
integrity checks: 32/32
network requests: 0
route occurrences: 1
call candidates: 1
direct invocation candidates: 1
call class: generic_helper_call
method candidate: POST
method evidence: method_property_literal
method unambiguous: true
```

The receipt publishes hashes, bounded counts and classifications only. Raw context, raw callee, source IDs and scalar source values remain local.

The observed generic-helper structural envelope is overbroad:

```text
call/envelope characters: 2479207
function characters: 2411715
reviewable threshold: 65536
```

## Explicit helper/call-site review

```text
receipt: argentum-guild-progression-callsite-review.json
SHA-256: d79302d755eab918ce3f85a9ad39e78231720391c8f0692925fe2e79b6adc60f
review version: guild-progression-helper-callsite-review-v1
integrity checks: 36/36
helper/call-site reviewed: true
HTTP method candidate: POST
helper identity resolved: false
request payload mapping resolved: false
ready for helper-definition inventory: true
ready for bounded route probe: false
```

Blocked by:

```text
generic_helper_identity_unresolved
structural_envelope_overbroad
request_payload_mapping_unresolved
```

The review accepts `POST` only as the method candidate observed inside the generic helper call. It does not verify helper identity, request payload mapping, response schema, pagination, termination or completeness.

## Current decision boundary

```text
progression route candidate observed: true
progression usage context reviewed: true
progression helper/call-site inventory observed: true
progression helper/call-site reviewed: true
progression HTTP method candidate: POST
progression method candidate unambiguous: true
progression helper identity resolved: false
progression request payload mapping resolved: false
progression request shape verified: false
ready for helper-definition inventory: true
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
offline helper-definition inventory from the exact archived SPA asset
-> scalar-free definition/call-chain receipt
-> explicit helper-definition review
-> bounded network probe only after helper identity and exact request contract are verified
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

Never commit credentials, cookies, tokens, Authorization headers, browser profiles, `.env`, unsanitized HAR, source guild IDs, report IDs, private query values, private recovery receipts, raw JavaScript contexts or raw callees.
