# Continuation handoff — 2026-08-19

This is the durable restart point for a new ChatGPT/Codex session. It records the verified baseline,
non-obvious source facts, operator workflow, safety boundaries, the exact unresolved gates, and the split
between the canonical E3 path and the isolated E4 discovery experiment.

## Read first on resume

Always read:

```text
docs/PROJECT_STATE.md
docs/NEXT_CHAT_HANDOFF.md
docs/PARALLEL_WORKSTREAMS_2026-08-19.md
docs/SOURCE_OBSERVABILITY_AND_REANALYSIS.md
docs/SCOPE_SCHEMA_CYCLE.md
docs/CURRENT_REPORT_ANALYTICS_READ_MODELS.md
docs/CURRENT_REPORT_COMPARISON_READ_MODEL.md
docs/CURRENT_REPORT_ANALYTICS_API.md
docs/CROSS_REPORT_EQUIVALENCE.md
```

If continuing the E4 experiment, also read:

```text
docs/INTERACTIVE_HAR_DISCOVERY.md
```

Then check the live branch HEAD, PR state and exact-head CI. SHA values in this document are historical
checkpoints, not substitutes for live GitHub state.

## Branch / workstream topology

```text
main
└── e2/log-evidence-refactor        Draft PR #3 -> main
    └── e3/real-log-capture         Draft PR #7 -> e2/log-evidence-refactor
        └── e4/interactive-har-discovery
```

`e3/real-log-capture` is the canonical evidence/product line.

`e4/interactive-har-discovery` is an isolated UI -> Network discovery experiment. E4 may generate
candidate contracts, but unverified E4 conclusions must not silently redefine E3 semantics.

Important shared functional checkpoint:

```text
ac4e15b2fb4c879b2010c12dae1aeb50df3fd745
Record real equivalence blocker and add structure review
```

E3 later received the documentation/workstream split commit:

```text
e2a74553ecb091c0f325eed61aeb74360c1d6a9b
Document parallel E3 and interaction-HAR workstreams
```

Exact-head CI #853 for `e2a745...` succeeded. PR #7 is open, Draft and mergeable. Do not merge only
because CI is green; the current evidence promotion gates are intentionally unfinished.

## Working contract with the operator

- Perform GitHub, PR, CI, repository and documentation work autonomously whenever tooling permits.
- Ask the operator only for unavoidable Windows/local-runtime/browser/private-artifact actions.
- If local action is unavoidable, make it one compact demonstrative action. Complex PowerShell should be
  a downloadable `.ps1`; project Python remains the source of truth.
- Private/raw files are valid analysis inputs. Privacy is a publication/versioning boundary, not a reason
  to refuse inspection.
- Never delete or overwrite unknown/untracked operator files. A historical `e3-current-local.patch` may
  exist and is operator-owned unless explicitly stated otherwise.
- Do not offer completion-notification/button actions.
- Development cadence: focused tests -> coherent change -> one `verify_repo` -> one push -> exact-head CI.

Canonical checks:

```text
uv sync --frozen --extra dev --no-build-package ruff
uv run --no-sync python -m ruff check .
uv run --no-sync python -m ruff format --check .
uv run --no-sync python -m pytest
uv run --no-sync python scripts/verify_repo.py
```

## Product target and trust model

CoA-only, localhost-first, evidence-first raid intelligence platform.

Primary product question:

> Почему конкретный человек нужен именно текущему составу?

The system may automate discovery, immutable capture, structural diff, provenance, scoped invalidation
and deterministic reviewed transformations. It must not automatically infer gameplay mechanics, promote
planner trust, interpret unknown fields, or create performance scores because field names look plausible.

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
browser Network evidence.

Important active versions:

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

### Report detail / encounter catalog

Current report detail is additive relative to the old sample-specific mapping. Generic parsing must use
verified field contracts, not an old whole-payload field count or sample fingerprint.

Earlier private structural review observed encounter-catalog top-level `reportDifficulty` and encounter-row
`difficulty`. Those names are evidence candidates only; semantic equivalence has not been promoted.

### Combatants roster

The current roster contains character/spec/build/gear evidence. Across the first real corpus, every
snapshot had exact set equality among:

```text
resolved_ca_talent_ranks[].cao_id
hero_build values[].entry_id
talents.trees[].talents[].entry_id
```

The parser joins those structures only when exact equality holds and fails closed otherwise. Gear includes
resolved item/enchant/suffix/set/gem and BisBeard metadata, but this remains observation-only evidence.

### Throughput

