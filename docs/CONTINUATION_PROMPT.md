# Continuation prompt — CoA Raid Intelligence Workbench

Continue development of:

```text
repository: GunsPojoshe/coa-raid-intelligence-workbench
local repo: C:\Users\Simpa\source\repos\coa-raid-intelligence-workbench
branch: e3/real-log-capture
Draft PR #7: e3/real-log-capture -> e2/log-evidence-refactor
parent Draft PR #3: e2/log-evidence-refactor -> main
```

Work evidence-first. Never trust stale HEAD, CI, hashes, counts, routes or readiness.

## Mandatory start

1. Inspect PR #7 and PR #3 live.
2. Inspect the latest `Verify repository` run for the exact current HEAD.
3. Read in order:
   - `AGENTS.md`;
   - `docs/COA_DOMAIN_BOUNDARY.md`;
   - `docs/COA_TARGET_PRODUCT_DEFINITION.md`;
   - `docs/PROJECT_MASTER_CONTEXT.md`;
   - `docs/PROJECT_STATE.md`;
   - `docs/CONTINUATION_PROMPT.md`;
   - `docs/REAL_LOG_CAPTURE.md`;
   - `docs/GUILD_WIDE_COLLECTION_CONTRACT.md`;
   - relevant ADR/capture/review documents;
   - `docs/COA_RAID_UTILITY_BASELINE_2026-08-02.md` when capability research is relevant;
   - `evidence/real-data/README.md`.
4. Compare documentation with code, migrations and receipts.
5. Inspect local Git state before local execution.

## Canonical product and realm scope

The project is only for **Conquest of Azeroth**.

Do not use Bronzebeard, Classless Ascension, Mystic Enchants, Hero Architect or other-realm mechanics as CoA facts without independent exact CoA evidence.

The target product is not one permanent BiS 25 roster. It is an encounter-aware raid intelligence system that combines actual attendance, player/build/performance evidence and encounter requirements to explain roster additions and replacements.

Core question:

> Why is this specific player needed by this current roster?

## Core truth model

```text
source response
-> immutable raw archive
-> exact hash and schema fingerprint
-> reviewed mapping/extractor
-> deterministic normalization/reconstruction
-> immutable observations
-> supporting and contradicting evidence
-> trust decision
-> explainable raid-leader recommendation
```

```text
combat-log observation != mechanic proof
class/spec presence != capability coverage
shared Ascension text != CoA mechanic proof
```

## Verified project baseline

```text
public reports: 6454
unique public report IDs: 6454
exact Argentum label reports: 17
guild identity verified: true
private selected baseline: 17 unique reports
full-crawl collection contract reviewed: true
migrations: 0001–0008
```

Private source guild ID, report IDs, raw JavaScript and source rows are not versioned.

## Latest fully completed CI before CoA documentation refresh

```text
HEAD: 49bf9cdae01817cc0a7c6eb073d23d588ba6045e
Verify repository run: #583
conclusion: success
public-release-audit: success
Ubuntu: success
Windows: success
```

Documentation-only commits were created after this checkpoint. Recheck live current HEAD and CI.

## Provisional CoA raid utility baseline

```text
source SHA-256: adbb2f7f06d750ddad4d981cca3f22b3141f471e8f9819e87f528f357fabdddd
class cards: 28
class/spec associations: 87
unique specialization labels: 67
utility rows: 187
observed rows in latest 30-log sample: 132
zero-observation rows: 55
```

This is a provisional research reference. It is not a verified full catalog of 69 specializations and may not enter planner scoring.

Every capability must be verified through exact CoA source and combat-log evidence, including provider, target, uptime, scope, stacking, overwrite and contradictory observations.

## Progression helper/call-site checkpoint

```text
inventory checks: 32/32
review checks: 36/36
call class: generic_helper_call
HTTP method candidate: POST
method candidate unambiguous: true
helper identity resolved: false
request payload mapping resolved: false
request shape sufficient for bounded probe: false
ready for bounded route probe: false
```

`POST` is evidence-backed but is not a verified request contract. Do not perform a guessed network request.

## Implemented helper-definition inventory

```text
src/coa_workbench/collector/guild_progression_helper_definition_command.py
src/coa_workbench/collector/guild_progression_helper_definition_index.py
src/coa_workbench/collector/guild_progression_helper_definition_inventory.py
scripts/inventory_guild_progression_helper_definition.py
tests/unit/test_guild_progression_helper_definition_command.py
tests/unit/test_guild_progression_helper_definition_index.py
tests/unit/test_guild_progression_helper_definition_inventory.py
```

The tool:

- performs no network requests;
- reads exact archived SPA and bound artifacts;
- searches bounded definition and alias candidates;
- keeps raw definitions, aliases and contexts private;
- emits a scalar-free public receipt;
- applies 36 integrity checks;
- keeps route, pagination, completeness, crawl and scoring gates false.

## Current exact boundary

```text
helper-definition inventory implementation complete: true
helper-definition inventory executed on private artifacts: false
helper-definition public receipt validated: false
helper-definition receipt versioned: false
helper-definition review complete: false
progression helper identity resolved: false
progression request payload mapping resolved: false
progression request shape verified: false
ready for bounded progression route probe: false
pagination semantics verified: false
termination semantics verified: false
completeness verified: false
automatic full guild crawl allowed: false
ready for full guild crawl: false
ready for multi-report character graph: false
ready for performance model: false
ready for encounter-aware roster completion: false
planner scoring allowed: false
```

## Required next sequence

```text
verify exact current documentation HEAD and CI
-> fast-forward local e3/real-log-capture
-> confirm clean working tree and preserved evidence
-> run offline helper-definition inventory
-> inspect all 36 integrity checks and private candidates
-> verify public receipt contains no private scalars or raw JavaScript
-> version only the scalar-free receipt
-> implement explicit deterministic helper-definition review
-> consider bounded progression probe only after exact helper and payload verification
```

## Local execution guardrails

- Provide one complete PowerShell block.
- Validate branch, expected HEAD and clean working tree.
- Preserve `data/raw`, `data/extracted`, `data/warehouse`, `data/exchange/in`, `data/exchange/out` and tracked `.gitkeep` files.
- Do not commit private recovery, private inventory, raw archive, IDs, private queries, unsanitized HAR, cookies, tokens or browser profiles.
- Show exact public diff before commit.
- Stop on integrity, privacy, binding or unexpected-diff failure.
- Use `git --no-pager diff`.
- Do not install Visual Studio Build Tools solely for Ruff formatting.

No false gate may be raised by inference.
