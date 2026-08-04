# CoA Raid Intelligence — Agent Instructions

These instructions apply to the entire repository.

## Canonical context

Read in this order:

1. `AGENTS.md`;
2. `docs/PROJECT_MASTER_CONTEXT.md`;
3. `docs/PROJECT_STATE.md`;
4. `docs/CONTINUATION_PROMPT.md`;
5. `docs/REAL_LOG_CAPTURE.md`;
6. `docs/GUILD_WIDE_COLLECTION_CONTRACT.md`;
7. relevant ADR/capture/review documents;
8. `evidence/real-data/README.md`.

Documentation never replaces checking GitHub, code, local private artifacts and CI.

## Mission and truth model

Build a localhost-first raid intelligence system for Classless / Ascension WoW that produces explainable recommendations only from reproducible evidence.

```text
combat-log event = observation
combat-log event != automatic proof of a general mechanic
```

Only `corroborated` and `confirmed` mechanics may enter canonical planner scoring.

## Required start sequence

1. Inspect repository, current branch, remote HEAD and working tree.
2. Inspect PR #7, its base branch and parent PR #3.
3. Inspect the latest GitHub Actions run and every job for the exact current HEAD.
4. Read the canonical context documents in the order above.
5. Compare documentation claims with code, migrations and versioned receipts.
6. Inspect required local private artifacts before any local-only decision or capture.
7. Run focused deterministic tests before bounded real capture.
8. Report material discrepancies before changing analytical semantics.

Do not trust old commit, CI run, test count, hash, route, source count or readiness claim without checking.

## Collaboration and workflow notifications

After every push or connector write that starts a GitHub Actions workflow:

1. report the new HEAD and workflow run number/status;
2. offer one opt-in notification tied to that exact run;
3. create the condition-watch task only after the user accepts;
4. include final conclusions for `public-release-audit`, Ubuntu and Windows;
5. disable the task when the run completes or is superseded.

The user prefers checks every 15 minutes. Use the fastest cadence supported by the automation platform. The current platform limit is once per hour; never claim that 15-minute polling was configured when it was not.

Do not enter passive waiting. Check the current state during the active turn and use the notification task only for later completion.

## Current milestone