Throughput series use dynamic numeric-key maps. Numeric keys are normalized structurally. A series key is
linked to a character only on exact equality with `characters[].character_id` in the same response.
Opaque keys remain opaque.

The first real report produced 12 throughput requests across three reviewed `metric + perspective`
profiles. Optional/null variation inside one profile motivated profile-cycle aggregation.

### Healing / damage taken

Healing provides spell rows and source/target breakdowns with explicit character-ID fields in some rows.
Damage-taken grouping keys remain opaque; an exact equality with a roster ID is only a structural exact-key
match, not proof that the key semantically means target character ID.

## Real milestones already proven

### First report: generic derived persistence

```text
derived observations: 2031
first run: inserted 2031 / matched 0
replay:    inserted 0    / matched 2031
```

Core canonical `report` / `encounter` tables are not mutated by this observation-only path.

### First report: combat analytics

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

### First report: comparison model

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

Throughput rank is only upstream `characters[].total_amount DESC` inside one exact request profile; it is
not a performance grade.

### Typed localhost/private API

```text
GET /api/current-report-analytics/reports
GET /api/current-report-analytics/latest
GET /api/current-report-analytics/reports/{report_id}
```

The API is read-only/private and performs no collection.

### Second independent report

```text
catalog reports: 1 -> 2
dynamic routes resolved: 6
derived inserted: 2920
analytics inserted: 28213
encounters: 55
roster characters: 27
throughput profiles: 33
throughput characters: 867
throughput points: 16907
```

All 16907 throughput points in that proof linked exactly to characters. Pending reanalysis remained 0.

### Structural cross-report benchmark

```text
reports: 2
input profiles: 45
candidate peer cohorts: 3
eligible peer cohorts: 3
ambiguous peer cohorts: 0
eligible profiles: 6
eligible ranked player rows: 133
single-report profile groups: 33
```

Current structural peer key:

```text
exact zone
+ exact encounter name
+ exact metric
+ exact perspective
```

Repeated matching profiles inside one report make that cohort ambiguous and exclude it from numeric use.

### Scope-aware Source Observatory repair

The second report exposed false schema evolution because different `reportId` scopes were compared as
sequential versions of one source object.

Before repair:

```text
open change events: 645
combatants-roster endpoint: 614
throughput endpoint: 16
pending reanalysis: 0
```

Real `scope-schema-cycle-v1` replay proved:

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

Raw objects, fetch observations, source captures and exact schema snapshots were preserved. The remaining
22 events are not automatically confirmed upstream changes.

## Current difficulty / encounter equivalence result

`cross-report-equivalence-review-v1` ran on the real two-report corpus:

```text
status: insufficient_evidence
reports: 2

report-detail difficulty observed: 0
public highest-difficulty observed: 0
cross-surface matches: 0
cross-surface mismatches: 0
ambiguous difficulty reports: 0
verified difficulty reports: 0

eligible structural cohorts: 3
difficulty-verified cohorts: 0
encounter-equivalence cohorts: 0
encounter non-unique cohorts: 0
```

Interpretation:

- This is an evidence gap, not proof that the two reports use different difficulty.
- Encounter-name uniqueness is not the blocker.
- Numeric cross-report scoring, cross-report player identity, fight-duration semantics, mechanic semantics
  and planner scoring remain blocked.

Public-safe receipt:

```text
evidence/real-data/coa-cross-report-equivalence-real.json
```

## Track A — canonical E3 next action

E3 already contains:

```text
src/coa_workbench/analytics/cross_report_source_structure.py
scripts/review_cross_report_source_structure.py
tests/unit/test_cross_report_source_structure.py
```

`cross-report-source-structure-v1` is read-only and scalar-safe. It reports fixed field names + JSON types
from existing persisted report-detail, encounter-row and public-report evidence while excluding IDs,
names, difficulty values, raw payloads/paths and private hashes.

A helper previously generated for the operator:

```text
review-cross-report-source-structure.ps1
SHA-256 a1ccea59cf111430e7a90542569203189e24d6aa9dc5e1d9dbde973769007d5b
```

The real source-structure receipt is still pending at this handoff point. **No new HAR is needed for
Track A yet.**

Direct command if needed:

```powershell
uv run --no-sync python scripts/review_cross_report_source_structure.py `
  --output "$HOME\Desktop\coa-cross-report-source-structure-real.json"
```

Interpret the result as follows:

```text
existing independent stable difficulty evidence exists
-> implement revised corroboration gate
-> synthetic + real proof

