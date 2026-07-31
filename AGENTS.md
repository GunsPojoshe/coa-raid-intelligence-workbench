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

1. inspect repository, branch, remote HEAD and working tree;
2. inspect PR #7, its base and PR #3;
3. inspect the latest CI run and all jobs;
4. read the canonical context documents;
5. compare documentation claims with code and versioned receipts;
6. inspect required local private artifacts before local-only decisions or filtering;
7. run relevant verification;
8. report material discrepancies before changing analytical semantics.

Do not trust old commit, test, count, route or CI claims without checking.

## Current milestone

```text
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

Recheck actual HEAD and CI before every task.

## Completed E3 checkpoints

- verified Armory and public-report discovery mappings;
- report/encounter/combatants capture;
- report/encounter normalization, reconstruction and persistence;
- combatants review, promotion and immutable persistence through migration `0008`;
- deterministic combatants parser and actor/build read models;
- promoted public-report pagination limit `25`;
- exhaustive deduplicated public-report manifest;
- snapshot identity review for the 17 `Argentum` rows;
- profiled asset recovery and guild-route candidate inventory;
- guild-search response capture through the reviewed SPA fetch context;
- guild-search schema inventory and reviewed four-field mapping;
- explicit operator guild identity decision;
- deterministic filtering by the verified private source guild ID;
- scalar-free deduplicated guild report manifest containing 17 selected reports.

Do not repeat completed pagination, public manifest, snapshot review, route discovery, schema inventory, mapping review, identity decision, guild filtering or combatants persistence unless a bound hash/fingerprint changes.

## Current bounded sequence

1. review and promote a full-crawl collection contract separately from identity/filtering;
2. verify exact guild API route parameters, response contract, pagination and completeness semantics before using it for full crawl;
3. compare any guild-API-derived report set with the verified 17-report public-manifest filter;
4. preserve discrepancies and contradicting evidence;
5. begin bounded per-report report/encounter/combatants capture only under the reviewed contract;
6. build a multi-report character identity graph after stable identifiers are reviewed;
7. continue aura and supporting/contradicting evidence work;
8. admit only `corroborated` and `confirmed` mechanics to planner scoring.

Current boundary:

```text
guild identity verified: true
guild filtering completed: true
guild report manifest deduplicated: true
selected guild reports: 17
full crawl collection contract reviewed: false
guild API route semantics verified: false
ready for full guild crawl: false
ready for multi-report character graph: false
ready for performance model: false
ready for BiS 25 scoring: false
planner scoring allowed: false
```

## Current exact evidence facts

Public manifest:

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
```

Identity decision:

```text
file: evidence/real-data/argentum-guild-identity-decision.json
integrity checks: 16/16
independent source identity verified: true
guild identity verified: true
ready for guild filtering: true
contains raw payload: false
contains source scalar values: false
```

Verified guild report manifest:

```text
file: evidence/real-data/argentum-guild-report-manifest.json
source reports: 6454
selected reports: 17
unique selected report IDs: 17
duplicate selected occurrences: 0
integrity checks: 14/14
guild filtering completed: true
report IDs published: false
source guild ID published: false
ready for full guild crawl: false
```

Combatants persistence:

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
- Bind parsers and reviews to exact hashes/fingerprints.
- Unknown fingerprint means reject and review.
- Keep `raw_log`, `upstream_derived`, `companion_addon`, `local_inference` and `manual_override` distinct.
- Preserve contradicting evidence.
- Keep global mechanics separate from guild/player execution.
- Parser correctness does not promote mechanic trust.
- Identity verification and filtering do not verify route semantics, crawl completeness, character identity, performance or scoring.
- Explicit operator promotion must remain distinct from automatic evidence checks.

## Guild identity and filtering rules

- Public receipts must not expose raw guild ID, report IDs or raw records.
- Name matching alone cannot enable filtering.
- Filtering must use exact typed equality with the verified source guild ID loaded from the private decision.
- Preserve source-manifest order and reject duplicate selected report IDs.
- Private manifests and private decisions remain local-only.
- The 17-report manifest is a verified filtered snapshot, not authorization for full guild crawl.

## Combatants rules

- Persisted combatants records are immutable parser observations.
- Do not mutate core `actor` rows from addon-derived fields.
- Do not claim semantic uniqueness for nested IDs, slots or display names.
- Companion-addon provenance and gameplay meaning remain unverified.
- Read-model availability does not permit planner scoring.

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

Never commit cookies, tokens, Authorization headers, browser profiles, `.env` secrets, unsanitized HAR, credentials, raw source scalars, private report IDs or absolute local paths containing usernames.

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
- Preserve checkpoints on ordinary transport failure.
- Refresh discovery state only for classified temporal or binding drift.

## Required verification

```powershell
uv sync --frozen --extra dev
uv run python scripts/verify_repo.py
```

Additionally run focused tests, CLI smoke checks, clean/repeated DuckDB initialization for storage changes, and inspect exact Actions results for CI claims.

Never claim a check passed unless it ran.

## User interaction

The user prefers autonomous GitHub work, one complete PowerShell block for unavoidable local actions, full code without omissions, direct answers, and explicit verified/observed/candidate/planned distinctions.

## Completion report

Report verified facts, local-only observations, corrected stale claims, files/migrations changed, exact checks and CI state, remaining boundaries, and the next bounded task.

Do not describe scaffolding, parser correctness, schema mapping, identity verification or filtering as confirmed gameplay knowledge.