# CoA Raid Intelligence — Agent Instructions

These instructions apply to the whole repository.

## Mission

Build a localhost-first, evidence-first raid intelligence system **only for Conquest of Azeroth** that
can eventually explain:

> Why is this specific player needed by this exact current roster?

Only `corroborated` and `confirmed` mechanics may enter canonical planner scoring.

## Responsibility

The agent performs everything it can do directly: GitHub repository/branch/PR/CI inspection and
mutations, repository source/history inspection, documentation maintenance, and analysis of shared
private/raw artifacts.

The user is involved only for the boundary the agent cannot access directly: the user's Windows
filesystem, local runtime/browser state, or unshared private files. When local work is required, prefer
**one bundled action** producing one compact result or handoff artifact.

Private/raw files are valid analysis inputs. Privacy rules constrain **publication/versioning**, not
private analysis.

## Development workflow

```text
focused tests while iterating
-> one coherent change
-> one scripts/verify_repo.py
-> one push
-> exact-head GitHub CI
```

Evidence-sensitive work additionally validates deterministic bindings and publication/privacy
boundaries. Do not create permanent evidence stages for every intermediate question.

## Source discovery rule

Prefer the shortest evidence path:

```text
browser Network / Fetch / XHR
-> sanitized HAR inventory
-> reviewed request contract
-> immutable source capture
-> schema/dimension baseline
-> source-change event
-> scoped reanalysis
```

Inspect SPA JavaScript only when Network evidence does not fully explain request construction, optional
parameters or route selection. Do not start with minified-helper archaeology when an actual browser
request is available.

A timestamped source response is an observation, not permanent source semantics. Bosses, phases, logs,
fields, routes and meta are expected to evolve.

## Current real Source Observatory checkpoint

The user's local Observatory already contains the real browser-origin baseline for:

```text
phases_api
guild_phase_progression_api
```

The approved real derived `source_dimension_index` is initialized:

```text
observed endpoints: 2
active dependencies: 2
dimension names represented: 5
dimension values represented: 19
completed analysis runs: 1
```

The same existing HAR has already been replayed and was idempotent:

```text
open change events: 2 -> 2
pending reanalysis: 0 -> 0
new change events: 0
new reanalysis requests: 0
```

Do **not** ask the user to re-run this same HAR or reinitialize this same baseline merely to rediscover
those facts. The next meaningful proof requires a genuinely later observation or expansion to a new
source surface.

Canonical public receipts:

```text
evidence/real-data/source-observatory-network-baseline-2026-08-14.json
evidence/real-data/source-observatory-derived-baseline-2026-08-14.json
```

## Current guild-progression boundary

The old exact `/api/guilds/progression` POST hypothesis is superseded.

Historical/current SPA review still contains alternate rankings contracts:

```text
GET /api/guilds/progression/rankings
GET /api/guilds/progression/full-clears
GET /api/guilds/progression/rankings/{bossId}
```

The real current progression browser capture exercised:

```text
GET /api/phases
GET /api/guilds/phase-progression?phase=<value>&difficulty=<value>
```

Both returned `200 application/json`.

Do not resume the old global helper/owner/alias investigation unless a future concrete request cannot
be explained from Network evidence.

## Source Observatory

`Source Observatory v1` is the universal ingestion/change layer. Reviewed sources should flow through
the same infrastructure instead of creating endpoint-specific persistence stacks.

Generic Network discovery:

```text
scripts/inventory_network_har.py
```

Recurring browser HAR ingestion:

```powershell
uv run --no-sync python scripts/observe_network_cycle.py
```

With no positional HAR path, the command selects the newest readable `.har` in `~/Downloads` that
contains same-origin `/api/` traffic for the configured source host. Use `--har-dir` for another inbox
or pass an explicit HAR path when needed. Do not ask the user to manually identify a HAR path when this
automatic selection can resolve it.

Its public output must not include the selected local HAR path.

Generic discovery output must remain scalar-free: no query values, headers, cookies, response bodies,
user/session values, guild/report IDs or other record scalars.

Low-cardinality source dimensions such as phase, boss, difficulty and location may drive automatic
change detection. High-cardinality player/guild/report identifiers do not automatically become
source-change dimensions.

## Git/branches

Keep only active branches unless a temporary branch has a current purpose:

```text
main
e2/log-evidence-refactor
e3/real-log-capture
```

Delete merged/closed/stage branches promptly. Never rewrite published migrations. Never delete tracked
`.gitkeep` files.

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

Never publish secrets, cookies, tokens, Authorization values, browser profiles, unsanitized HAR,
private source IDs/report IDs, private queries, private receipts, raw JavaScript, raw owner chains or
raw private contexts unless an explicit reviewed publication contract permits the exact field.

## Windows

Repository:

```text
C:\Users\Simpa\source\repos\coa-raid-intelligence-workbench
```

Use PowerShell 7+ (`pwsh`) for new project automation. Complex local automation should be a complete
downloadable script, not a fragmented interactive paste.

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

Use focused tests during iteration. Never claim a pass unless it actually ran against the stated
checkout/diff.
