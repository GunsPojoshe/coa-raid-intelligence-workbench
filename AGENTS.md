# CoA Raid Intelligence — Agent Instructions

These instructions apply to the whole repository.

## Mission

Build a localhost-first, evidence-first raid intelligence system **only for Conquest of Azeroth** that can eventually explain:

> Why is this specific player needed by this exact current roster?

Only `corroborated` and `confirmed` mechanics may enter canonical planner scoring.

## Responsibility

The agent performs everything it can do directly: GitHub repository/branch/PR/CI inspection and mutations, repository source/history inspection, documentation maintenance, and analysis of shared private/raw artifacts.

The user is involved only for the boundary the agent cannot access directly: the user's Windows filesystem, local runtime/browser state, or unshared private files. When local work is required, prefer **one bundled action** producing one compact result or handoff artifact.

Private/raw files are valid analysis inputs. Privacy rules constrain **publication/versioning**, not private analysis.

## Development workflow

```text
focused tests while iterating
-> one coherent change
-> one scripts/verify_repo.py
-> one push
-> exact-head GitHub CI
```

Evidence-sensitive work additionally validates deterministic bindings and publication/privacy boundaries. Do not create permanent evidence stages for every intermediate question.

## Git/branches

Keep only active branches unless a temporary branch has a current purpose:

```text
main
e2/log-evidence-refactor
e3/real-log-capture
```

Delete merged/closed/stage branches promptly. Never rewrite published migrations. Never delete tracked `.gitkeep` files.

## Current guild-progression boundary

The historical helper chain that treated `/api/guilds/progression` as a candidate POST endpoint is superseded.

Direct inspection of the exact archived SPA asset established:

```text
exact literal /api/guilds/progression: cache-exclusion configuration only
direct request to exact /api/guilds/progression: none
observed direct progression methods: GET
observed direct progression calls: 4
```

Observed frontend request contracts:

```text
GET /api/guilds/progression/rankings
GET /api/guilds/progression/full-clears
GET /api/guilds/progression/rankings/{bossId}
```

Canonical public receipt:

```text
evidence/real-data/argentum-guild-progression-frontend-request-contract.json
```

`GET /api/guilds/progression/rankings` has an observed empty-params branch, so it is the first bounded request contract. The review stage itself performed no network request.

Do not continue the old global helper/owner/alias investigation unless a future concrete request path requires it.

## Privacy

Local/private by default:

```text
data/raw/
data/warehouse/
data/normalized/
data/reconstructed/
data/extracted/
data/exchange/in/
data/exchange/out/
```

Never publish secrets, cookies, tokens, Authorization values, browser profiles, unsanitized HAR, private source IDs/report IDs, private queries, private receipts, raw JavaScript, raw owner chains or raw private contexts unless an explicit reviewed publication contract permits the exact field.

## Windows

Repository:

```text
C:\Users\Simpa\source\repos\coa-raid-intelligence-workbench
```

Use PowerShell 7+ (`pwsh`) for new project automation. Complex local automation should be a complete downloadable script, not a fragmented interactive paste.

Remember: `git diff HEAD` does not include untracked files.

## Verification

Dependency preparation:

```powershell
uv sync --frozen --extra dev --no-build-package ruff
```

Canonical aggregate check before a meaningful push:

```powershell
uv run --no-sync python scripts/verify_repo.py
```

Use focused tests during iteration. Never claim a pass unless it actually ran against the stated checkout/diff.
