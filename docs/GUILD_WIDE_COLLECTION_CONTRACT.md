# Guild-wide report collection contract

## Goal

Prepare a reproducible Argentum corpus for a future explainable `BiS 25` roster calculation.

```text
guild label: Argentum
candidate characters: 30-40
final roster: 25
```

This document defines collection and trust boundaries, not a scoring policy.

## Verified foundation

```text
public reports: 6454
verified private Argentum baseline: 17 reports
guild identity verified: true
guild filtering completed: true
full-crawl collection contract reviewed: true
```

The source guild ID and report IDs remain private.

## Completed guild-search phases

### Route and response schema

```text
route: /api/guilds/search
response envelope: guilds, success
guild fields: id, name, realm, report_count
route review checks: 22/22
```

### Multi-result limit semantics

```text
capture result counts: 1 / 7 / 7
capture checks: 15/15
review checks: 30/30
limit truncation semantics verified: true
```

These phases prove stable truncation of guild-search results only. They do not identify or verify the route used to retrieve one guild's report corpus.

## Progression route evidence chain

Recovered SPA asset evidence contains:

```text
/api/guilds/progression
```

### Usage-context checkpoint

```text
inventory: evidence/real-data/argentum-guild-progression-usage-context.json
inventory SHA-256: e19cc1a72175bd838b151b8438861af1aece14ba2a30f94da8f6989ce7be3d59
inventory checks: 23/23
review: evidence/real-data/argentum-guild-progression-usage-review.json
review SHA-256: 063abc51579e3942c4b33766fa9d1f9ba336a921a78bc15a5849971025a77198
review checks: 30/30
classification: literal_reference
bounded route probe ready: false
```

This phase observed only a lexical route reference and authorized a separate offline helper/call-site inventory.

### Helper/call-site checkpoint

```text
inventory: evidence/real-data/argentum-guild-progression-callsite.json
inventory SHA-256: ad8a5addf9ac9dd566284e0bc395ac40100986d0f14f0a49e9519a6aef28d351
inventory checks: 32/32
review: evidence/real-data/argentum-guild-progression-callsite-review.json
review SHA-256: d79302d755eab918ce3f85a9ad39e78231720391c8f0692925fe2e79b6adc60f
review checks: 36/36
call class: generic_helper_call
method candidate: POST
method candidate unambiguous: true
helper identity resolved: false
request payload mapping resolved: false
bounded route probe ready: false
```

The observed structural envelope is too broad for request-contract promotion:

```text
call/envelope characters: 2479207
function characters: 2411715
reviewable threshold: 65536
```

Current blockers:

```text
generic_helper_identity_unresolved
structural_envelope_overbroad
request_payload_mapping_unresolved
```

`POST` is an evidence-backed method candidate, not a verified route contract. No network request may be designed until the helper identity and exact request shape are independently reviewed.

## Privacy and evidence contract

The offline tools:

- read only local private recovery and the immutable raw archive;
- verify exact source document and archived payload hashes;
- perform no network requests;
- keep raw JavaScript context and raw callee private;
- publish only scalar-free hashes, bounded counts and classifications;
- preserve route, pagination, termination, completeness, full-crawl and scoring gates as false.

Deterministic source document hashes use canonical LF bytes so Linux and Windows checkouts produce the same review receipt.

## Promotion sequence

```text
offline helper-definition inventory from the exact archived SPA asset
-> bind definition/call-chain candidates to the published callee hash
-> scalar-free helper-definition receipt
-> separate explicit helper-definition review
-> bounded route probe only if helper identity and exact method/request shape are verified
-> response envelope/schema review
-> pagination field and successor behavior review
-> termination/completeness review
-> API-derived report set capture
-> set comparison against private 17-report baseline
-> explicit full-crawl promotion
```

An unambiguous method candidate alone does not authorize a route probe.

## Set-comparison contract

Any future API-derived report set must be partitioned into:

```text
matching_reports
missing_from_guild_api
extra_in_guild_api
conflicting_report_records
```

Rules:

- deduplicate by private source report ID;
- preserve contradicting evidence;
- keep IDs private;
- do not mark partial results complete;
- preserve failed requests as observations;
- require exact contract/checkpoint binding for resume;
- keep retries bounded.

## Current boundary

```text
guild identity verified: true
guild filtering completed: true
full crawl collection contract reviewed: true
guild-search route/schema verified: true
guild-search limit truncation verified: true
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
progression route semantics verified: false
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

Planner scoring remains disabled.
