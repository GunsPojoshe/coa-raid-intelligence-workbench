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
argentum-guild-full-crawl-contract.json
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

## Public-report manifest

```text
receipt: argentum-public-report-manifest.json
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

## Guild identity decision

```text
receipt: argentum-guild-identity-decision.json
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
guild identity verified: true
ready for guild filtering: true
```

The source guild ID and private decision packet remain local-only.

## Verified guild report manifest

```text
receipt: argentum-guild-report-manifest.json
manifest version: verified-guild-report-manifest-v1
source reports: 6454
selected reports: 17
unique selected report IDs: 17
duplicate selected occurrences: 0
integrity checks: 14/14
guild filtering completed: true
guild report manifest deduplicated: true
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

## Full-crawl collection contract

```text
receipt: argentum-guild-full-crawl-contract.json
contract version: guild-full-crawl-contract-v1
source public reports: 6454
selected guild reports: 17
integrity checks: 12/12
full crawl collection contract reviewed: true
ready for bounded route-semantics capture: true
guild API route semantics verified: false
automatic full guild crawl allowed: false
ready for full guild crawl: false
planner scoring allowed: false
```

The contract is bound to the public manifest, identity decision and verified guild report manifest. It defines the 17-report set as the baseline for future API comparison.

Required future comparison partitions:

```text
matching_reports
missing_from_guild_api
extra_in_guild_api
conflicting_report_records
```

The contract requires immutable raw capture, exact payload SHA-256, schema fingerprint, reviewed field contracts, pagination/termination/completeness proof, discrepancy preservation and explicit route-semantic promotion.

## Preserved decision boundaries

```text
full crawl collection contract reviewed: true
ready for bounded route-semantics capture: true
guild API route semantics verified: false
automatic full guild crawl allowed: false
ready for full guild crawl: false
ready for multi-report character graph: false
ready for performance model: false
ready for BiS 25 scoring: false
planner scoring allowed: false
```

Identity verification, filtering and contract review do not verify gameplay semantics or authorize full crawl/scoring.

## Next evidence artifact

The next artifact must capture and review exact guild API route semantics under the contract. It must record exact route/query parameters, raw payload hash, schema fingerprint, collection shape, pagination fields, termination/completeness evidence and a scalar-free decision. No full crawl may begin before that decision.

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

Never commit credentials, cookies, tokens, Authorization headers, browser profiles, `.env`, unsanitized HAR, source guild IDs, report IDs or source-scalar private batches.