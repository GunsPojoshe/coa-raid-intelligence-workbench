# CoA Raid Intelligence — Agent Instructions

These instructions apply to the entire repository.

## Canonical context order

Read:

1. `AGENTS.md`
2. `docs/COA_DOMAIN_BOUNDARY.md`
3. `docs/COA_TARGET_PRODUCT_DEFINITION.md`
4. `docs/PROJECT_MASTER_CONTEXT.md`
5. `docs/PROJECT_STATE.md`
6. `docs/E3_GUILD_PROGRESSION_EVIDENCE_STATUS.md`
7. `docs/CI_OPERATIONS.md`
8. `docs/WINDOWS_DEVELOPMENT_ENVIRONMENT.md` for Windows local work
9. `docs/CONTINUATION_PROMPT.md`
10. relevant ADR/capture/review documents
11. `evidence/real-data/README.md`

Documentation never replaces live verification of GitHub, current code, local private artifacts or CI.

## Mission

Build a localhost-first evidence-first raid intelligence system **only for Conquest of Azeroth**.

The product must explain encounter-specific roster problems and answer:

> Why is this specific player needed by this exact current roster?

Core truth rules:

```text
combat-log event = observation
combat-log event != automatic mechanic proof
class/spec presence != verified capability coverage
shared Ascension text != CoA mechanic proof
```

Only `corroborated` and `confirmed` mechanics may enter canonical planner scoring.

## Required start sequence

1. Inspect repository, current local branch, remote branch and working tree.
2. Inspect PR #7, its base branch and parent PR #3.
3. Inspect exact current HEAD CI and every required job.
4. Read canonical context above.
5. Compare documentation claims with code, migrations, tests and versioned receipts.
6. Inspect required local private artifacts before local-only evidence actions.
7. Report material discrepancies before changing evidence semantics.

Never trust an old HEAD, CI run, hash, count, route or readiness claim without checking.

## Branch structure

```text
main
└── e2/log-evidence-refactor        Draft PR #3 -> main
    └── e3/real-log-capture         Draft PR #7 -> e2/log-evidence-refactor
```

PR #7 remains Draft until evidence gates are explicitly closed.

## Current E3 progression boundary

The last fully verified code/evidence checkpoint before the 2026-08-12 docs handoff was:

```text
HEAD: 13982825295737c029b425a37d210a34a7ea0762
Verify repository run: #603
run ID: 31533555026
result: success
```

Versioned evidence stages:

```text
helper-definition inventory: 36/36
helper-definition review: 42/42
helper-reference inventory: 40/40
helper-reference review: 46/46
```

Helper-reference review proves:

```text
references: 31
route-context references: 0
direct transport contexts: 0
helper identity resolved: false
helper owner binding resolved: false
request payload mapping resolved: false
request shape sufficient for bounded probe: false
ready for helper-owner inventory: true
ready for bounded progression route probe: false
network requests performed: false
```

At the handoff, four helper-owner implementation files existed **only locally, untracked**, had been formatted/validated, but were not committed and no real helper-owner inventory had been executed. See `docs/PROJECT_STATE.md`.

Do not repeat completed definition/reference inventory/review unless a bound hash, fingerprint or contract changes.

## Next bounded E3 sequence

```text
safely sync docs-only handoff commit
-> verify PowerShell 7 local runtime
-> inspect and revalidate local helper-owner implementation
-> version helper-owner implementation atomically
-> exact-head CI
-> execute offline helper-owner inventory
-> validate 54/54 and scalar-free public receipt
-> version public owner receipt separately
-> implement explicit helper-owner review
-> only then consider bounded route probe if exact helper/owner/payload binding exists
```

No guessed request to `/api/guilds/progression` is allowed.

## Trust and collection rules

- Never invent routes, parameters, fields, IDs, pagination or provider semantics.
- Probe/fingerprint real payloads before mappings.
- Archive complete response bytes before interpretation.
- Bind parsers/reviews to exact hashes and fingerprints.
- Unknown fingerprint means reject and review.
- Preserve contradicting evidence and failed requests.
- Accepted parameter does not prove semantics.
- Method candidate does not prove helper identity or payload mapping.
- Partial results may not be marked complete.
- Full crawl requires explicit route/query, schema, limit, pagination, termination, completeness and set-comparison evidence.

## Raw data and privacy

Versioned:

- code/tests;
- migrations;
- reviewed mappings/reviews;
- canonical documentation;
- approved provisional references;
- scalar-free public receipts.

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

Never commit cookies, tokens, Authorization headers, browser profiles, `.env` secrets, unsanitized HAR, source guild/report IDs, private queries, private receipts, raw JavaScript, raw owner chains or raw private contexts.

Do not delete tracked `.gitkeep` files.

## Database and migrations

- Current migration range: `0001`–`0008`.
- Never edit a migration already published to branch history.
- Add a migration only for a demonstrated schema gap.
- Live-network behavior is not a unit test.
- Use deterministic fake responses in tests.

## Windows local rules

Repository:

```text
C:\Users\Simpa\source\repos\coa-raid-intelligence-workbench
```

Windows automation standard:

```text
PowerShell 7+ / pwsh
```

The VS Code `ms-vscode.powershell` extension may be used, but verify that its active session is PowerShell 7 rather than Windows PowerShell 5.1. See `docs/WINDOWS_DEVELOPMENT_ENVIRONMENT.md`.

Run large automation as `.ps1`:

```powershell
pwsh -NoProfile -File .\script.ps1
```

Do not paste multi-branch/here-string-heavy programs into an interactive prompt.

User workflow preference: when a complex local PowerShell workflow is needed, provide a complete downloadable `.ps1`, not fragmented commands.

Use `git --no-pager diff`. Do not install Visual Studio Build Tools solely for Ruff.

## Verification

Prepare dependencies using the current locked project contract:

```powershell
uv sync --frozen --extra dev --no-build-package ruff
```

Then prefer `--no-sync` for deterministic checks:

```powershell
uv run --no-sync python -m ruff check .
uv run --no-sync python -m ruff format --check .
uv run --no-sync python -m pytest
uv run --no-sync python scripts/verify_repo.py
```

Always compare with `docs/CI_OPERATIONS.md`. Never claim a check passed unless it ran on the claimed HEAD/working diff.

## Commit policy

Keep scopes atomic:

- implementation;
- public evidence receipt;
- documentation;
- CI/dependency infrastructure;
- cleanup.

Show exact public/staged diff before commit. Never use `git add -A` when a bounded file set is expected.

## Completion report

Report:

- verified facts;
- files changed;
- exact tests/CI state;
- privacy/evidence boundary;
- remaining blockers;
- next bounded action.
