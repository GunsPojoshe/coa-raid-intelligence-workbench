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

## Completed search-route phases

### Route and schema

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

Current classification:

```text
lexical route candidate observed: true
HTTP method verified: false
request shape verified: false
response schema verified: false
relation to guild report membership verified: false
pagination verified: false
termination verified: false
completeness verified: false
```

No network request may be designed from the route name alone.

## Offline usage-context inventory contract

The nearest bounded tool scans the exact archived SPA asset and performs no network requests.

```text
src/coa_workbench/collector/guild_progression_usage_inventory.py
scripts/inventory_guild_progression_usage.py
tests/unit/test_guild_progression_usage_inventory.py
```

Required bindings:

- versioned public profiled-recovery kind/version;
- 15/15 public recovery checks;
- exact private profiled-recovery SHA-256;
- exact recovered asset payload SHA-256;
- unique content manifest below `data/raw`;
- verified gzip payload and byte count;
- exact `/api/guilds/progression` occurrence inventory.

Privacy contract:

- raw JavaScript contexts are private;
- source guild ID and asset URL are private;
- public receipt publishes only counts, hashes, method/call-style candidates and booleans;
- no network request is performed;
- no route or pagination semantic is promoted.

Expected outputs:

```text
private:
  data/extracted/report-discovery/argentum-guild-progression-usage-context.private.json

public:
  data/exchange/out/argentum-guild-progression-usage-context.json
```

## Promotion sequence

```text
offline usage-context inventory
-> separate explicit usage-context review
-> bounded route probe only if method and request shape are unambiguous
-> response envelope/schema review
-> pagination field and successor behavior review
-> termination/completeness review
-> API-derived report set capture
-> set comparison against private 17-report baseline
-> explicit full-crawl promotion
```

A usage inventory does not itself authorize a route probe.

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
progression usage context reviewed: false
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
