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
6. inspect required local private artifacts before running local-only decisions;
7. run relevant verification;
8. report material discrepancies before changing analytical semantics.

Do not trust old commit, test, count, route or CI claims without checking.

## Current milestone

```text
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

Implementation baseline before the current documentation refresh:

```text
HEAD: 297895c5ce3b26ce2911befd9addf474ef3e1138
Verify repository run: #464
public-release-audit: success
Ubuntu: success
Windows: success
```

Recheck the actual HEAD and CI because documentation commits may have advanced the branch.

## Completed E3 checkpoints

- verified Armory and public-report discovery mappings;
- report/encounter/combatants capture;
- report/encounter normalization, reconstruction and persistence;
- combatants review, promotion and immutable persistence through migration `0008`;
- deterministic combatants parser and actor/build read models;
- promoted public-report pagination limit `25`;
- exhaustive deduplicated public-report manifest;
- local snapshot identity review for the 17 `Argentum` rows;
- profiled asset recovery and guild-route candidate inventory;
- guild-search response capture through the reviewed SPA fetch context;
- guild-search schema inventory;
- reviewed mapping of `id`, `name`, `realm` and `report_count`;
- cross-endpoint identity candidate linking the manifest candidate and the single guild-search result;
- explicit identity-decision implementation requiring `--promote-identity`.

Do not repeat completed pagination, manifest, snapshot review, route discovery, schema inventory, mapping review or combatants persistence unless a bound hash/fingerprint changes.

## Current bounded sequence

1. run the explicit local guild identity decision with `scripts/decide_guild_identity.py --promote-identity`;
2. upload only `data/exchange/out/argentum-guild-identity-decision.json`;
3. validate that the receipt is scalar-free and bound to the exact public/private evidence chain;
4. version the receipt only after successful review;
5. update documentation and PR #7 boundary to `guild_identity_verified=true` only if the receipt proves it;
6. implement deterministic filtering by the verified source guild ID;
7. produce a deduplicated guild report manifest;
8. begin bounded per-report capture and multi-report character identity work.

Until the decision receipt exists and is reviewed:

```text
guild identity verified: false
ready for guild filtering: false
ready for full guild crawl: false
ready for multi-report character graph: false
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

Snapshot identity review:

```text
file: evidence/real-data/argentum-guild-identity-snapshot-review.json
exact label reports: 17
candidate guild-ID reports: 17
conflicting non-empty names: 0
integrity checks: 10/10
snapshot internal identity consistent: true
```

Independent guild-search chain:

```text
profiled asset bytes: 3881146
API route candidates: 79
guild route candidates: 3
guild search results: 1
schema field entries: 5
mapped semantic fields: 4
source-ID matches: 1
name casefold matches: 1
cross-endpoint identity candidate observed: true
ready for guild identity decision review: true
```

Reviewed mapping:

```text
$.guilds[].id           -> guild_id
$.guilds[].name         -> guild_name
$.guilds[].realm        -> realm
$.guilds[].report_count -> report_count
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
- A label, repeated ID or cross-endpoint candidate is not automatic identity promotion.
- Explicit operator promotion must remain distinct from automatic evidence checks.

## Guild identity rules

- The public manifest is verified only for its captured time boundary and exact hashes.
- The private manifest and private review packets remain local-only.
- Public receipts must not expose the raw guild ID or raw payload.
- Name matching alone cannot enable filtering.
- Snapshot consistency plus independent search evidence creates a reviewable candidate, not a verified identity.
- Identity promotion requires the explicit CLI flag and a reviewed scalar-free decision receipt.
- Identity verification may enable filtering only; it does not verify guild API route semantics, full crawl, character identity, performance or scoring.

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

Never commit cookies, tokens, Authorization headers, browser profiles, `.env` secrets, unsanitized HAR, credentials, raw source scalars or absolute local paths containing usernames.

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

Do not describe scaffolding, parser correctness, schema mapping or an unpromoted identity candidate as confirmed gameplay knowledge.