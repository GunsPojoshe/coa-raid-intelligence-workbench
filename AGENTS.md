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

1. Inspect repository, branch, remote HEAD and working tree.
2. Inspect PR #7, its base and PR #3.
3. Inspect the latest GitHub Actions run and every job.
4. Read the canonical context documents in the order above.
5. Compare documentation claims with code, migrations and versioned receipts.
6. Inspect required local private artifacts before any local-only decision or network capture.
7. Run focused deterministic tests before bounded real capture.
8. Report material discrepancies before changing analytical semantics.

Do not trust old commit, CI run, test count, hash, route, source count or readiness claim without checking.

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
- explicit scalar-free route/schema review;
- bounded multi-result limit capture implementation and deterministic tests.

Do not repeat completed pagination, public manifest, identity decision, filtering, contract review or route/schema review unless a bound hash/fingerprint changes.

## Exact completed evidence facts

```text
report/encounter:
  normalized: 2 reports, 15 encounters, 31 actors, 31 participants, 0 aura events
  reconstructed: 1 report, 14 encounters, 31 actors, 31 participants
  persisted through 0007: 77 observations

combatants:
  persisted through 0008: 1343 observations
  actor/build observations: 1339
  linked actors: 11
  integrity checks: 14/14

public manifest:
  reports: 6454
  unique report IDs: 6454
  integrity checks: 19/19

identity/filtering:
  identity checks: 16/16
  guild identity verified: true
  selected reports: 17
  unique selected report IDs: 17
  filter checks: 14/14

full-crawl contract:
  integrity checks: 12/12
  contract reviewed: true
  private comparison baseline: 17 reports

route capture:
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

## Implemented current probe

```text
src/coa_workbench/collector/guild_limit_semantics_capture.py
scripts/capture_guild_limit_semantics.py
tests/unit/test_guild_limit_semantics_capture.py
```

The probe performs exactly three bounded requests:

```text
private query + low limit
private query + high limit
private query + identical high-limit repeat
```

A capture is ready for separate limit review only when:

- all three responses are complete and valid;
- response schema is stable;
- low-limit result count equals the low limit;
- high-limit result count is greater than low and does not exceed high;
- the high-limit repeat has the same ordered-record and source-ID-order hashes;
- the low-limit source-ID hash sequence is an exact prefix of the high-limit sequence.

The capture implementation must never publish the query, request URLs, source IDs, raw records or error text. A successful capture sets only `ready_for_limit_semantics_review=true`; it must leave `limit_truncation_semantics_verified=false` until a separate review receipt exists.

## Current bounded sequence

1. Confirm green CI on the current HEAD.
2. Select a privacy-safe private query expected to return multiple guild records.
3. Run the bounded multi-result limit capture locally.
4. Upload only the scalar-free public capture receipt.
5. Validate the receipt and version it if privacy/integrity checks pass.
6. Implement and run a separate deterministic limit-semantics review.
7. Version the scalar-free limit review only after explicit promotion.
8. Separately prove pagination, termination and completeness.
9. Compare any future API-derived report set with the private 17-report baseline.
10. Preserve matching, missing, extra and conflicting partitions.
11. Keep full crawl, character graph, performance model and scoring closed until their own gates pass.

## Current boundary

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
- Archive complete response bytes before interpretation.
- Bind parsers and reviews to exact hashes/fingerprints.
- Unknown fingerprint means reject and review.
- Preserve contradicting evidence and failed requests.
- Accepted parameter does not prove its semantics.
- Route/schema verification does not prove limit truncation, pagination, termination or completeness.
- A one-result response cannot verify limit truncation behavior.
- Public receipts must not expose source guild IDs, report IDs, query values, request URLs, raw rows or error text.
- Partial results may not be marked complete.
- Full crawl requires explicit route/query, schema, limit, pagination, termination, completeness and set-comparison evidence.
- Parser correctness, identity verification, filtering and collection review do not confirm gameplay mechanics.

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

Never commit cookies, tokens, Authorization headers, browser profiles, `.env` secrets, unsanitized HAR, credentials, source guild IDs, report IDs, private queries or private packets.

## Database and collector rules

- Never edit a migration already published to branch history.
- Current migration range is `0001`–`0008`.
- Add a migration only for a demonstrated schema gap.
- Live-network behavior is not a unit test.
- Use deterministic fake responses in tests.
- Archive before interpretation.
- Write scalar-free receipts atomically.
- Preserve checkpoints on ordinary transport failure.
- Keep retries and response sizes bounded.
- Use same-origin HTTPS and no credentials for public-source probes.

## Required verification

```powershell
uv sync --frozen --extra dev
uv run python scripts/verify_repo.py
```

Run focused tests and inspect exact Actions results. Never claim a check passed unless it ran on the claimed HEAD.

## Completion report

Report verified facts, local-only observations, corrected stale claims, files changed, exact checks and CI state, remaining boundaries, and the next bounded task.
