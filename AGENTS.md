# CoA Raid Intelligence — Agent Instructions

These instructions apply to the entire repository.

## Canonical context order

Read in this order:

1. `AGENTS.md`
2. `docs/COA_DOMAIN_BOUNDARY.md`
3. `docs/COA_TARGET_PRODUCT_DEFINITION.md`
4. `docs/PROJECT_MASTER_CONTEXT.md`
5. `docs/PROJECT_STATE.md`
6. `docs/E3_GUILD_PROGRESSION_EVIDENCE_STATUS.md`
7. `docs/CI_OPERATIONS.md`
8. `docs/WINDOWS_DEVELOPMENT_ENVIRONMENT.md` for Windows-local work
9. `docs/CONTINUATION_PROMPT.md`
10. relevant ADR/capture/review documents
11. `evidence/real-data/README.md`

Documentation never replaces live verification of GitHub, current code, local private artifacts or CI.

## Mission and truth model

Build a localhost-first evidence-first raid intelligence system **only for Conquest of Azeroth**.

The product must eventually explain:

> Why is this specific player needed by this exact current roster?

Core truth rules:

```text
combat-log event = observation
combat-log event != automatic mechanic proof
class/spec presence != verified capability coverage
shared Ascension text != CoA mechanic proof
```

Only `corroborated` and `confirmed` mechanics may enter canonical planner scoring.

## Operating responsibility

The agent owns every operation it can perform directly.

- GitHub inspection, PR/CI checks, branch comparison, documentation updates and other available GitHub mutations are performed by the agent through the GitHub connector.
- Do not ask the user to run GitHub commands merely to report information available through the connector.
- Do not ask the user to repeat repository searches or source inspection that the agent can perform itself.
- The user is required only at the boundary the agent cannot access directly: the user's Windows filesystem, local-only runtime state, browser/session state, or private artifacts that have not been shared.
- When local execution is necessary, prefer **one bundled action** producing one compact result or one handoff artifact. Avoid chains of manual commands.
- `git diff HEAD` does not include untracked files. When exact local state matters, account for tracked changes **and** untracked files explicitly.

Private data is not forbidden input. The agent may inspect private/raw files when they are required to solve the task. Privacy restrictions apply to **publication, logging and versioning**, not to private analysis itself.

## Development modes

Choose the lightest mode that preserves correctness.

### Normal development

- focused tests while iterating;
- one coherent implementation change;
- one full `scripts/verify_repo.py` before push;
- one push;
- GitHub CI is the final cross-platform assurance.

Do not repeatedly run the full suite after every small edit when focused tests are sufficient.

### Evidence-sensitive development

Use the normal flow plus:

- deterministic evidence validation;
- public/private binding validation;
- privacy/publication validation;
- explicit false downstream gates until evidence closes them.

Implementation, tests and the approved scalar-free public receipt may be one coherent commit when they form one meaningful evidence stage and have been validated together.

### High-risk capability gate

Requires an explicit contract before enabling:

- first/unknown network request;
- destructive migration or data-loss operation;
- promotion into trusted scoring/recommendations;
- any action that changes privacy/security boundaries.

A route name, HTTP method candidate, helper-name similarity or request-shape marker is never enough to authorize a probe.

## Diagnostic discipline

Diagnostics exist to decide the next implementation, not to become an endless architecture.

- Prefer one narrow offline diagnostic when it can distinguish two materially different fixes.
- Do not create a permanent evidence stage for every intermediate question.
- Stop broad alias/owner searches when they do not bind the actual invocation; trace provenance from the concrete invocation instead.
- Never increase an evidence gate by inference.

## Branch policy

Active branch structure:

```text
main
└── e2/log-evidence-refactor        Draft PR #3 -> main
    └── e3/real-log-capture         Draft PR #7 -> e2/log-evidence-refactor
```

Keep the branch list small.

