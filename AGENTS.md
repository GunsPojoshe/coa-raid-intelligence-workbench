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
6. inspect required local private artifacts before local-only decisions or captures;
7. run relevant verification;
8. report material discrepancies before changing analytical semantics.

Do not trust old commit, test, count, route or CI claims without checking.

## Current milestone

```text
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

## Completed E3 checkpoints

- verified Armory and public-report discovery mappings;
- report/encounter/combatants capture;
- report/encounter normalization, reconstruction and persistence;
- combatants persistence through migration `0008`;
- promoted public-report pagination limit `25`;
- exhaustive deduplicated public-report manifest;
- snapshot and independent guild identity review;
- explicit operator guild identity decision;
- deterministic filtering by verified private source guild ID;
- scalar-free 17-report guild manifest;
- reviewed full-crawl collection contract bound to the three public receipts.

Do not repeat completed pagination, public manifest, identity decision, guild filtering or contract review unless a bound hash/fingerprint changes.

## Current exact evidence facts

```text
public manifest:
  reports: 6454
  unique report IDs: 6454
  integrity checks: 19/19

identity decision:
  integrity checks: 16/16
  guild identity verified: true
  ready for guild filtering: true

verified guild report manifest:
  selected reports: 17
  unique selected report IDs: 17
  integrity checks: 14/14
  report IDs published: false

full-crawl contract:
  integrity checks: 12/12
  full crawl collection contract reviewed: true
  ready for bounded route-semantics capture: true
  guild API route semantics verified: false
  ready for full guild crawl: false
```

Versioned receipts:

```text
evidence/real-data/argentum-public-report-manifest.json
evidence/real-data/argentum-guild-identity-decision.json
evidence/real-data/argentum-guild-report-manifest.json
evidence/real-data/argentum-guild-full-crawl-contract.json
```

## Current bounded sequence

1. perform bounded guild API route-semantics capture under the reviewed contract;
2. record exact route and query parameters without inventing semantics;
3. archive complete raw response before interpretation;
4. bind payload SHA-256 and schema fingerprint;
5. inventory collection shape, fields, nullability and pagination structure;
6. verify termination and completeness before promoting full crawl;
7. compare any API-derived report set with the private verified 17-report baseline;
8. preserve missing, extra and conflicting reports;
9. keep graph, performance and scoring closed.

Current boundary:

```text
guild identity verified: true
guild filtering completed: true
guild report manifest deduplicated: true
full crawl collection contract reviewed: true
ready for bounded route-semantics capture: true
guild API route semantics verified: false
automatic full guild crawl allowed: false
ready for full guild crawl: false
ready for multi-report character graph: false
ready for performance model: false
ready for BiS 25 scoring: false
planner scoring allowed: false
```

## Trust rules

- Never invent routes, parameters, fields, IDs, pagination or provider semantics.
- Probe and fingerprint real payloads before mappings.
- Bind parsers and reviews to exact hashes/fingerprints.
- Unknown fingerprint means reject and review.
- Keep `raw_log`, `upstream_derived`, `companion_addon`, `local_inference` and `manual_override` distinct.
- Preserve contradicting evidence.
- Parser correctness, identity verification, filtering and contract review do not promote mechanic trust.
- Explicit operator promotion must remain distinct from automatic evidence checks.

## Guild collection rules

- Public receipts must not expose source guild ID, report IDs or raw report rows.
- Filtering must use exact typed equality with the source guild ID loaded from the private decision.
- Preserve source-manifest order and reject duplicate report IDs.
- The 17-report manifest is the verified comparison baseline.
- Route candidates are not verified route semantics.
- Full crawl requires explicit route/query, schema, pagination, termination, completeness and set-comparison evidence.
- Partial results may not be marked complete.
- Preserve failed requests and discrepancies as observations.

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

Never commit cookies, tokens, Authorization headers, browser profiles, `.env` secrets, unsanitized HAR, credentials, source guild IDs, report IDs or private packets.

## Database migrations

- Never edit a migration already published to branch history.
- Current migration range is `0001`–`0008`.
- Add a migration only for a demonstrated schema gap.
- Test clean temporary DuckDB initialization twice.

## Collector rules

- Live-network behavior is not a unit test.
- Use deterministic fake responses in tests.
- Archive before interpretation.
- Validate exact receipt, payload hash and schema fingerprint.
- Write scalar-free receipts atomically.
- Keep private outputs local and gitignored.
- Preserve checkpoints on ordinary transport failure.

## Required verification

```powershell
uv sync --frozen --extra dev
uv run python scripts/verify_repo.py
```

Run focused tests and inspect exact Actions results. Never claim a check passed unless it ran.

## Completion report

Report verified facts, local-only observations, corrected stale claims, files changed, exact checks and CI state, remaining boundaries, and the next bounded task.

Do not describe parser correctness, identity verification, filtering or contract review as confirmed gameplay knowledge.