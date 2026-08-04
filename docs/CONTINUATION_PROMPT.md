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

```text
inventory: evidence/real-data/argentum-guild-progression-usage-context.json
inventory SHA-256: e19cc1a72175bd838b151b8438861af1aece14ba2a30f94da8f6989ce7be3d59
inventory checks: 23/23
review: evidence/real-data/argentum-guild-progression-usage-review.json
review SHA-256: 063abc51579e3942c4b33766fa9d1f9ba336a921a78bc15a5849971025a77198
review checks: 30/30
network requests: 0
route occurrences: 1
classification: literal_reference
ready for bounded route probe: false
```

The literal route reference did not prove a caller, helper, HTTP method or request shape. It authorized only the separate offline helper/call-site inventory.

## Progression helper/call-site checkpoint

Versioned inventory:

```text
evidence/real-data/argentum-guild-progression-callsite.json
inventory version: guild-progression-helper-callsite-inventory-v1
canonical LF SHA-256: ad8a5addf9ac9dd566284e0bc395ac40100986d0f14f0a49e9519a6aef28d351
integrity checks: 32/32
network requests: 0
route occurrences: 1
call candidates: 1
direct invocation candidates: 1
call class: generic_helper_call
method candidate: POST
method evidence: method_property_literal
method candidate unambiguous: true
```

Observed structural spans:

```text
call/envelope characters: 2479207
function characters: 2411715
reviewable threshold: 65536
```

Versioned review:

```text
evidence/real-data/argentum-guild-progression-callsite-review.json
review version: guild-progression-helper-callsite-review-v1
SHA-256: d79302d755eab918ce3f85a9ad39e78231720391c8f0692925fe2e79b6adc60f
integrity checks: 36/36
helper/call-site reviewed: true
HTTP method candidate: POST
helper identity resolved: false
request payload mapping resolved: false
request shape sufficient for bounded probe: false
ready for helper-definition inventory: true
ready for bounded route probe: false
```

Blockers:

```text
generic_helper_identity_unresolved
structural_envelope_overbroad
request_payload_mapping_unresolved
```

`POST` is an evidence-backed candidate inside the observed generic-helper call. It is not a verified request contract. Do not perform a guessed network request.

Implementation:

```text
src/coa_workbench/collector/guild_progression_callsite_contract.py
src/coa_workbench/collector/guild_progression_js_index.py
src/coa_workbench/collector/guild_progression_callsite_inventory.py
scripts/inventory_guild_progression_callsite.py
src/coa_workbench/collector/guild_progression_callsite_review.py
scripts/review_guild_progression_callsite.py
tests/unit/test_guild_progression_callsite_inventory.py
tests/unit/test_guild_progression_callsite_review.py
tests/unit/test_versioned_guild_progression_callsite_review.py
```

The deterministic review uses canonical LF hashes for versioned JSON sources so Linux and Windows checkouts generate the same receipt.

## Last confirmed implementation checkpoint

Before the documentation checkpoint, the exact implementation HEAD was:

```text
HEAD: 2bfd1e15abe715d37454db95d6b46fd17619ed99
Verify repository run: #570
public-release-audit: success
Ubuntu: success
Windows: success
pytest: 356 passed, 1 warning
Doctor: success
DuckDB clean/repeated initialization: success
migrations: 0001–0008
```

Recheck live. Do not transfer this result to a later HEAD.

## Current exact boundary

```text
guild identity verified: true
guild filtering completed: true
full crawl collection contract reviewed: true
guild-search route/schema verified: true
guild-search limit truncation verified: true
progression route candidate observed: true
progression usage context reviewed: true
progression helper/call-site inventory observed: true
progression helper/call-site reviewed: true
progression HTTP method candidate: POST
progression method candidate unambiguous: true
progression helper identity resolved: false
progression request payload mapping resolved: false
progression request shape verified: false
ready for helper-definition inventory: true
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
offline helper-definition inventory from the exact archived SPA asset
-> bind definition/call-chain candidates to the published callee hash
-> publish scalar-free definition/call-chain hashes and classifications
-> explicit helper-definition review
-> bounded progression route probe only if helper identity and exact request contract become verified
-> response schema review
-> pagination/termination/completeness review
-> API-versus-private-baseline set comparison
-> explicit full-crawl promotion
```

No false gate may be raised by inference. Never version private recovery, private inventories, raw JavaScript contexts, raw callees, source IDs, credentials or raw archive contents.
