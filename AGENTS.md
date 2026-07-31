# CoA Raid Intelligence — Agent Instructions

These instructions apply to the entire repository.

## Canonical context

Read in this order:

1. `AGENTS.md`;
2. `docs/PROJECT_MASTER_CONTEXT.md`;
3. `docs/PROJECT_STATE.md`;
4. `docs/CONTINUATION_PROMPT.md`;
5. relevant ADR/capture/review documents;
6. `evidence/real-data/README.md`.

Documentation never replaces checking GitHub, code, local private artifacts and CI.

## Mission

Build a localhost-first raid intelligence system for Classless / Ascension WoW that produces explainable recommendations only from reproducible evidence.

```text
combat-log event = observation
combat-log event != automatic proof of a general mechanic
```

Only `corroborated` and `confirmed` mechanics may enter canonical planner scoring.

## Required start sequence

Before changing code:

1. inspect branch, HEAD and working tree;
2. inspect PR #7, its base and PR #3;
3. inspect latest CI and exact failures;
4. read canonical context documents;
5. compare claims with code and versioned receipts;
6. run relevant verification;
7. report material discrepancies before changing analytical semantics.

Do not trust old commit, test or count claims without checking.

## Current milestone

```text
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

Completed in E3:

- verified Armory and public-report discovery mappings;
- report/encounter/combatants capture;
- report/encounter normalization, reconstruction and persistence;
- combatants review, promotion and immutable persistence through migration `0008`;
- deterministic combatants parser and actor/build read models;
- promoted public-report pagination limit `25`;
- verified terminal contract and exhaustive public-report manifest.

Current bounded sequence:

1. review the private manifest rows for the 17 exact `Argentum` label matches;
2. verify whether their single non-null source guild ID is the operator target identity;
3. emit a scalar-free guild-identity review receipt;
4. only after explicit identity promotion, enable deterministic guild filtering;
5. capture selected guild reports and build a multi-report character graph;
6. continue aura and independent supporting/contradicting evidence work;
7. integrate only corroborated/confirmed mechanics into scoring.

Do not repeat completed pagination, manifest or combatants persistence stages unless a bound hash changes.

## Current exact evidence facts

Public manifest receipt:

```text
file: evidence/real-data/argentum-public-report-manifest.json
route: /api/reports/public
limit: 25
pages: 259
reports: 6454
unique report IDs: 6454
duplicates: 0
terminal page reports: 4
integrity checks: 19/19
exact Argentum label reports: 17
distinct non-null guild IDs for exact label: 1
guild identity verified: false
ready for guild identity review: true
```

Combatants persistence receipt:

```text
file: evidence/real-data/observed-combatants-info-persistence.json
migration: 0008_combatants_observation_persistence
persisted observations: 1343
actor/build observations: 1339
linked actors: 11
integrity checks: 14/14
core actor mutations: 0
```

## Trust rules

- Never invent routes, parameters, fields, IDs, pagination or provider semantics.
- Probe and fingerprint real payloads before mappings.
- Bind parsers to exact reviewed hashes/fingerprints.
- Unknown fingerprint means reject and review.
- Keep `raw_log`, `upstream_derived`, `companion_addon`, `local_inference` and `manual_override` distinct.
- Preserve contradicting evidence.
- Keep global mechanics separate from guild/player execution.
- Parser correctness does not promote mechanic trust.
- A guild label and a repeated guild ID are evidence for review, not automatic identity confirmation.

## Combatants rules

- Persisted combatants records are immutable parser observations.
- Do not mutate core `actor` rows from addon-derived fields.
- Do not claim semantic uniqueness for nested IDs, slots or display names.
- Companion-addon provenance and gameplay meaning remain unverified.
- Read-model availability does not permit planner scoring.

## Public manifest and guild identity rules

- The exhaustive manifest is verified only for the captured time boundary and exact hashes.
- The private manifest contains source scalar values and stays local-only.
- Git may contain the scalar-free receipt only.
- Do not expose the observed guild ID in documentation or receipts unless an explicit review policy permits it.
- Do not enable guild filtering from name matching alone.
- Identity promotion requires a reviewed private packet and a scalar-free decision receipt.

## Raw data and privacy

Versioned:

- code/tests;
- migrations;
- reviewed mappings;
- documentation;
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

Never commit cookies, tokens, Authorization headers, browser profiles, `.env` secrets, unsanitized HAR, credentials, or absolute local paths containing usernames.

Never modify archived raw payloads to make tests pass.

## Database migrations

- Never edit a migration already published to branch history.
- Current migration range is `0001`–`0008`.
- Add a migration only for a demonstrated schema gap.
- Test clean temporary DuckDB initialization twice.
- Preserve deterministic checksums and repeatability.

## Collector rules

- Live-network behavior is not a unit test.
- Use deterministic fake responses in tests.
- Use bounded real capture only after deterministic tests pass.
- Archive before interpretation.
- Validate exact receipt, payload hash and schema fingerprint.
- Write scalar-free receipts atomically.
- Keep private outputs local and gitignored.

## Required verification

```powershell
uv sync --frozen --extra dev
uv run python scripts/verify_repo.py
```

Additionally run focused tests, CLI smoke checks, clean/repeated DuckDB initialization for storage changes, and inspect exact Actions logs for CI failures.

Never claim a check passed unless it ran.

## User interaction

The user prefers autonomous GitHub work, one complete PowerShell block for unavoidable local actions, full code without omissions, direct answers, and explicit verified/observed/candidate/planned distinctions.

## Completion report

Report verified facts, local-only observations, corrected stale claims, files/migrations changed, exact checks and CI state, remaining boundaries, and the next bounded task.

Do not describe scaffolding, parser correctness or schema mapping as confirmed gameplay knowledge.
