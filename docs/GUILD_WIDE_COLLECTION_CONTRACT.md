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

## Progression route candidate

Recovered SPA asset evidence contains:

```text
/api/guilds/progression
```

The versioned offline inventory and explicit review are:

```text
evidence/real-data/argentum-guild-progression-usage-context.json
evidence/real-data/argentum-guild-progression-usage-review.json
```

Evidence checkpoint:

```text
inventory SHA-256: e19cc1a72175bd838b151b8438861af1aece14ba2a30f94da8f6989ce7be3d59
inventory checks: 23/23
review SHA-256: 063abc51579e3942c4b33766fa9d1f9ba336a921a78bc15a5849971025a77198
review checks: 30/30
route occurrences: 1
call styles: literal_reference
HTTP method candidates: []
actual invocation observed: false
bounded route probe ready: false
```

The sole lexical route reference does not prove a call site, HTTP method or request shape.

## Privacy and evidence contract

The inventory:

- reads only local private recovery and the immutable raw archive;
- verifies the exact private recovery and archived asset payload hashes;
- performs no network requests;
- keeps raw JavaScript context private;
- publishes only scalar-free context hashes and classifications.

The explicit review may mark the usage context as reviewed, but it must not infer an HTTP method from a literal string reference.

Current blockers:

```text
http_method_unresolved
literal_reference_without_call_site
invocation_shape_unresolved
```

No network request may be designed from the route name alone.

## Promotion sequence

```text
offline helper/call-site recovery from the archived SPA asset
-> scalar-free helper/call-site inventory
-> separate explicit helper/call-site review
-> bounded route probe only if exact method and request shape become unambiguous
-> response envelope/schema review
-> pagination field and successor behavior review
-> termination/completeness review
-> API-derived report set capture
-> set comparison against private 17-report baseline
-> explicit full-crawl promotion
```

A lexical usage inventory or blocked review does not authorize a route probe.

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
progression usage context observed: true
progression usage context reviewed: true
progression HTTP method resolved: false
progression request shape verified: false
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
