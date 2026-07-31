# Real-data evidence checkpoint

Дата актуализации: **2026-07-31**.

Этот каталог содержит versioned scalar-free receipts и trust boundaries для real CoA Logs pipeline. Private payload contents, source scalar rows and DuckDB remain local-only.

## Versioned artifacts

```text
observed-combatants-info-candidate-extraction.json
observed-combatants-info-candidate-promotion.json
observed-combatants-info-persistence.json
argentum-report-pagination-limit-promotion.json
argentum-public-report-manifest.json
```

## Combatants evidence chain

```text
exact candidate extraction
-> manual parser-only promotion
-> atomic immutable persistence through migration 0008
-> deterministic parser and actor/build read models
```

Persistence receipt facts:

```text
persisted observations: 1343
actor/build observations: 1339
linked actors: 11
persistence runs: 1
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
-> concurrent checkpointed manifest capture
-> scalar-free exhaustive manifest receipt
```

Manifest receipt:

```text
argentum-public-report-manifest.json
receipt SHA-256: ed2c8884ce8d9a96b26d25eea269f71a85aadd34c5e2a6f42362dbd41be19796
```

Verified facts:

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
```

Guild-field summary:

```text
reports with both guild fields: 1171
distinct guild identity pairs: 88
exact Argentum label reports: 17
distinct non-null guild IDs for exact label: 1
```

Decision boundary:

```text
exhaustive captured snapshot: true
guild identity verified: false
ready for guild identity review: true
ready for guild filtering: false
ready for full guild crawl: false
planner scoring allowed: false
```

The receipt contains counts and hashes, not report rows or the raw guild ID.

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

They may contain report IDs, guild IDs/names, character names, talents, gear, GUIDs, normalized entities or DuckDB state.

Never commit credentials, cookies, tokens, Authorization headers, browser profiles, `.env`, unsanitized HAR or source-scalar private batches.

## Next evidence artifact

The next versioned artifact should be a scalar-free guild-identity review receipt bound to the exact private manifest SHA-256.

It must include:

- source manifest receipt name and SHA-256;
- private manifest name and verified SHA-256;
- exact target-label match count;
- distinct non-null guild-ID count;
- same-ID alternate-name conflict count;
- independent source evidence hashes or an explicit absence statement;
- reviewer metadata;
- decision (`verified_target_identity`, `insufficient_evidence`, `conflicting_evidence` or `rejected_identity`);
- no raw guild ID or other source scalar values;
- guild filtering and scoring boundaries.
