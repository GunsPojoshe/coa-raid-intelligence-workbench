# CoA Raid Intelligence — Agent Instructions

These instructions apply to the entire repository. Read them before changing code.

## Canonical context

Read in this order:

1. `AGENTS.md`;
2. `docs/PROJECT_MASTER_CONTEXT.md`;
3. `docs/PROJECT_STATE.md`;
4. `docs/CONTINUATION_PROMPT.md`;
5. relevant ADR/capture/review documents;
6. `evidence/real-data/README.md`.

Documentation does not replace checking GitHub, code, local receipts and CI.

## Mission

Build a localhost-first raid intelligence system for Classless / Ascension WoW that derives explainable planning recommendations from evidence captured from `coa.ascensionlogs.gg`.

A combat-log event is an observation, not automatic proof of a general game mechanic.

## Required start sequence

Before modifying code:

1. inspect current branch, HEAD and working tree;
2. inspect active PR and base branch;
3. inspect latest CI run and exact failures;
4. read canonical context documents;
5. compare documentation with implementation and versioned receipts;
6. run relevant verification;
7. report material discrepancies before changing analytical semantics.

Do not trust old commit/test counts without checking.

## Current milestone

```text
main
└── e2/log-evidence-refactor        PR #3 -> main, Draft
    └── e3/real-log-capture         PR #7 -> e2, Draft
```

Completed in E3:

- verified Armory mappings;
- verified public-report discovery mapping;
- exact report/encounter/combatants capture;
- published report and encounter mappings;
- selected-parser normalization;
- deterministic reconstruction;
- selected-parser persistence through migration `0007`;
- combatants deep review, field selection, design and candidate extraction.

Current bounded sequence:

1. manually validate/promote the exact combatants candidate extraction;
2. persist six immutable observation types atomically and idempotently;
3. add deterministic observation read models;
4. investigate and normalize aura endpoints for the bounded report slice;
5. gather independent supporting and contradicting evidence;
6. integrate only corroborated/confirmed mechanics into planner scoring.

Do not repeat already completed capture, selection or mapping-design stages unless a hash/fingerprint changes.

## Source and trust rules

- Never invent routes, parameters, JSON fields, event types, Spell IDs, pagination or provider semantics.
- Probe and fingerprint real payloads before creating mappings.
- Bind every parser to exact reviewed hashes/fingerprints.
- Unknown fingerprint means reject and review.
- Keep `raw_log`, `upstream_derived`, `companion_addon`, `local_inference` and `manual_override` distinct.
- Preserve contradicting evidence.
- Keep global mechanics separate from guild/player execution.
- Only `corroborated` and `confirmed` mechanics may enter canonical planner scoring.
- Parser/mapping correctness does not promote mechanic trust.

## Current exact report-slice facts

```text
report_detail
payload:     161739896f0b8321f884bcc24d1896efb894a9c6e05166269189f9871c64cba9
fingerprint: 3d533a4178b67957bbd31544ddf5484bd5959635ebd5edcdd0c7689a4bace216

encounter_detail
payload:     955437d6c9c287cc7db280dd2388b88603af2785508061b95c7811dcd272fe22
fingerprint: 567f36824efb37a29b835df01ce9b1fcc79eae57d6230202d16a6265c6ca0e85

combatants_info
payload:     45672e0f0ff9eb461c575bdd38385795daa6326378bc3f8ad51474276140dc14
fingerprint: 41d6d15422c668f83d2ccae1ec0ff2969671861f9e43b21cb371578961c5f8ff
```

Published report/encounter mappings:

```text
config/mappings/coa_report_detail_v1.json
config/mappings/coa_encounter_detail_v1.json
```

Current persisted selected-parser slice:

```text
1 report
14 encounters
31 actors
31 participants
77 canonical entity observations
0 rejects
```

Current combatants candidate extraction:

```text
1350 source matches
1343 output observations
7 deduplicated instance-context matches
11 actor links
12/12 integrity checks
0 core mutations
```

## Combatants persistence rules

- The six design units target immutable `canonical_entity_observation` records.
- Do not mutate core `actor` rows from candidate addon-derived fields.
- Require exact private extraction SHA-256 and versioned receipt validation.
- Preserve raw match path/selected record hash identity for nested rows.
- Do not claim semantic uniqueness for `cao_id`, `entry_id`, gear slot or display names.
- Promotion must be manual and parser-only.
- Keep companion-addon provenance and nested semantics unverified.

## Raw data and privacy

The user permits full use of local private data for development. Git remains minimal by default.

Versioned:

- code/tests;
- migrations;
- reviewed mappings;
- docs;
- scalar-free receipts.

Local-only paths:

```text
data/raw/
data/warehouse/
data/normalized/
data/reconstructed/
data/extracted/
data/exchange/in/
data/exchange/out/
```

Never commit:

- cookies, tokens or Authorization headers;
- browser profiles;
- `.env` secrets;
- unsanitized HAR;
- credentials;
- absolute local paths containing usernames.

Never modify archived raw payloads to make tests pass.

## Database migrations

- Never edit a migration already published to branch history.
- Add a new migration only for a demonstrated schema gap.
- Test on a clean temporary DuckDB twice.
- Preserve deterministic checksums and repeatability.
- Prefer existing migration `0007` for combatants observations when it can represent required provenance without loss.

## Collector/extractor rules

- Live-network behavior is not a unit test.
- Use deterministic fake responses/payloads for tests.
- Use bounded real capture only after deterministic tests pass.
- Treat status receipt and completed body read as separate facts.
- Archive before interpretation.
- Validate exact manifest, payload hash and schema fingerprint.
- Write scalar-free receipts atomically.
- Private output files must remain local and gitignored.

## Development scope

- Complete one bounded analytical slice at a time.
- Do not mix unrelated UI redesign with evidence work.
- Do not broadly refactor without acceptance need.
- Heavy analytics belongs in Python.
- Version parsers, mappings, policies, migrations and inference outputs.
- Carry provenance and reproducibility identifiers.

## Required verification

```powershell
uv sync --frozen --extra dev
uv run python scripts/verify_repo.py
```

Additionally:

- run focused tests for changed behavior;
- run CLI `--help` and deterministic smoke tests for CLI changes;
- initialize a clean DuckDB twice for migration/storage changes;
- inspect exact Actions logs for CI failures.

Never claim a check passed unless it ran.

## Git rules

- Re-check branch and remote before publishing.
- Do not overwrite unrelated work.
- Keep commits coherent and bounded.
- Do not use `git add -A` on a mixed worktree.
- Leave the working tree clean except intentional gitignored private data.

## User interaction

The user prefers:

- autonomous GitHub work;
- one complete PowerShell block for unavoidable local actions;
- full code without omissions;
- direct answers;
- no repeated requests for already supplied facts;
- explicit verified/observed/candidate/planned distinctions.

## Completion report

Report:

- verified facts;
- local-only observations;
- outdated claims corrected;
- files/migrations changed;
- exact checks and CI state;
- remaining boundaries;
- next bounded task.

Do not describe scaffolding, parser correctness or schema mapping as confirmed gameplay knowledge.