- Temporary Codex, cleanup and `*-stage` branches must be deleted after their PR is merged/closed or after their commits are proven ancestors of the active branch.
- Do not create a staging branch merely to perform a normal bounded change.
- Prefer the existing active branch for the current milestone.
- Keep `main`, the current parent feature branch, and the current working feature branch; remove obsolete branches promptly.

See `docs/PROJECT_STATE.md` for the audited cleanup list.

## Current E3 correction boundary

Remote checkpoint at the start of the 2026-08-13 cleanup:

```text
HEAD: be899cc5f66c7bd82a1006116dbe57d91ecaed84
Verify repository: #613
run ID: 31651028612
result: success
public-release-audit: success
ubuntu: success
windows: success
```

The previously versioned helper definition/reference/owner receipts remain useful historical artifacts, but they are **superseded for helper-identity inference** because a lexical-analysis defect was later demonstrated: terminal helper-like text inside JavaScript template-literal text was counted as executable code.

The current local correction is not yet a remote canonical checkpoint. Provisional local observations after lexical hardening are documented in `docs/PROJECT_STATE.md` and `docs/E3_GUILD_PROGRESSION_EVIDENCE_STATUS.md`.

Do not reuse the old `31 references / 1 definition / owner groups 5 vs 7` model as current truth.

## Product-oriented next direction

After the analyzer repair is stabilized and versioned:

```text
trace the two concrete full-chain helper invocations
-> establish the actual helper implementation/provenance
-> establish exact request payload mapping
-> review the bounded request contract
-> only then perform one bounded progression request
```

Do not return to open-ended global owner/alias graph exploration unless concrete invocation provenance requires it.

## Raw data and privacy

Versioned:

- code/tests;
- migrations;
- reviewed mappings/reviews;
- canonical documentation;
- approved provisional references;
- scalar-free public receipts.

Local/private:

```text
data/raw/
data/warehouse/
data/normalized/
data/reconstructed/
data/extracted/
data/exchange/in/
data/exchange/out/
```

Private files may be inspected during analysis. Never publish or commit cookies, tokens, Authorization values, browser profiles, `.env` secrets, unsanitized HAR, private source IDs/report IDs, private queries, private receipts, raw JavaScript, raw owner chains or raw private contexts unless a deliberately reviewed publication contract explicitly permits the specific field.

Do not delete tracked `.gitkeep` files.

## Database and migrations

- Current migration range: `0001`–`0008`.
- Never edit a migration already published to branch history.
- Add a migration only for a demonstrated schema gap.
- Live-network behavior is not a unit test.
- Use deterministic fake responses in tests.

## Windows/local rules

Repository:

```text
C:\Users\Simpa\source\repos\coa-raid-intelligence-workbench
```

Windows automation standard is PowerShell 7+ (`pwsh`). See `docs/WINDOWS_DEVELOPMENT_ENVIRONMENT.md`.

Complex local automation must be provided as one complete downloadable script rather than fragmented interactive commands. The output should be concise and demonstrative.

## Verification

Dependency preparation:

```powershell
uv sync --frozen --extra dev --no-build-package ruff
```

Canonical checks:

```powershell
uv run --no-sync python -m ruff check .
uv run --no-sync python -m ruff format --check .
uv run --no-sync python -m pytest
uv run --no-sync python scripts/verify_repo.py
```

During iteration use focused tests; before a meaningful push run one aggregate verifier. Never claim a pass unless it actually ran against the stated checkout/diff.

## Commit policy

Prefer **one coherent commit per meaningful change**. Do not create micro-commits merely to satisfy process ceremony.

Separate only genuinely independent concerns such as unrelated dependency repair, migration work or cleanup.

Before push, verify the intended file set and privacy boundary. Do not use broad staging/cleanup commands over private data trees.

## Completion report

Report only what materially helps continuation:

- verified current state;
- meaningful files/changes;
- actual tests/CI state;
- privacy/evidence boundary;
- remaining blocker;
- next product-facing action.
