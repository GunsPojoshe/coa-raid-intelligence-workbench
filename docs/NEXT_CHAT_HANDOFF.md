# Continuation handoff — 2026-08-19

This file is the durable restart point for a new ChatGPT/Codex session. It records the current verified
state, non-obvious source facts, operator workflow, safety boundaries and the exact next decision tree.

If this branch has moved after this snapshot, first inspect commits after the implementation checkpoint
below and update this handoff before making product changes.

## Read first on resume

Read these files before changing code:

```text
docs/PROJECT_STATE.md
docs/SOURCE_OBSERVABILITY_AND_REANALYSIS.md
docs/CURRENT_REPORT_ANALYTICS_READ_MODELS.md
docs/CURRENT_REPORT_COMPARISON_READ_MODEL.md
docs/CURRENT_REPORT_ANALYTICS_API.md
docs/SCOPE_SCHEMA_CYCLE.md
docs/CROSS_REPORT_EQUIVALENCE.md
docs/NEXT_CHAT_HANDOFF.md
```

The public-safe real receipts under `evidence/real-data/` are evidence, not configuration.

## Git / PR checkpoint

Repository:

```text
GunsPojoshe/coa-raid-intelligence-workbench
```

Active branch stack:

```text
main
└── e2/log-evidence-refactor        Draft PR #3 -> main
    └── e3/real-log-capture         Draft PR #7 -> e2/log-evidence-refactor
```

Implementation checkpoint before this documentation snapshot:

```text
ac4e15b2fb4c879b2010c12dae1aeb50df3fd745
Record real equivalence blocker and add structure review
```

Documentation snapshot commit:

```text
0988e93bddf8e0e95c735502b02d30e9997f9ab5
Document exact continuation state and next evidence gates
```

Exact-head CI for the implementation checkpoint: Verify repository #835, all three jobs successful:

```text
ubuntu
windows
public-release-audit
```

PR #7 is open, Draft and mergeable. Do not merge merely because CI is green; the E3 product/evidence
boundary is still intentionally under construction.

## Working contract with the operator

These conventions are part of the project workflow:

- Perform GitHub, PR, CI, repository and documentation work autonomously whenever connector/tools allow.
- Ask the operator only for unavoidable Windows/local-runtime/browser/private-artifact actions.
- When local action is unavoidable, make it one compact, demonstrative action. Complex PowerShell should
  be provided as a downloadable `.ps1`; project Python remains the source of truth.
- Private/raw files are valid analysis inputs. Privacy is a publication/versioning boundary, not a reason
  to refuse to inspect them.
- Do not ask for HAR by default. The regular handoff is a scalar/public-safe JSON receipt. Ask for a HAR
  only when a genuinely new or changed source contract cannot be understood from existing persisted
  evidence.
- Never delete or overwrite unknown/untracked local files. A historical untracked
  `e3-current-local.patch` may exist and must be preserved.
- Do not offer a completion-notification/button action.
- Development rhythm: focused tests -> coherent change -> one `verify_repo` -> one push -> exact-head CI.

Canonical verification commands:

```text
uv sync --frozen --extra dev --no-build-package ruff
uv run --no-sync python -m ruff check .
uv run --no-sync python -m ruff format --check .
uv run --no-sync python -m pytest
uv run --no-sync python scripts/verify_repo.py
```

## Product target

CoA-only, localhost-first, evidence-first raid intelligence platform.

Primary product question:

> Почему конкретный человек нужен именно текущему составу?

The system must remain generic across new reports, bosses, phases, fields and source contracts. It may
automate source discovery, immutable capture, structural diff, provenance, scoped invalidation and
replay of reviewed deterministic transformations. It must not automatically infer game mechanics,
promote planner trust, interpret unknown fields, or create scores because a field name looks plausible.

## Canonical current-report runtime

Six current browser/network source families are real-observed and registered:

