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
argentum-guild-route-discovery-incomplete.json
argentum-guild-asset-profiled-recovery.json
argentum-guild-search-schema-inventory.json
argentum-guild-search-mapping-review.json
```

Additional receipts document failed or incomplete bounded attempts. They remain evidence of classified transport/access behavior, not proof of guild identity.

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

This proves exact parser extraction and persistence reproducibility. It does not verify companion-addon provenance, nested collection semantics, gameplay meaning, canonical build projection or planner scoring.

## Public-report manifest evidence chain

```text
pagination semantic review
-> terminal search
-> manual limit=25 promotion
-> promoted terminal search
-> checkpointed manifest capture with temporal-drift handling
-> scalar-free exhaustive manifest receipt
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

The current downstream binding for the public manifest receipt is:

```text
aaad2a9301bdb6a8e2af62a04fc74083a3d1fcd255c293b72dba3d4953b49e57
```

The receipt contains counts and hashes, not report rows or the raw guild ID.

## Snapshot identity evidence

```text
public manifest + exact private manifest
-> recompute 6454 report rows
-> isolate 17 Argentum rows
-> confirm one non-null source ID
-> confirm no conflicting non-empty name for that ID
-> scalar-free snapshot review
```

Receipt:

```text
argentum-guild-identity-snapshot-review.json
```

```text
exact label reports: 17
candidate source-ID reports: 17
conflicting non-empty names: 0
integrity checks: 10/10
snapshot internal identity consistent: true
ready for independent source identity review: true
```

This verifies consistency inside one captured snapshot only.

## Independent guild-search evidence

Profiled asset recovery established reviewed route candidates:

```text
asset bytes: 3881146
API route candidates: 79
guild route candidates: 3
```

Observed route shapes:

```text
/api/guilds/progression
/api/guilds/search?q=<value>
/api/guilds/search?q=<value>&limit=<value>
```

Guild-search access required the reviewed SPA fetch context. The captured response contains one guild object.

Schema inventory:

```text
guild objects: 1
field entries: 5
casefold label matches: 1
source ID matches: 1
integrity checks: 15/15
```

Reviewed mapping:

```text
$.guilds[].id           -> guild_id
$.guilds[].name         -> guild_name
$.guilds[].realm        -> realm
$.guilds[].report_count -> report_count
```

Mapping review:

```text
mapped fields: 4
search results: 1
source ID matches: 1
name casefold matches: 1
integrity checks: 13/13
cross-endpoint identity candidate observed: true
ready for guild identity decision review: true
```

The private evidence binds the same source ID across public-report and guild-search endpoints. Public receipts publish neither that ID nor the raw payload.

## Current decision boundary

Completed:

```text
exhaustive snapshot capture
snapshot-internal identity consistency
independent guild-search capture
schema inventory
field mapping review
cross-endpoint identity candidate
```

Not completed:

```text
explicit operator identity decision
guild identity verification
guild filtering
full guild crawl
character graph
performance model
BiS 25 scoring
planner scoring
```

The explicit decision implementation requires `--promote-identity`. A successful scalar-free output is expected at:

```text
data/exchange/out/argentum-guild-identity-decision.json
```

The next versioned artifact must be:

```text
evidence/real-data/argentum-guild-identity-decision.json
```

It may be added only after verifying all evidence bindings, integrity checks, explicit promotion, scalar-free content and preservation of all crawl/performance/scoring gates.

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