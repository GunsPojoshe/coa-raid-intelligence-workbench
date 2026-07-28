# CoA Raid Intelligence — Agent Instructions

These instructions apply to the entire repository. Read them before changing code.

## Mission

Build a localhost-first raid intelligence system for Classless / Ascension WoW that derives explainable planning recommendations from evidence captured from `coa.ascensionlogs.gg`.

The system keeps these layers separate:

1. immutable raw observations;
2. upstream-derived fields;
3. canonical normalized events;
4. locally inferred hypotheses;
5. supporting and contradicting evidence;
6. corroborated or confirmed mechanics;
7. planner scoring and recommendations.

A combat-log event is an observation. It is not automatic proof of a general game mechanic.

## Mandatory first step

Before modifying code:

1. inspect the current branch, HEAD and working tree;
2. inspect the active pull request and its base branch when available;
3. read `README.md`, `docs/PROJECT_STATE.md`, `docs/CONTINUATION_PROMPT.md` and relevant ADR files;
4. compare documented claims with the actual implementation;
5. inspect the latest CI runs;
6. run the available verification commands;
7. report any discrepancy before extending the analytical model.

Do not trust commit counts, test counts, branch state or implementation claims from old prompts without checking them.

## Current milestone

The active real-log capture branch is `e3/real-log-capture` and its pull request is PR #7 into `e2/log-evidence-refactor`.

The parent evidence PR is PR #3 from `e2/log-evidence-refactor` into `main`. Both remain Draft until their acceptance criteria are met unless the user explicitly changes this instruction.

The current bounded implementation sequence is:

1. centralize the verified same-origin fetch-context HTTP profile;
2. keep one persistent cookie jar/opener for a same-host request chain;
3. add Armory HTTP and collector unit tests;
4. repeat real Armory capture for detail, captures and talent-grid payloads;
5. inventory and fingerprint those payloads before mapping;
6. automate report discovery and bounded endpoint capture;
7. normalize a complete real report/encounter/roster slice;
8. expand supporting and contradicting evidence;
9. run the full verifier and cross-platform CI.

Update this section when the project moves to a new branch or phase.

## Source and data-trust rules

- `coa.ascensionlogs.gg` is the primary source of observations.
- Never invent source routes, request parameters, JSON fields, event types, spell mappings, class mappings or pagination behavior.
- Probe and fingerprint a real payload before creating a mapping.
- Normalization requires an explicitly verified mapping and a matching schema fingerprint.
- Keep `raw_log`, `upstream_derived`, `companion_addon`, `local_inference` and `manual_override` provenance distinct.
- Preserve contradicting evidence. Never delete it because a preferred hypothesis exists.
- Keep global game mechanics separate from guild and individual-player execution quality.
- Recent evidence may receive more weight, but old observations remain stored.
- Only `corroborated` and `confirmed` mechanics may participate in canonical planner scoring.
- Historical static catalogs are non-canonical and must not enter planner scoring.
- A verified normalizer behavior does not by itself corroborate a game mechanic.

## Verified HTTP-access finding

The following full request profile has been observed to return HTTP 200 for public reports, character search and Armory by-name routes:

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

Do not overstate this result:

- only the complete profile and tested sequence are verified;
- the minimum required subset is not yet isolated;
- the diagnostic sequence requested public reports before the Armory endpoints;
- one cookie existed after the first successful API response;
- it is not yet proven whether Armory succeeds as the first request in a fresh session;
- do not describe the source as authorization-only, browser-only or TLS-fingerprint-only based on earlier 403 responses.

When implementing the profile:

- version it;
- use one persistent same-host session/opener;
- keep cookies in memory only;
- never log or archive cookie values;
- record only profile version and safe header names;
- retain the HAR path only as a fallback, not the primary requirement.

## Raw data and privacy

- Raw payloads are immutable and content-addressed by SHA-256.
- Repeated retrieval of the same payload creates another observation, not another payload body.
- Never commit cookies, authorization headers, access tokens or unsanitized HAR files.
- Never commit browser profiles, local DuckDB files or private raw payloads.
- Do not commit private player information unless it is intentionally sanitized and documented as a test fixture.
- Do not modify an archived raw payload to make a test pass.
- Cookies may exist only in process memory and must not appear in output metadata.

