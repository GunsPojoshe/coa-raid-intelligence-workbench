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

## Mission and truth model

Build a localhost-first raid intelligence system for Classless / Ascension WoW that produces explainable recommendations only from reproducible evidence.

```text
combat-log event = observation
combat-log event != automatic proof of a general mechanic
```

Only `corroborated` and `confirmed` mechanics may enter canonical planner scoring.

## Required start sequence

1. Inspect repository, branch, remote HEAD and working tree.
2. Inspect PR #7, its base and PR #3.
3. Inspect the latest CI run and all jobs.
4. Read the canonical context documents.
5. Compare documentation claims with code and versioned receipts.
6. Inspect local private artifacts before local-only decisions or captures.
7. Run relevant verification.
8. Report material discrepancies before changing analytical semantics.

Do not trust old commit, test, count, route or CI claims without checking.

## Current milestone

```text
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

## Completed E3 checkpoints

- verified Armory and public-report discovery mappings;
- report/encounter/combatants capture and persistence through migration `0008`;
- promoted public-report pagination limit `25`;
- exhaustive deduplicated public-report manifest;
- explicit verified Argentum identity decision;
- deterministic filtering by verified private source guild ID;
- scalar-free 17-report guild manifest;
- reviewed full-crawl collection contract;
- bounded guild-search route capture;
- explicit scalar-free route/schema review.

Do not repeat completed pagination, public manifest, identity decision, filtering, contract review or route/schema review unless a bound hash/fingerprint changes.

## Current exact evidence facts

```text
public manifest:
  reports: 6454
  unique report IDs: 6454
  integrity checks: 19/19

identity decision:
  integrity checks: 16/16
  guild identity verified: true

verified guild report manifest:
  selected reports: 17
  unique selected report IDs: 17
  integrity checks: 14/14

full-crawl contract:
  integrity checks: 12/12
  full crawl collection contract reviewed: true

route-semantics capture:
  attempts: 3
  completed attempts: 3
  HTTP 200: 3
  integrity checks: 13/13
  observed result counts: [1]

route/schema review:
  integrity checks: 22/22
  route template verified: true
  query shapes verified: true
  response schema verified: true
  limit parameter accepted: true
  ready for bounded limit-semantics capture: true
```

Versioned receipts:

```text
evidence/real-data/argentum-public-report-manifest.json
evidence/real-data/argentum-guild-identity-decision.json
evidence/real-data/argentum-guild-report-manifest.json
evidence/real-data/argentum-guild-full-crawl-contract.json
evidence/real-data/argentum-guild-route-semantics-capture.json
evidence/real-data/argentum-guild-route-semantics-review.json
```

## Current bounded sequence

1. design a bounded multi-result guild-search probe;
2. use a query expected to return more than one record;
3. compare at least two accepted `limit` values;
4. archive complete raw responses before interpretation;
5. publish only scalar-free counts, hashes, field inventories and schema fingerprints;
6. verify truncation behavior without inferring pagination or completeness;
7. keep full crawl, graph, performance and scoring closed;
8. only after separate pagination/termination/completeness proof compare an API-derived report set with the private 17-report baseline.

Current boundary:

```text
guild identity verified: true
guild filtering completed: true
full crawl collection contract reviewed: true
guild route template verified: true
guild query shapes verified: true
guild response schema verified: true
limit parameter accepted: true
ready for bounded limit-semantics capture: true
limit truncation semantics verified: false
pagination semantics verified: false
termination semantics verified: false
completeness verified: false
guild API route semantics verified: false
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
- Bind parsers and reviews to exact hashes/fingerprints.
- Unknown fingerprint means reject and review.
- Preserve contradicting evidence and failed requests.
- Route/schema verification does not prove limit truncation, pagination, termination or completeness.
- A one-result response cannot verify limit truncation behavior.
- Public receipts must not expose source guild ID, report IDs, query values, request URLs or raw rows.
- Partial results may not be marked complete.
- Full crawl requires explicit route/query, schema, pagination, termination, completeness and set-comparison evidence.

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

Never commit cookies, tokens, Authorization headers, browser profiles, `.env` secrets, unsanitized HAR, credentials, source guild IDs, report IDs or private packets.

## Database and collector rules

- Never edit a migration already published to branch history.
- Current migration range is `0001`–`0008`.
- Add a migration only for a demonstrated schema gap.
- Live-network behavior is not a unit test.
- Use deterministic fake responses in tests.
- Archive before interpretation.
- Write scalar-free receipts atomically.
- Preserve checkpoints on ordinary transport failure.

## Required verification

```powershell
uv sync --frozen --extra dev
uv run python scripts/verify_repo.py
```

Run focused tests and inspect exact Actions results. Never claim a check passed unless it ran.

## Completion report

Report verified facts, local-only observations, corrected stale claims, files changed, exact checks and CI state, remaining boundaries, and the next bounded task.
