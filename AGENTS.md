# CoA Raid Intelligence — Agent Instructions

These instructions apply to the entire repository.

## Canonical context

Read in this order:

1. `AGENTS.md`;
2. `docs/COA_DOMAIN_BOUNDARY.md`;
3. `docs/COA_TARGET_PRODUCT_DEFINITION.md`;
4. `docs/PROJECT_MASTER_CONTEXT.md`;
5. `docs/PROJECT_STATE.md`;
6. `docs/CONTINUATION_PROMPT.md`;
7. `docs/REAL_LOG_CAPTURE.md`;
8. `docs/GUILD_WIDE_COLLECTION_CONTRACT.md`;
9. relevant ADR/capture/review documents;
10. `docs/COA_RAID_UTILITY_BASELINE_2026-08-02.md` when capability research is relevant;
11. `evidence/real-data/README.md`.

Documentation never replaces live verification of GitHub, code, local private artifacts and CI.

## Mission

Build a localhost-first evidence-first raid intelligence system **only for Conquest of Azeroth**.

The product must help the raid leader understand combat results, encounter-specific composition problems and dynamic attendance-aware roster completion, including why a specific player is needed by the current roster.

```text
combat-log event = observation
combat-log event != automatic proof of a mechanic
class/spec presence != verified capability coverage
shared Ascension text != CoA mechanic proof
```

Only `corroborated` and `confirmed` mechanics may enter canonical planner scoring.

## CoA-only boundary

- Do not import Bronzebeard, Classless Ascension or other-realm mechanics into the CoA model.
- Mystic Enchants are outside the current CoA domain.
- Treat shared FAQ/frontend content as potentially cross-realm until independently verified from an exact CoA source.
- CoA BisBeard is a planning/reference source, not automatic runtime evidence.
- A provisional catalog may guide research but may not become planner truth without log verification.

The canonical boundary is `docs/COA_DOMAIN_BOUNDARY.md`.

## Required start sequence

1. Inspect repository, current branch, remote HEAD and working tree.
2. Inspect PR #7, its base branch and parent PR #3.
3. Inspect the latest GitHub Actions run and every job for the exact current HEAD.
4. Read the canonical context in the order above.
5. Compare documentation claims with code, migrations and versioned receipts.
6. Inspect required local private artifacts before any local-only decision or capture.
7. Run focused deterministic tests before bounded real capture.
8. Report material discrepancies before changing analytical semantics.

Do not trust old commit, CI run, test count, hash, route, source count or readiness claim without checking.

## Current branch structure

```text
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

PR #7 remains Draft until its evidence gates are explicitly closed.

## Current product direction

The long-term product is not one permanent BiS 25 roster.

The target is:

```text
actual attendance
+
verified player/build/performance evidence
+
encounter requirements
+
relevant external benchmarks
=
explainable roster completion and raid-leader decisions
```

Every recommendation must explain why a person is useful to this exact roster and encounter.

## Completed E3 checkpoints

- verified selected Armory and public-report discovery mappings;
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

## Provisional CoA utility baseline

`docs/COA_RAID_UTILITY_BASELINE_2026-08-02.md` records a user-supplied research baseline:

```text
class cards: 28
class/spec associations: 87
unique specialization labels: 67
utility rows: 187
observed in 30-log sample: 132
zero observations in sample: 55
```

It is not a verified complete catalog of 69 CoA specializations and is not allowed in canonical scoring.

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

It is offline-only, reads the exact archived SPA asset and bound private/public artifacts, keeps definitions and aliases private, emits a scalar-free public receipt and enforces `36` integrity checks.

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

No guessed request to `/api/guilds/progression` is allowed.

## Trust and collection rules

- Never invent routes, parameters, fields, IDs, pagination or provider semantics.
- Probe and fingerprint real payloads before mappings.
- Archive complete response bytes before interpretation.
- Bind parsers and reviews to exact hashes/fingerprints.
- Unknown fingerprint means reject and review.
- Preserve contradicting evidence and failed requests.
- Accepted parameter does not prove its semantics.
- A method candidate does not prove helper identity, payload mapping or request shape.
- Talent text does not prove runtime behavior.
- Character build selection does not prove actual use.
- Actual use does not prove successful raid coverage.
- Partial results may not be marked complete.
- Full crawl requires explicit route/query, schema, limit, pagination, termination, completeness and set-comparison evidence.

## Raw data and privacy

Versioned:

- code and tests;
- migrations;
- reviewed mappings and reviews;
- canonical documentation;
- approved provisional references;
- scalar-free receipts.

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

## Database and collector rules

- Never edit a migration already published to branch history.
- Current migration range is `0001`–`0008`.
- Add a migration only for a demonstrated schema gap.
- Live-network behavior is not a unit test.
- Use deterministic fake responses in tests.
- Archive before interpretation.
- Write public receipts atomically.
- Preserve checkpoints on ordinary transport failure.
- Keep retries, scans, contexts and response sizes bounded.

## Local Windows rules

- User repository: `C:\Users\Simpa\source\repos\coa-raid-intelligence-workbench`.
- Preserve all evidence paths during cleanup.
- Do not delete tracked `.gitkeep` files.
- Use `git --no-pager diff`.
- Do not install Visual Studio Build Tools solely for formatting.
- Prefer `uv run --no-sync` or the existing environment only after verifying required runtime dependencies.
- Provide one complete PowerShell block for local actions.

## Verification

Canonical CI verification:

```powershell
uv sync --frozen --extra dev
uv run python scripts/verify_repo.py
```

Never claim a check passed unless it ran on the claimed HEAD.

## Workflow notifications

After every push or connector write that starts GitHub Actions:

1. identify the exact new HEAD and workflow run;
2. report `public-release-audit`, Ubuntu and Windows;
3. offer one opt-in completion notification tied to that exact run;
4. create it only after user acceptance;
5. disable it after completion or supersession.

The automation platform currently supports no more than hourly checks. Never claim 15-minute polling is configured.

## Completion report

Report:

- verified facts;
- corrected stale or cross-realm claims;
- files changed;
- exact checks and CI state;
- remaining evidence boundaries;
- next bounded task.
