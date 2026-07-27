# CoA Raid Intelligence — Agent Instructions

These instructions apply to the entire repository. Read them before changing code.

## Mission

Build a localhost-first raid intelligence system for Classless / Ascension WoW that derives explainable planning recommendations from evidence captured from `coa.ascensionlogs.gg`.

The system must keep these layers separate:

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
3. read `README.md` and relevant files under `docs/`;
4. compare documented claims with the actual implementation;
5. run the available verification commands;
6. report any discrepancy before extending the analytical model.

Do not trust commit counts, test counts, branch state or implementation claims from old prompts without checking them.

## Current milestone

The active evidence-refactor branch is `e2/log-evidence-refactor` and its pull request is PR #3 into `main`.

PR #3 must remain Draft until the evidence checkpoint is complete. Do not merge it, mark it ready, or delete the branch unless the user explicitly changes this instruction.

This milestone information must be updated when the project moves to a new branch or phase.

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

## Legacy data

Excel-derived effect and provider data is `legacy_unverified`.

It may be used only for migration audits, forensic comparison and regression investigation. It must not participate in canonical scoring by default.

The environment flag `COA_ENABLE_LEGACY_EFFECTS=1` enables legacy analytics only for forensic comparison. Results remain non-canonical.

## Raw data and privacy

- Raw payloads are immutable and content-addressed by SHA-256.
- Repeated retrieval of the same payload creates another observation, not another payload body.
- Never commit cookies, authorization headers, access tokens or unsanitized HAR files.
- Do not commit private player information unless it is intentionally sanitized and documented as a test fixture.
- Do not modify an archived raw payload to make a test pass.

## Database migrations

- Never edit a migration that has already been published to the branch history.
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
- encounter-end closure.

Do not silently discard anomalies. Return or persist them with deterministic reason codes.

## Development scope

- Complete one bounded analytical slice at a time.
- Do not mix unrelated UI redesign with evidence-pipeline work.
- Do not perform broad refactors unless required by the current acceptance criteria.
- Do not create speculative CoA Logs mappings or mechanics to unblock development.
- Heavy analytics belongs in Python, not frontend JavaScript.
- Algorithms, mappings, policies and inference outputs must be versioned.
- Results must carry provenance and enough identifiers to reproduce them.

## Required verification

Use the locked environment when possible:

```bash
uv sync --frozen --extra dev
```

Run the checks relevant to the change, including at minimum:

```bash
uv run pytest
uv run coa-workbench doctor --project-root .
```

For migration or storage changes, initialize a clean temporary database and run initialization again to verify repeatability:

```bash
uv run coa-workbench init-db --database <temporary-path>/coa.duckdb --migrations migrations
```

For CLI changes, run the affected command's `--help` and a deterministic smoke test.

Never claim a test passed unless it was actually executed. If a check cannot run, state the exact reason and what was run instead.

## Git and concurrent work

- Do not overwrite unrelated user or agent changes.
- Before committing, re-check the branch and remote state.
- If the selected base branch changed while a task was running, refresh or rebase safely before publishing.
- Avoid multiple concurrent write tasks touching the same files.
- Keep commits limited to one coherent block.
- Leave the working tree clean when a task is complete.

## User involvement checkpoint

Do not request manual user testing before the evidence pipeline reaches the agreed checkpoint:

1. a real CoA Logs JSON or HAR has been captured immutably;
2. its schema fingerprint is recorded;
3. a verified mapping exists;
4. one report and encounter are normalized;
5. actors, participants and aura events are linked;
6. aura intervals are reconstructed;
7. at least one repeatable mechanic has independent supporting evidence;
8. contradicting evidence has been checked;
9. at least one legacy discrepancy has been documented;
10. the result is reproducible and visible with provenance.

## Completion report

Every completed task must report:

- what was verified;
- what previous claim was false, incomplete or outdated;
- files changed;
- migrations added;
- exact commands executed;
- exact test results;
- remaining limitations;
- the next bounded task.

Do not hide uncertainty and do not describe scaffolding as confirmed game knowledge.