```text
GET /api/reports/{reportId}
GET /api/reports/{reportId}/encounters?includeTrash=...
GET /api/reports/{reportId}/combatants-roster?encounterIds=...
GET /api/reports/{reportId}/encounters/{encounterId}/throughput-timeline?...
GET /api/reports/{reportId}/character_damage_taken_abilities?...
GET /api/reports/{reportId}/character_spell_healing?...
```

Historical encounter-detail/combatants-info routes remain evidence only and do not override current
Network evidence.

Current important implementation versions:

```text
network-source-cycle-v9
scope-schema-cycle-v1
current-report-derived-persistence-v1
current-report-analytics-v1
current-report-analytics-persistence-v1
current-report-comparison-read-model-v1
cross-report-structural-benchmark-v1
cross-report-equivalence-review-v1
cross-report-source-structure-v1
```

## Non-obvious source facts already learned

Do not rediscover these unless the source changes.

### Report detail / encounter catalog

Current report detail is additive relative to the old sample-specific mapping. Generic parsing must use
verified field contracts, not an old whole-payload field count or sample fingerprint.

Earlier private structural review observed the encounter-catalog response with top-level fields including
`reportDifficulty`, while encounter rows themselves include a `difficulty` field. These names are safe to
record, but their semantic equivalence has **not** been promoted. The first difficulty gate deliberately
required stronger cross-surface corroboration and failed due missing usable scalar evidence for the two
persisted reports.

### Combatants roster

The current roster contains character/spec/build/gear evidence. Across the first real corpus, every
snapshot had exact set equality among:

```text
resolved_ca_talent_ranks[].cao_id
hero_build values[].entry_id
talents.trees[].talents[].entry_id
```

The parser joins those talent structures only when that exact equality holds. It fails closed on a
mismatch. Gear observations include resolved item/enchant/suffix/set/gem and BisBeard metadata, but these
remain observation-only and do not establish mechanic semantics.

### Throughput

Current throughput is a dynamic numeric-key map. Numeric object keys are normalized structurally, while
private values remain private. Within a report/profile, series keys may link to characters only on exact
ID equality with `characters[].character_id` from the same response. No semantic inference from an
opaque key is allowed.

The first real report produced 12 throughput requests. Private evidence showed three reviewed
`metric + perspective` profiles; optional/null variation inside one profile was the reason profile-cycle
aggregation was introduced.

### Healing / damage taken

Healing has spell rows plus source/target breakdowns with explicit character-ID fields in some rows.
Damage-taken dynamic grouping keys are preserved as opaque keys; an exact equality with a roster ID may
be reported as a structural exact-key match, but that does not prove the key semantically means target
character ID.

## Real milestones already proven

### First report: generic derived persistence

```text
derived observations: 2031
first run: inserted 2031 / matched 0
replay:    inserted 0    / matched 2031
```

Entity families include report, encounter, roster character, roster snapshot, talent entry and gear slot
observations. Core canonical `report`/`encounter` tables are not mutated by this observation-only path.

### First report: combat analytics persistence

```text
analytics observations: 19660
throughput requests:       12
throughput characters:    299
throughput points:      13244
damage-taken rows:        852
healing spell rows:       178
healing source rows:     1624
healing target rows:     3451
```

Immediate replay inserted 0 and matched all 19660. Six report-scoped analytics dependencies were
registered.

### First report: comparison read model

Real read-model proof:

```text
reports:                       1
encounters:                   19
roster characters:           25
throughput profiles:         12
ranked player rows:         296
unmatched throughput rows:    3
throughput points:        13244
exact point-character links: 13244
opaque throughput groups:     0
```

Throughput rank is only `upstream characters[].total_amount DESC` inside one exact request profile. It
is not a performance grade.

### Typed localhost/private API

Implemented read-only endpoints:

```text
GET /api/current-report-analytics/reports
GET /api/current-report-analytics/latest
GET /api/current-report-analytics/reports/{report_id}
```

The API performs no collection and returns local/private models behind fail-closed safety flags.

### Second independent report

A second report passed the same generic pipeline without parser forks:

