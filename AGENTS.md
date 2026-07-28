# CoA Raid Intelligence — Agent Instructions

These instructions apply to the entire repository. Read them before changing code.

## Canonical context

Read in this order:

1. `AGENTS.md`;
2. `docs/PROJECT_MASTER_CONTEXT.md`;
3. `docs/PROJECT_STATE.md`;
4. `docs/CONTINUATION_PROMPT.md`;
5. relevant ADR and capture documents.

`PROJECT_MASTER_CONTEXT.md` contains the full product and architecture context. `PROJECT_STATE.md` contains mutable operational facts. Neither replaces checking GitHub, code and CI.

## Mission

Build a localhost-first raid intelligence system for Classless / Ascension WoW that derives explainable planning recommendations from evidence captured from `coa.ascensionlogs.gg`.

Keep these layers separate:

1. immutable raw observations;
2. upstream-derived fields;
3. canonical normalized events;
4. deterministic local reconstruction;
5. locally inferred hypotheses;
6. supporting and contradicting evidence;
7. corroborated or confirmed mechanics;
8. planner scoring and recommendations.

A combat-log event is an observation. It is not automatic proof of a general game mechanic.

## Mandatory first step

Before modifying code:

1. inspect the current branch, HEAD and working tree;
2. inspect the active pull request and base branch;
3. inspect the latest CI run and exact failures;
4. read the canonical context documents;
5. compare documented claims with actual implementation;
6. run available verification commands;
7. report discrepancies before extending the analytical model.

Do not trust old commit counts, test counts, branch state or implementation claims without checking them.

## Current milestone

The active branch is `e3/real-log-capture`, PR #7 into `e2/log-evidence-refactor`.

The parent evidence branch is `e2/log-evidence-refactor`, PR #3 into `main`.

Both remain Draft until their acceptance criteria are met unless the user explicitly changes this instruction.

Current bounded sequence:

1. restore green Ruff/CI baseline;
2. implement endpoint-isolated and progressive Armory capture;
3. capture missing real `character` and `talent-grid` payloads;
4. inventory and fingerprint those payloads;
5. create reviewed mappings only after structural review;
6. automate bounded report discovery;
7. normalize a complete report/encounter/roster slice;
8. expand supporting and contradicting evidence;
9. integrate only corroborated/confirmed mechanics into planner scoring.

Update this section when the project moves to a new branch or phase.

## Source and data-trust rules

- `coa.ascensionlogs.gg` is the primary observation source.
- Never invent source routes, request parameters, JSON fields, event types, spell mappings, class mappings or pagination behavior.
- Probe and fingerprint a real payload before creating a mapping.
- Normalization requires an explicitly verified mapping and a matching schema fingerprint.
- Keep `raw_log`, `upstream_derived`, `companion_addon`, `local_inference` and `manual_override` provenance distinct.
- Preserve contradicting evidence.
- Keep global mechanics separate from guild and player execution.
- Only `corroborated` and `confirmed` mechanics may participate in canonical planner scoring.
- Historical static catalogs are `legacy_unverified` and non-canonical.
- A verified normalizer behavior does not corroborate a gameplay mechanic.

## Verified HTTP finding

The full versioned request profile `coa-fetch-context-v1` has returned HTTP 200 for public reports, character search and Armory by-name routes:

```text
Accept: application/json, text/plain, */*
Accept-Language: en-US,en;q=0.9
Cache-Control: no-cache
Pragma: no-cache
User-Agent: Chromium-like
Referer: https://coa.ascensionlogs.gg/
Sec-Fetch-Dest: empty
Sec-Fetch-Mode: cors
Sec-Fetch-Site: same-origin
```

Do not overstate it:

- only the complete profile is verified;
- the minimum required subset is unknown;
- cookie and request-order dependencies are not isolated;
- Armory-first behavior in a completely fresh session is not proven;
- old 403 responses do not prove authorization-only, browser-only or TLS-fingerprint-only access.

Implementation requirements:

- one persistent same-origin session/opener;
- in-memory cookies only;
- no cookie or header values in output metadata;
- record profile version and safe header names;
- HAR remains fallback, not a primary requirement.

## Raw data and privacy

