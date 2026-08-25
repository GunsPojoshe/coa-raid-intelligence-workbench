# Real-data evidence checkpoint

Updated: **2026-08-26**.

This directory contains **public-safe real receipts only**. Raw payloads, source rows, query values, dynamic keys, private IDs, HAR, browser state, API credentials and DuckDB stay local unless an explicit reviewed publication contract permits the exact field.

Receipts are evidence of a scoped real run, not permanent source configuration.

## Official public API receipts

```text
coa-public-api-catalog-real.json
coa-public-api-statistics-capture-real.json
coa-public-api-statistics-shape-real.json
```

Current scalar-safe facts:

```text
phase records: 3
active/current phase candidate: 1
boss records: 285
unique stable boss_id values: 285
/statistics: HTTP 200, archived
statistics top-level entries: 21
statistics max depth: 5
objects with documented metric fields: 83
statistics_normalization_ready: true
```

No API key, query values, class/spec names, difficulty values, metric values or percentile scalar values are published.

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
