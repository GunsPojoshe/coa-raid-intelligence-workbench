# Continuation prompt — CoA Raid Intelligence Workbench

Continue development of:

```text
repository: GunsPojoshe/coa-raid-intelligence-workbench
local repo: C:\Users\Simpa\source\repos\coa-raid-intelligence-workbench
branch: e3/real-log-capture
Draft PR #7: e3/real-log-capture -> e2/log-evidence-refactor
parent Draft PR #3: e2/log-evidence-refactor -> main
```

Work evidence-first. Never trust stale HEAD, CI, hashes, counts, routes or readiness. Verify live before changes.

## Mandatory start

1. Inspect PR #7 state, draft status, mergeability, base/head and current SHA.
2. Inspect PR #3 and branch relation.
3. Inspect the latest `Verify repository` run and every job for the exact current HEAD.
4. Read in order:
   - `AGENTS.md`;
   - `docs/PROJECT_MASTER_CONTEXT.md`;
   - `docs/PROJECT_STATE.md`;
   - `docs/CONTINUATION_PROMPT.md`;
   - `docs/REAL_LOG_CAPTURE.md`;
   - `docs/GUILD_WIDE_COLLECTION_CONTRACT.md`;
   - relevant ADR/capture/review documents;
   - `evidence/real-data/README.md`.
5. Compare documentation with code, migrations and versioned receipts.
6. Inspect local Git state before requesting local execution:

```powershell
git branch --show-current
git rev-parse HEAD
git status --porcelain=v1 --untracked-files=all
git fetch --all --prune
git rev-parse origin/e3/real-log-capture
```

7. If the remote branch is ahead and the working tree is clean, provide one complete `git pull --ff-only` PowerShell block.
8. Preserve all ignored/private evidence paths and tracked `.gitkeep` files.

## Collaboration convention

After every push or connector write that launches GitHub Actions:

1. identify the exact new HEAD and workflow run;
2. check and report `public-release-audit`, Ubuntu and Windows immediately;
3. offer one opt-in completion notification tied to that exact run;
4. create the condition-watch task only after the user presses/accepts it;
5. disable the task after completion or if superseded.

The user prefers a 15-minute check interval. Current automation supports no more than hourly checking. Use the fastest supported cadence and state the limitation honestly. Do not claim 15-minute polling is active.

Do not passively wait inside the response. Check the current state now; use the task only for later completion.

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

## Last fully verified implementation checkpoint

```text
HEAD: 82265903a26bbf8e0032e6dc2512e623055da972
commit: Format guild progression helper definition CLI
Verify repository run: #578
conclusion: success
public-release-audit: success
Ubuntu: success
Windows: success
working tree after push: clean
```

Documentation-only commits were created after this checkpoint. Recheck the live current HEAD and its CI before new implementation work.

## Progression helper/call-site checkpoint

```text
inventory: evidence/real-data/argentum-guild-progression-callsite.json
inventory version: guild-progression-helper-callsite-inventory-v1
canonical LF SHA-256: ad8a5addf9ac9dd566284e0bc395ac40100986d0f14f0a49e9519a6aef28d351
integrity checks: 32/32
network requests: 0
route occurrences: 1
call candidates: 1
direct invocation candidates: 1
call class: generic_helper_call
HTTP method candidate: POST
method evidence: method_property_literal
method candidate unambiguous: true
```

```text
review: evidence/real-data/argentum-guild-progression-callsite-review.json
review version: guild-progression-helper-callsite-review-v1
SHA-256: d79302d755eab918ce3f85a9ad39e78231720391c8f0692925fe2e79b6adc60f
integrity checks: 36/36
helper/call-site reviewed: true
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

`POST` is evidence-backed but not a verified request contract. Do not perform a guessed network request.

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

The implementation:

- performs no network requests;
- reads the exact archived SPA asset and bound call-site/recovery artifacts;
- searches bounded helper-definition and alias candidates;
- keeps raw helper definitions, aliases, callees and JavaScript contexts private;
- emits a scalar-free public receipt;
- applies `36` integrity checks;
- keeps route, pagination, completeness, crawl and scoring gates false.

The implementation and formatting are CI-green. It has not yet been executed against the current local private artifacts, and no helper-definition receipt or review is versioned.

## Local Windows tooling facts

```text
repo: C:\Users\Simpa\source\repos\coa-raid-intelligence-workbench
last local implementation HEAD before documentation commits: 82265903a26bbf8e0032e6dc2512e623055da972
working tree after push: clean
private evidence paths: preserved
virtual environment at that time: not activated
```

Known issue:

```text
uv sync --frozen --extra dev
-> attempted source build of ruff==0.12.12
-> failed because MSVC link.exe was unavailable
```

Do not install Visual Studio Build Tools solely to format one file. The previous formatting fix used the official standalone Ruff `0.12.12` Windows binary and passed:

```text
ruff check: success
ruff format --check: success
git diff --check: success
```

Use `git --no-pager diff` in PowerShell instructions to avoid entering the `(END)` pager.

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
helper-definition inventory implementation complete: true
helper-definition inventory executed on private artifacts: false
helper-definition public receipt validated: false
helper-definition receipt versioned: false
helper-definition review complete: false
progression helper identity resolved: false
progression request payload mapping resolved: false
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
verify current documentation HEAD and CI
-> fast-forward local e3/real-log-capture
-> confirm clean working tree and preserved private evidence
-> inspect the helper-definition CLI contract and required paths
-> run offline helper-definition inventory against exact local private artifacts
-> preserve private output under data/extracted
-> inspect all 36 integrity checks and candidate classifications
-> verify public receipt contains no private scalars or raw JavaScript
-> version only the scalar-free public receipt if valid
-> implement explicit deterministic helper-definition review
-> bounded progression route probe only if helper identity and exact payload contract become verified
```

## Local execution guardrails

- Provide one complete PowerShell block, not fragmented commands.
- Validate branch, expected HEAD and clean working tree before changes.
- Do not delete `data/raw`, `data/extracted`, `data/warehouse`, `data/exchange/in` or `data/exchange/out`.
- Do not delete tracked `.gitkeep` files.
- Do not commit private recovery, private inventory, raw archive, source IDs, report IDs, private queries, HAR, cookies, tokens or browser profiles.
- Show the exact public file that would be committed.
- Stop on any integrity, privacy, binding or unexpected-diff failure.

No false gate may be raised by inference.