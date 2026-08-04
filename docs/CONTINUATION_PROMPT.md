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
3. Inspect the latest `Verify repository` run and all jobs for the exact current HEAD.
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
6. Use the GitHub connector for repository operations.
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

## Guild-search checkpoint

```text
route: /api/guilds/search
response keys: guilds, success
guild fields: id, name, realm, report_count
route review checks: 22/22
limit result counts: 1 / 7 / 7
limit capture checks: 15/15
limit review checks: 30/30
limit truncation semantics verified: true
```

This verifies search-list truncation only. It does not verify guild-report pagination.

## Progression usage-context checkpoint

Versioned inventory:

```text
evidence/real-data/argentum-guild-progression-usage-context.json
SHA-256: e19cc1a72175bd838b151b8438861af1aece14ba2a30f94da8f6989ce7be3d59
inventory checks: 23/23
network requests: 0
route occurrences: 1
call styles: literal_reference
HTTP method candidates: []
method unambiguous: false
```

Versioned review:

```text
evidence/real-data/argentum-guild-progression-usage-review.json
SHA-256: 063abc51579e3942c4b33766fa9d1f9ba336a921a78bc15a5849971025a77198
review checks: 30/30
usage context reviewed: true
actual invocation observed: false
ready for bounded route probe: false
```

Blockers:

```text
http_method_unresolved
literal_reference_without_call_site
invocation_shape_unresolved
```

The literal route string does not prove the HTTP method, caller/helper or request shape. Do not perform a guessed network request.

Implementation:

```text
src/coa_workbench/collector/guild_progression_usage_inventory.py
scripts/inventory_guild_progression_usage.py
src/coa_workbench/collector/guild_progression_usage_review.py
scripts/review_guild_progression_usage.py
tests/unit/test_guild_progression_usage_inventory.py
tests/unit/test_guild_progression_usage_review.py
tests/unit/test_versioned_guild_progression_usage_review.py
```

## Last confirmed code checkpoint

At the time this prompt was updated, the implementation HEAD before documentation updates was:

```text
HEAD: 683f76d83caa62724abedeb521d3cd95d9433989
Verify repository run: #562
public-release-audit: success
Ubuntu: success
Windows: success
pytest: 341 passed, 1 warning
Doctor: success
DuckDB clean/repeated initialization: success
migrations: 0001–0008
```

Recheck live. Do not transfer this result to a later documentation HEAD.

## Current exact boundary

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

## Required next sequence

```text
offline helper/call-site recovery from the exact archived SPA asset
-> scalar-free helper/call-site inventory
-> explicit helper/call-site review
-> bounded progression route probe only if exact method and request shape become unambiguous
-> response schema review
-> pagination/termination/completeness review
-> API-versus-private-baseline set comparison
-> explicit full-crawl promotion
```

No false gate may be raised by inference. Never version private recovery, private usage inventory, raw JavaScript contexts, source IDs, credentials or raw archive contents.
