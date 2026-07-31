# Real-data evidence checkpoint

Дата актуализации: **2026-07-31**.

Этот каталог содержит versioned scalar-free receipts и trust boundaries для real CoA Logs pipeline. Private payload contents, source scalar rows, private reviews/decisions and DuckDB remain local-only.

## Major versioned artifacts

```text
observed-combatants-info-candidate-extraction.json
observed-combatants-info-candidate-promotion.json
observed-combatants-info-persistence.json
argentum-report-pagination-limit-promotion.json
argentum-public-report-manifest.json
argentum-guild-identity-snapshot-review.json
argentum-guild-asset-profiled-recovery.json
argentum-guild-search-schema-inventory.json
argentum-guild-search-mapping-review.json
argentum-guild-identity-decision.json
```

Additional receipts document failed or incomplete bounded attempts. They remain classified evidence, not successful identity or route-semantic decisions.

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
contains source scalar values: false
```

This proves parser extraction and persistence reproducibility. It does not verify companion-addon provenance, gameplay meaning, canonical build projection or planner scoring.

## Public-report manifest evidence chain

```text
pagination semantic review
-> terminal search
-> manual limit=25 promotion
-> checkpointed exhaustive manifest capture
-> scalar-free public manifest receipt
```

```text
route: /api/reports/public
limit: 25
pages: 259
reports: 6454
unique report IDs: 6454
duplicates: 0
terminal page reports: 4
integrity checks: 19/19
sentinel stability: verified
exact Argentum label reports: 17
distinct non-null guild IDs for exact label: 1
```

The receipt contains counts and hashes, not report rows or the raw guild ID.

## Guild identity evidence chain

```text
exhaustive public/private manifest
-> scalar-free snapshot consistency review
-> profiled asset recovery and route candidates
-> independent guild-search capture
-> scalar-free schema inventory
-> reviewed four-field mapping
-> cross-endpoint source-ID and name comparison
-> explicit operator promotion
-> scalar-free identity decision
```

Identity decision receipt:

```text
argentum-guild-identity-decision.json
```

Verified facts:

```text
decision kind: guild_identity_decision
decision version: guild-identity-decision-v1
snapshot reports: 6454
exact target-label reports: 17
distinct target guild IDs: 1
conflicting names: 0
guild-search results: 1
mapped fields: 4
cross-endpoint source-ID equality: true
name casefold equality: true
explicit operator promotion: true
integrity checks: 16/16
contains raw payload: false
contains source scalar values: false
independent source identity verified: true
guild identity verified: true
ready for guild filtering: true
```

The source guild ID and private decision packet remain local-only.

## Preserved decision boundaries

Identity verification does not verify guild API route semantics and does not authorize collection or scoring beyond deterministic filtering.

```text
guild API route semantics verified: false
ready for full guild crawl: false
ready for multi-report character graph: false
ready for performance model: false
ready for BiS 25 scoring: false
planner scoring allowed: false
```

## Next evidence artifact

Deterministic verified-ID filtering is implemented in:

```text
src/coa_workbench/collector/verified_guild_report_filter.py
scripts/filter_verified_guild_reports.py
```

The next local execution should produce:

```text
private:
  data/extracted/report-discovery/argentum-guild-report-manifest.private.json

scalar-free receipt:
  data/exchange/out/argentum-guild-report-manifest.json
```

Only the scalar-free receipt may be reviewed for versioning. Filtering must use the verified source guild ID from the private identity decision, not name matching.

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

They may contain report IDs, guild IDs/names, character names, talents, gear, GUIDs, normalized entities, private review packets or DuckDB state.

Never commit credentials, cookies, tokens, Authorization headers, browser profiles, `.env`, unsanitized HAR or source-scalar private batches.