## Automated report capture

The intended design is not manual download and per-file parsing.

```text
public report discovery
→ verified filters and pagination
→ bounded selection, normally up to 5 reports per category
→ encounter discovery
→ selected analytical endpoints
→ immutable archive
→ fingerprint
→ endpoint/schema parser
→ canonical normalization
```

Prefer specialized payloads over a full event stream. Download the full event stream only when compact endpoint data cannot test the current temporal or causal hypothesis.

Many similar raw files are expected. Implement one versioned parser per reviewed endpoint/schema, not one parser per file. Unknown fingerprints must be rejected and queued for review.

## Database migrations

- Never edit a migration that has already been published to branch history.
- Add a new migration for every schema correction.
- Test migrations on a clean temporary DuckDB database.
- Test migration repeatability and checksum behavior.
- Keep migrations deterministic and independent of external network access.

## Aura State Engine

Before building scope, overwrite, stacking or order-sensitive inference, verify at least:

- normal apply/remove;
- refresh;
- stack changes;
- missing remove;
- duplicate events;
- out-of-order events;
- two sources;
- two targets;
- encounter-end closure;
- observed-window start and end boundaries.

Do not silently discard anomalies. Return or persist them with deterministic reason codes.

The confirmed technical aura checkpoint for `Ninja's Focus` verifies normalizer and interval reconstruction behavior only. It does not confirm the effect's numeric description, stacking, overwrite, provider equivalence or strategic criticality.

## Development scope

- Complete one bounded analytical slice at a time.
- Do not mix unrelated UI redesign with evidence-pipeline work.
- Do not perform broad refactors unless required by the current acceptance criteria.
- Do not create speculative CoA Logs mappings or mechanics to unblock development.
- Heavy analytics belongs in Python, not frontend JavaScript.
- Algorithms, mappings, policies, HTTP profiles and inference outputs must be versioned.
- Results must carry provenance and enough identifiers to reproduce them.
- Temporary diagnostic workflows should be removed or reduced to manual dispatch after their behavior is integrated into tested production code.

## Required verification

Use the locked environment when possible:

```bash
uv sync --frozen --extra dev
```

Run the repository verifier:

```bash
uv run python scripts/verify_repo.py
```

Run change-specific tests when the full verifier does not isolate the changed behavior.

For migration or storage changes, initialize a clean temporary database and run initialization again to verify repeatability:

```bash
uv run coa-workbench init-db --database <temporary-path>/coa.duckdb --migrations migrations
```

For CLI changes, run the affected command's `--help` and a deterministic smoke test.

For collector changes, use deterministic fake-opener tests and a bounded real capture. Do not make unit tests depend on live network access.

Never claim a test passed unless it was actually executed. If a check cannot run, state the exact reason and what was run instead.

## Git and concurrent work

- Do not overwrite unrelated user or agent changes.
- Before committing, re-check the branch and remote state.
- If the selected base branch changed while a task was running, refresh safely before publishing.
- Avoid multiple concurrent write tasks touching the same files.
- Keep commits limited to one coherent block.
- Leave the working tree clean when a task is complete.

## User involvement checkpoint

Do not request broad manual user testing before the evidence pipeline reaches the agreed checkpoint. Narrow local capture commands are acceptable when the raw data must remain private and the agent has already implemented and verified the corresponding collector path.

The full checkpoint requires:

1. a real CoA Logs JSON or HAR captured immutably;
2. its schema fingerprint recorded;
3. a verified mapping;
4. one complete report and encounter normalized;
5. actors, participants and aura events linked;
6. aura intervals reconstructed;
7. at least one repeatable mechanic with independent supporting evidence;
8. contradicting evidence checked;
9. the result reproducible and visible with provenance.

## Completion report

Every completed task reports:

- what was verified;
- what previous claim was false, incomplete or outdated;
- files changed;
- migrations added;
- exact commands executed;
- exact test results;
- remaining limitations;
- the next bounded task.

Do not hide uncertainty and do not describe scaffolding as confirmed game knowledge.