- Raw payloads are immutable and content-addressed by SHA-256.
- Repeated retrieval of the same payload creates another observation, not another payload body.
- Never commit cookies, authorization headers, access tokens or unsanitized HAR files.
- Never commit browser profiles, local DuckDB files or private raw payloads.
- Never commit absolute local paths containing usernames.
- Do not modify archived raw payloads to make tests pass.
- Cookies may exist only in process memory.

## Automated report capture

The intended design is not manual download and per-file parsing.

```text
public report discovery
-> verified filters and pagination
-> bounded deterministic selection, normally up to 5 reports per category
-> encounter discovery
-> selected analytical endpoints
-> immutable archive
-> fingerprint
-> endpoint/schema parser
-> canonical normalization
```

Prefer specialized payloads over a full event stream. Download the full event stream only when compact endpoint data cannot test the current temporal or causal hypothesis.

Many similar raw files are expected. Implement one versioned parser per reviewed endpoint/schema. Unknown fingerprints must be rejected and queued for review.

## Database migrations

- Never edit a migration already published to branch history.
- Add a new migration for every schema correction.
- Test migrations on a clean temporary DuckDB database.
- Test repeatability and checksum behavior.
- Keep migrations deterministic and independent of external network access.

## Aura State Engine

Before building scope, overwrite, stacking or order-sensitive inference, verify:

- normal apply/remove;
- refresh;
- stack changes;
- missing remove;
- duplicate events;
- out-of-order events;
- two sources;
- two targets;
- encounter-end closure;
- observed-window boundaries.

Do not silently discard anomalies. Return or persist them with deterministic reason codes.

The real `Ninja's Focus` checkpoints verify normalizer and interval reconstruction behavior only. They do not confirm numeric effect, stacking, overwrite, provider equivalence or strategic criticality.

## Collector development rules

- Live-network tests must not be unit tests.
- Use deterministic fake openers/responses for unit coverage.
- Use bounded real capture only after deterministic tests pass.
- Prefer endpoint-isolated capture over a long all-or-nothing chain.
- Write progressive safe result state after each endpoint.
- Make capture resumable where practical.
- Do not re-fetch already archived successful payloads without a reason.
- Treat HTTP status and completed body capture as separate facts.
- Preserve transport warnings without treating partial invalid bytes as valid evidence.

## Development scope

- Complete one bounded analytical slice at a time.
- Do not mix unrelated UI redesign with evidence-pipeline work.
- Do not perform broad refactors unless required by current acceptance criteria.
- Do not create speculative CoA Logs mappings or mechanics.
- Heavy analytics belongs in Python, not frontend JavaScript.
- Algorithms, mappings, policies, HTTP profiles and inference outputs must be versioned.
- Results must carry provenance and reproducibility identifiers.
- Temporary diagnostic workflows should become tested production code or manual-only probes.

## Required verification

Use the locked environment when possible:

```bash
uv sync --frozen --extra dev
```

Run the repository verifier:

```bash
uv run python scripts/verify_repo.py
```

Run change-specific tests when the verifier does not isolate changed behavior.

For migration/storage changes, initialize a clean temporary database twice.

For CLI changes, run `--help` and a deterministic smoke test.

For collector changes, use fake-opener tests and one bounded real capture.

Never claim a test passed unless it actually ran. If a check cannot run, state the exact reason and what ran instead.

Local `uv run --no-sync` targeted tests are useful diagnostics but do not replace locked full verification.

## Git and concurrent work

- Do not overwrite unrelated user or agent changes.
- Re-check branch and remote state before publishing.
- Avoid concurrent writes to the same files.
- Keep commits coherent and bounded.
- Leave the working tree clean.
- Do not add private local data to a commit.

## User interaction

The user prefers:

- autonomous GitHub work;
- one complete PowerShell block for local actions;
- full code without omissions;
- direct answers;
- no unnecessary manual steps;
- explicit verified/observed/planned distinctions.

Do not request broad manual testing before the evidence pipeline reaches the agreed checkpoint. Narrow local capture is acceptable when private data must remain local and the corresponding collector path is already implemented and tested.

## Completion report

Every completed task reports:

- what was verified;
- local-only observations;
- outdated or incorrect prior claims;
- files changed;
- migrations added;
- exact commands executed;
- exact tests and results;
- CI state;
- remaining limitations;
- next bounded task.

Do not describe scaffolding, parser correctness or schema mapping as confirmed gameplay knowledge.
