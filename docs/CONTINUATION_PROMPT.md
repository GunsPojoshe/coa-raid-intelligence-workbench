# Continuation prompt — CoA Raid Intelligence Workbench

Continue development of:

```text
repository: GunsPojoshe/coa-raid-intelligence-workbench
branch: e3/real-log-capture
Draft PR #7: e3/real-log-capture -> e2/log-evidence-refactor
parent Draft PR #3: e2/log-evidence-refactor -> main
```

Work evidence-first. Never trust stale HEAD, CI, hashes, counts, routes or readiness. Verify live before changes.

## Mandatory start

1. Verify PR #7 state, draft status, mergeability, base/head and current SHA.
2. Verify PR #3 and target branch relation.
3. Inspect current `Verify repository` run and all jobs.
4. Read:
   - `AGENTS.md`;
   - `docs/PROJECT_MASTER_CONTEXT.md`;
   - `docs/PROJECT_STATE.md`;
   - `docs/CONTINUATION_PROMPT.md`;
   - `docs/REAL_LOG_CAPTURE.md`;
   - `docs/GUILD_WIDE_COLLECTION_CONTRACT.md`;
   - `docs/ADR_012_LOG_EVIDENCE_TRUTH_MODEL.md`;
   - `evidence/real-data/README.md`.
5. Compare documentation with code, migrations and versioned receipts.
6. Use GitHub connector for repository operations.
7. For local Windows-only evidence actions, provide one complete PowerShell block.

## Core truth model

```text
source response
-> immutable raw archive
-> exact payload hash and schema fingerprint
-> reviewed mapping/extractor
-> deterministic normalization/reconstruction
-> immutable persistence/read models
-> supporting and contradicting evidence
-> explicit trust decision
-> planner scoring only for corroborated/confirmed mechanics
```

```text
combat-log observation != automatic gameplay mechanic proof
```

## Verified baseline

```text
public reports: 6454
unique public report IDs: 6454
exact Argentum label reports: 17
guild identity verified: true
private selected baseline: 17 unique reports
full-crawl collection contract reviewed: true
migrations: 0001–0008
```

Private source guild ID, report IDs and source rows are not versioned.

## Guild-search route checkpoint

```text
route: /api/guilds/search
response keys: guilds, success
guild fields: id, name, realm, report_count
route review checks: 22/22
```

Multi-result limit evidence:

```text
capture: evidence/real-data/argentum-guild-limit-semantics-capture.json
capture SHA-256: 690d7d93d5e9c592877a4fa049d2638b0a5a523430f9205777ce4fa06e624e58
result counts: 1 / 7 / 7
capture checks: 15/15
review checks: 30/30
limit truncation semantics verified: true
```

This verifies search-list truncation only. It does not verify guild-report pagination.

## Last confirmed green checkpoint

At the time this prompt was updated:

```text
HEAD: 6a6a28aaf5a8cf6e4d9240e19b714073a0096282
Verify repository run: #551
public-release-audit: success
Ubuntu: success
Windows: success
pytest: 335 passed, 1 warning
Doctor: success
DuckDB clean/repeated initialization: success
```

Recheck live. Do not transfer this result to a later HEAD.

## Recovered SPA asset evidence

Versioned receipt:

```text
evidence/real-data/argentum-guild-asset-profiled-recovery.json
```

Facts:

```text
asset download completed: true
HTTP 200: true
asset bytes: 3881146
integrity checks: 15/15
all API route candidates: 79
guild route candidates: 3
```

Guild route shapes:

```text
/api/guilds/progression
/api/guilds/search?q=<value>
/api/guilds/search?q=<value>&limit=<value>
```

Search routes are reviewed. `/api/guilds/progression` is only a lexical candidate. Method, request shape, response schema and connection to report membership are not verified.

## Current implemented nearest tool

```text
src/coa_workbench/collector/guild_progression_usage_inventory.py
scripts/inventory_guild_progression_usage.py
tests/unit/test_guild_progression_usage_inventory.py
```

Purpose:

- work only from local private profiled recovery and `data/raw`;
- verify exact private receipt and archived asset payload hashes;
- find every bounded usage of `/api/guilds/progression`;
- keep raw JavaScript context private;
- publish scalar-free context hashes, call-style/method candidates and query-construction markers;
- perform no network requests;
- promote no route/pagination/full-crawl semantics.

Default local inputs:

```text
public recovery:
  evidence/real-data/argentum-guild-asset-profiled-recovery.json

private recovery:
  data/extracted/report-discovery/argentum-guild-asset-profiled-recovery.private.json

raw archive:
  data/raw
```

Default outputs:

```text
private:
  data/extracted/report-discovery/argentum-guild-progression-usage-context.private.json

public:
  data/exchange/out/argentum-guild-progression-usage-context.json
```

Only the public output may be uploaded/versioned. Never upload private recovery, private inventory, raw archive, asset URL, source IDs or raw JavaScript context.

## Acceptance of future public usage receipt

Validate:

- schema/kind/version;
- exact public/private recovery bindings;
- unique raw content manifest;
- asset payload hash and byte count;
- bounded occurrence count;
- context hashes present;
- method/call-style/query markers are scalar-free;
- no raw context, asset URL, guild ID or source values;
- all integrity checks true;
- all network/route/pagination/full-crawl gates false.

A successful inventory may set only:

```text
ready_for_guild_progression_usage_review: true
```

## Current exact boundary

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

## Required next sequence

```text
local offline usage-context inventory
-> validate/version scalar-free public receipt
-> implement separate deterministic usage-context review
-> bounded route probe only if method/request shape become unambiguous
-> response schema review
-> pagination/termination/completeness review
-> API-versus-private-baseline set comparison
-> explicit full-crawl promotion
```

No false gate may be raised by inference.