```text
catalog reports: 1 -> 2
dynamic routes resolved: 6

derived inserted: 2920
analytics inserted: 28213

encounters:             55
roster characters:      27
throughput profiles:    33
throughput characters: 867
throughput points:   16907
```

All 16907 throughput points in that proof received exact character links. Pending reanalysis remained 0.

### Structural cross-report benchmark

Two persisted reports produced:

```text
input profiles:                 45
candidate peer cohorts:          3
eligible peer cohorts:           3
ambiguous peer cohorts:          0
eligible profiles:               6
eligible ranked player rows:   133
single-report profile groups:   33
```

Current structural peer key:

```text
exact zone
+ exact encounter name
+ exact metric
+ exact perspective
```

Repeated matching profiles inside one report make a cohort ambiguous and exclude it from numeric use.

### Scope-aware Source Observatory repair

The second report exposed false schema evolution because different `reportId` scopes were compared as
sequential versions of one source object.

Before repair:

```text
open change events: 645
combatants-roster endpoint: 614
throughput endpoint:         16
pending reanalysis:           0
```

`scope-schema-cycle-v1` made the reviewed path scope part of the schema peer boundary. Real replay of the
existing second-report corpus proved:

```text
member events superseded:              619
legacy profile events superseded:        4
total false/legacy events superseded:  623
new aggregate scoped schema changes:     0
open change events:                 645 -> 22
pending reanalysis:                   0 -> 0
active dependencies:                 21 -> 21
completed analysis runs:              6 -> 6
```

Raw objects, raw fetch observations, source captures and exact schema snapshots were preserved. Do not
call the remaining 22 signals confirmed upstream changes; their provenance still needs separate review.

## Current difficulty / encounter equivalence state

`cross-report-equivalence-review-v1` was run against the real two-report local corpus and returned:

```text
status: insufficient_evidence
reports: 2

report-detail difficulty observed: 0
public highest-difficulty observed: 0
cross-surface matches:             0
cross-surface mismatches:          0
ambiguous difficulty reports:      0
verified difficulty reports:       0

eligible structural cohorts:       3
difficulty-verified cohorts:       0
encounter-equivalence cohorts:     0
encounter non-unique cohorts:      0
```

Interpretation:

- This does **not** show different difficulty. It shows that the attempted two-surface corroboration had
  no usable scalar evidence for these two reports.
- Encounter-name uniqueness is not the blocker: `encounter_non_unique_cohort_count = 0`.
- Numeric cross-report scoring, player identity, fight-duration semantics, mechanic semantics and planner
  scoring remain false/blocked.

Public-safe receipt:

```text
evidence/real-data/coa-cross-report-equivalence-real.json
```

## Code already prepared for the next probe

At implementation checkpoint `ac4e15b...` the following was added:

```text
src/coa_workbench/analytics/cross_report_source_structure.py
scripts/review_cross_report_source_structure.py
tests/unit/test_cross_report_source_structure.py
```

`cross-report-source-structure-v1` is read-only and scalar-safe. It reports fixed field names and JSON
types from already persisted report-detail, encounter-row and public-report evidence while excluding
IDs, names, difficulty values, raw payloads/paths and private hashes.

The helper previously generated for the operator is:

```text
review-cross-report-source-structure.ps1
SHA-256 a1ccea59cf111430e7a90542569203189e24d6aa9dc5e1d9dbde973769007d5b
```

It invokes the project Python script. **It has not yet produced a real receipt in this snapshot.**

No new HAR is needed for this probe.

## Exact next action

1. Obtain the real `cross-report-source-structure-v1` result from the existing local DuckDB/raw archive.
   If the operator still has the helper, run it; otherwise regenerate a thin helper or directly run:

```powershell
uv run --no-sync python scripts/review_cross_report_source_structure.py `
  --output "$HOME\Desktop\coa-cross-report-source-structure-real.json"
