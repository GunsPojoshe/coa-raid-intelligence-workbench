# Real-data evidence checkpoint

Updated: **2026-08-28**.

This directory contains **public-safe real receipts only**. Raw payloads, source rows, query values, dynamic keys, private IDs, HAR, browser state, API credentials and DuckDB stay local unless an explicit reviewed publication contract permits the exact field.

Receipts are evidence of a scoped real run, not permanent source configuration.

## Official public API receipts

```text
coa-public-api-catalog-real.json
coa-public-api-statistics-capture-real.json
coa-public-api-statistics-shape-real.json
coa-public-api-statistics-provenance-capture-real.json
coa-public-api-statistics-persistence-real.json
coa-public-api-statistics-profile-reanalysis-real.json
coa-public-api-population-coverage-real.json
```

Current scalar-safe facts:

```text
phase records: 3
active/current phase candidate: 1
boss records: 285
unique stable boss_id values: 285
/statistics: HTTP 200, archived
single-slice exact normalization: 21 class summaries / 62 spec records / 806 percentile values
profile-scoped aggregate dependency migration: proven
bounded population coverage: 4/4 slices complete
missing slices captured over network: 3
successful new captures: 3
deterministic second replays: 3
aggregate coverage rows: 60 class summaries / 162 spec records / 2106 percentile values
source_endpoint_profile dependencies: 4
legacy broad aggregate dependency: 0
pending reanalysis: 0
actionable source changes: 0
source health attention required: false
planner scoring allowed: false
```

No API key, query values, class/spec names, phase/difficulty/metric/role values, raw IDs/paths or metric/percentile scalar values are published.

## Report/Source Observatory receipts

The directory also retains the real E3 evidence chain, including current-report persistence/analytics, second-report generalization, cross-report structural review, scope-schema-cycle repair and the historical equivalence blocker.

Key retained status:

```text
two independent reports passed generic persistence/analytics
scope-aware schema repair superseded 623 invalid/legacy events
historical difficulty equivalence: insufficient_evidence
numeric historical cross-report scoring: blocked
```

## Historical guild/progression receipts

Older guild/progression/network receipts remain provenance/history. They do not override newer official API/source-priority rules or current browser/runtime evidence.

## Publication boundary

Public-safe receipts may contain:

```text
endpoint codes
route templates
static field names
types/scalar-free shapes
counts
booleans
review/algorithm versions
```

They must not contain:

```text
secrets/tokens/cookies
raw payloads/HAR
report/encounter/player/guild identities
query values
dynamic class/spec/group keys
private scope/profile values
private scalar hashes used as disguised identifiers
```