```text
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

PR #7 remains Draft until its evidence gates are explicitly closed.

## Completed E3 checkpoints

- verified Armory and public-report discovery mappings;
- report/encounter/combatants capture and persistence through migration `0008`;
- exhaustive deduplicated public-report manifest: `6454` reports;
- verified Argentum identity and private comparison baseline: `17` reports;
- reviewed full-crawl collection contract;
- `/api/guilds/search` route/schema review;
- bounded limit capture `1 / 7 / 7` and explicit limit-truncation review;
- offline `/api/guilds/progression` usage-context inventory and review;
- offline helper/call-site inventory and review;
- helper-definition inventory implementation and deterministic tests.

Do not repeat a completed checkpoint unless a bound hash, fingerprint or contract changes.

## Current progression boundary

The helper/call-site review established an evidence-backed `POST` candidate but did not resolve generic-helper identity or payload mapping.

The implemented next tool is:

```text
src/coa_workbench/collector/guild_progression_helper_definition_command.py
src/coa_workbench/collector/guild_progression_helper_definition_index.py
src/coa_workbench/collector/guild_progression_helper_definition_inventory.py
scripts/inventory_guild_progression_helper_definition.py
tests/unit/test_guild_progression_helper_definition_command.py
tests/unit/test_guild_progression_helper_definition_index.py
tests/unit/test_guild_progression_helper_definition_inventory.py
```

It is offline-only, reads the exact archived SPA asset and bound private/public call-site/recovery artifacts, keeps raw definitions and aliases private, emits a scalar-free public receipt, and enforces `36` integrity checks.

It must keep every downstream gate false, including:

```text
ready for bounded progression route probe: false
guild API route semantics verified: false
pagination semantics verified: false
termination semantics verified: false
completeness verified: false
ready for full guild crawl: false
planner scoring allowed: false
```

No versioned helper-definition receipt or explicit helper-definition review exists yet. The next bounded task is to run this inventory locally against the exact private artifacts, inspect the private output, validate the scalar-free public receipt, and only then consider versioning it.

Do not perform a guessed network request to `/api/guilds/progression`.

## Current decision boundary

```text
guild identity verified: true
guild filtering completed: true
full crawl collection contract reviewed: true
guild-search route/schema verified: true
guild-search limit truncation verified: true
progression route candidate observed: true
progression usage context reviewed: true
progression helper/call-site reviewed: true
progression HTTP method candidate: POST
progression method candidate unambiguous: true
helper-definition inventory implementation complete: true
helper-definition inventory executed on private artifacts: false
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
automatic full guild crawl allowed: false
ready for full guild crawl: false
ready for multi-report character graph: false
ready for performance model: false
ready for BiS 25 scoring: false
planner scoring allowed: false
```

## Trust and collection rules

- Never invent routes, parameters, fields, IDs, pagination or provider semantics.
- Probe and fingerprint real payloads before mappings.
- Archive complete response bytes before interpretation.
- Bind parsers and reviews to exact hashes/fingerprints.
- Unknown fingerprint means reject and review.
- Preserve contradicting evidence and failed requests.
- Accepted parameter does not prove its semantics.
- A method candidate does not prove helper identity, payload mapping or request shape.
- Public receipts must not expose source guild IDs, report IDs, private query values, request URLs, raw rows, raw JavaScript, callees, helper symbols, definitions, aliases or error text.
- Partial results may not be marked complete.
- Full crawl requires explicit route/query, schema, limit, pagination, termination, completeness and set-comparison evidence.

## Raw data and privacy

Versioned: code/tests, migrations, reviewed mappings, documentation and scalar-free receipts.

Local-only:

```text
data/raw/
data/warehouse/
data/normalized/
data/reconstructed/
data/extracted/
data/exchange/in/
data/exchange/out/
```

Never commit cookies, tokens, Authorization headers, browser profiles, `.env` secrets, unsanitized HAR, credentials, source guild IDs, report IDs, private queries, raw JavaScript contexts or private receipts.

## Local Windows rules

- User repository: `C:\Users\Simpa\source\repos\coa-raid-intelligence-workbench`.
- Preserve all evidence paths during cleanup.
- Do not delete tracked `.gitkeep` files inside ignored directories.
- Use `git --no-pager diff` in PowerShell blocks to avoid stopping at `(END)`.
- Do not assume an activated virtual environment is required for `uvx` or a standalone tool.
- Local `uv sync --frozen --extra dev` previously attempted to build Ruff `0.12.12` from source and failed because MSVC `link.exe` was unavailable. Do not install Visual Studio Build Tools solely for formatting. Use the official standalone Ruff `0.12.12` Windows binary when required, or fix the dependency resolution separately.
- Prefer `uv run --no-sync` or the existing environment for project commands only after verifying required runtime dependencies are present.
- Provide one complete PowerShell block for local actions.

## Database and collector rules

- Never edit a migration already published to branch history.
- Current migration range is `0001`–`0008`.
- Add a migration only for a demonstrated schema gap.
- Live-network behavior is not a unit test.
- Use deterministic fake responses in tests.
- Archive before interpretation.
- Write scalar-free receipts atomically.
- Preserve checkpoints on ordinary transport failure.
- Keep retries, scans, contexts and response sizes bounded.

## Verification

Canonical CI verification remains:

```powershell
uv sync --frozen --extra dev
uv run python scripts/verify_repo.py
```

For local Windows work, adapt tooling only when the environment cannot satisfy the locked dev installation, and report the deviation explicitly. Never claim a check passed unless it ran on the claimed HEAD.

## Completion report

Report verified facts, local-only observations, corrected stale claims, files changed, exact checks and CI state, remaining boundaries, and the next bounded task.