```

2. Inspect only the returned field names/types. Pay special attention to:

```text
report detail: difficulty-like fields
encounter rows: difficulty-like fields
public report rows: difficulty-like fields
```

Also remember the earlier private structural observation of encounter-catalog top-level
`reportDifficulty`. The current source-structure v1 output inspects encounter **row** fields, not that
response top-level field. If row evidence is insufficient, extend the structure reviewer to inspect the
encounter-catalog top-level shape before requesting any new browser capture.

3. Choose the next difficulty rule based on evidence, not names:

- If two existing independently bound surfaces expose one stable scalar difficulty for each target report
  and they agree, implement a revised corroboration gate and prove it synthetic + real.
- If encounter-row `difficulty` is present, first prove it is internally stable for the report and seek an
  independent report-level corroborator (for example the observed top-level `reportDifficulty`) before
  promoting semantics.
- If existing persisted evidence truly lacks an independent corroborator, only then request the smallest
  new Network observation that exposes explicit report identity + difficulty. Do not capture another full
  HAR merely to repeat already-proven transport/persistence behavior.

4. After difficulty + encounter equivalence is real-proven, implement a separate fight-duration /
comparison-unit gate. Candidate observed timing surfaces include encounter timing/duration fields and
throughput `duration_ms`; verify exact encounter linkage and units across surfaces before converting totals
into cross-report rates or scores.

5. Only after the comparison-unit gate passes may a guarded numeric cross-report benchmark be enabled.
Then, in order:

```text
explicit cross-report character identity from stable source evidence
-> character history / rankings / statistics
-> Armory/talent-grid enrichment
-> BisBeard planning evidence
-> planner scoring only from corroborated/confirmed mechanic semantics
```

## Public-safe real evidence index

Important receipts currently in Git:

```text
evidence/real-data/coa-current-report-private-structure-review.json
evidence/real-data/coa-current-report-profile-replay-v3-review.json
evidence/real-data/coa-current-report-derived-persistence-real.json
evidence/real-data/coa-current-report-scoped-cycle-real.json
evidence/real-data/coa-current-report-analytics-real.json
evidence/real-data/coa-current-report-comparison-real.json
evidence/real-data/coa-second-report-generalization-real.json
evidence/real-data/coa-cross-report-structural-real.json
evidence/real-data/coa-scope-schema-cycle-real.json
evidence/real-data/coa-cross-report-equivalence-real.json
```

Do not turn timestamped counts from receipts into permanent source configuration.

## Privacy and trust boundary

Never publish HAR/raw bodies, report/encounter/player/guild IDs or names, query values, dynamic group
keys, source-capture IDs, scope/profile scalar values or hashes, difficulty scalar values, or private
input/output fingerprints.

Safe public receipts may publish field names, scalar-free structure, counts, booleans, endpoint codes and
algorithm/version names when they do not reveal private scalar identity.

Low-entropy hashes of private values are not automatically safe. Prefer scalar-free structural
fingerprints; high-entropy input/capture fingerprints remain local unless specifically safe-reviewed.

## Things not to repeat

- Do not ask for the old/current-report HAR again for the already-proven report slice.
- Do not rebuild one-off report-specific parsers.
- Do not gate generic parsing on the original sample field count/fingerprint.
- Do not treat different report IDs as schema versions of the same object.
- Do not treat the remaining 22 Source Observatory events as confirmed site changes.
- Do not use character name as cross-report identity without a separate identity proof.
- Do not normalize totals by duration or calculate percentiles/grades until duration/unit semantics are
  explicitly proven.
- Do not promote planner scoring from schema names, talent names, item metadata, or one combat result.

## First actions in a new chat

On a fresh session:

```text
1. Read this handoff and PROJECT_STATE.
2. Fetch PR #7 / branch e3/real-log-capture and verify current HEAD + exact-head CI.
3. If HEAD is newer than the implementation checkpoint, inspect intervening commits first.
4. If the operator supplies coa-cross-report-source-structure-real*.json, analyze it immediately.
5. Otherwise the only pending local proof is the read-only source-structure review above.
6. Continue from the difficulty evidence decision tree; do not return to source discovery unless the
   evidence actually requires a new source surface.
```
