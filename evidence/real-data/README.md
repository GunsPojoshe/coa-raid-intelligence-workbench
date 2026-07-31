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
argentum-guild-report-manifest.json
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

```text
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

## Verified guild report manifest evidence chain

```text
verified public manifest
+ verified public identity decision
+ exact private manifest
+ exact private identity decision
-> load verified source guild ID privately
-> exact typed source-ID filtering
-> report-ID deduplication
-> source-order preservation
-> private guild report manifest
-> scalar-free public receipt
```

Receipt:

```text
argentum-guild-report-manifest.json
```

Verified facts:

```text
manifest kind: verified_guild_report_manifest
manifest version: verified-guild-report-manifest-v1
source reports: 6454
selected reports: 17
unique selected report IDs: 17
duplicate selected occurrences: 0
integrity checks: 14/14
guild filtering completed: true
guild report manifest deduplicated: true
contains raw payload: false
contains source scalar values: false
report IDs published: false
source guild ID published: false
```

Selection contract:

```text
filter field: /reports/*/guild_id
filter operation: equals_verified_private_source_guild_id
deduplication key: /reports/*/id
selection order: source_manifest_order
```

The exact selected report IDs and records remain local-only.

## Preserved decision boundaries

Identity verification and filtering do not verify guild API route semantics and do not authorize full crawl, graph construction, performance modeling or scoring.

```text
full crawl collection contract reviewed: false
guild API route semantics verified: false
ready for full guild crawl: false
ready for multi-report character graph: false
ready for performance model: false
ready for BiS 25 scoring: false
planner scoring allowed: false
```

## Next evidence artifact

The next artifact must review the full-crawl collection contract against all three receipts:

```text
argentum-public-report-manifest.json
argentum-guild-identity-decision.json
argentum-guild-report-manifest.json
```

It must define:

- the verified 17-report set as the current baseline;
- exact guild API route-semantic evidence requirements;
- pagination, termination and completeness requirements;
- immutable raw capture and exact hash/fingerprint bindings;
- deterministic API-versus-baseline set comparison;
- missing/extra/conflicting report preservation;
- partial-failure and resume behavior;
- explicit promotion before automatic full crawl;
- scalar-free publication boundaries.

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

Never commit credentials, cookies, tokens, Authorization headers, browser profiles, `.env`, unsanitized HAR, source guild IDs, report IDs or source-scalar private batches.