encounter-row difficulty exists but needs report-level corroboration
-> extend scalar-free review to encounter-catalog top-level reportDifficulty
-> prove stable same-report binding before semantic promotion

persisted evidence truly lacks an independent corroborator
-> only then request the smallest new Network observation that binds report identity + difficulty
```

Do not recapture a full current-report HAR merely to repeat already-proven transport/persistence.

After difficulty + encounter equivalence passes:

```text
prove fight-duration / comparison-unit semantics
-> guarded numeric cross-report benchmark
-> prove explicit cross-report character identity
-> character history / rankings / statistics
-> Armory/talent-grid enrichment
-> BisBeard planning evidence
-> planner scoring only from corroborated/confirmed mechanics
```

## Track B — isolated E4 interaction-HAR experiment

E4 intentionally permits a **new controlled interaction HAR** because its purpose is different from E3:
it is testing UI -> Network causality, not re-proving current-report persistence.

Read `docs/INTERACTIVE_HAR_DISCOVERY.md` for the exact protocol.

Core experiment:

```text
baseline reload
-> difficulty A
-> boss 1 / Summary
-> boss 2 / Summary
-> boss 3 / Summary
-> neighbouring tab/subpage
-> back to Summary
-> difficulty B
-> repeat selected bosses/Summary
```

Change one UI factor at a time and leave roughly 2-3 seconds between transitions. Save one HAR with
content plus an ordered action list and a few representative screenshots.

E4 should build reusable project Python that turns the HAR into an ordered differential model:

```text
HAR entries ordered by startedDateTime
-> action-window request bursts
-> path/query/body shape deltas
-> response structural deltas
-> repeated transition correlation
-> explicit network-silent transitions
```

Do not infer a contract from a UI label. A candidate should be repeatable and isolated from neighbouring
controls before it can be proposed back to E3.

Merge back from E4 only reviewed endpoint/parameter/profile contracts, deterministic parser/reviewer code,
focused tests, scalar-safe receipts and documentation. Never merge the raw HAR/screenshots/private IDs,
UI-label guesses, one-off report assumptions or unverified gameplay semantics.

## Public-safe real evidence index

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

Receipts are evidence, not permanent configuration. Do not hardcode their timestamped counts as source
contracts.

## Privacy boundary

Never publish HAR/raw bodies, report/encounter/player/guild IDs or names, query values, dynamic group
keys, source-capture IDs, scope/profile scalar values or hashes, difficulty scalar values, or private
input/output fingerprints.

Safe receipts may expose field names, scalar-free structure, counts, booleans, endpoint codes and
algorithm versions when these do not reveal private scalar identity.

Low-entropy hashes of private scalar values are not automatically safe.

## Things not to repeat

- Do not rebuild one-off report-specific parsers.
- Do not gate generic parsing on the original sample field count/fingerprint.
- Do not treat different report IDs as schema versions of one source object.
- Do not treat the remaining 22 Source Observatory events as confirmed site changes.
- Do not use character name as cross-report identity without a separate proof.
- Do not normalize totals by duration or calculate percentiles/grades until duration/unit semantics are
  proven.
- Do not promote planner scoring from schema names, talents, item metadata or one combat result.
- On E3, do not ask for the old/current-report HAR again unless the evidence decision tree truly reaches a
  missing source surface.
- On E4, do not confuse a deliberate interaction HAR experiment with E3's normal no-new-HAR default.

## Exact fresh-chat resume instructions

### Continue Track A / E3

```text
Read docs/PROJECT_STATE.md, docs/NEXT_CHAT_HANDOFF.md and
 docs/PARALLEL_WORKSTREAMS_2026-08-19.md from e3/real-log-capture.
Verify live PR #7 HEAD and exact-head CI.
Stay on E3. Do not use unverified E4 conclusions.
If coa-cross-report-source-structure-real*.json is available, analyze it first.
Otherwise the only pending local proof is scripts/review_cross_report_source_structure.py.
Continue from the difficulty evidence decision tree; do not restart source discovery.
```

### Continue Track B / E4

```text
Read docs/PROJECT_STATE.md, docs/NEXT_CHAT_HANDOFF.md,
docs/PARALLEL_WORKSTREAMS_2026-08-19.md and docs/INTERACTIVE_HAR_DISCOVERY.md
from e4/interactive-har-discovery.
Verify live E4 branch state before changes.
Stay on E4 and treat it as isolated discovery.
Prepare/analyze the controlled interaction HAR and ordered action list.
Return only corroborated contracts/parsers/tests/scalar-safe evidence toward E3.
```
