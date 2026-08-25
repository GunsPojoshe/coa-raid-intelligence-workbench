# Фактическое состояние проекта

Дата актуализации: **2026-08-26**.

Canonical restart order:

```text
AGENTS.md
docs/DOCUMENTATION_INDEX.md
docs/CURRENT_PARADIGM.md
docs/PROJECT_MASTER_CONTEXT.md
docs/PROJECT_STATE.md
docs/OFFICIAL_PUBLIC_API.md
docs/CONTINUATION_PROMPT.md
```

## GitHub / workstreams

```text
main
└── e2/log-evidence-refactor        Draft PR #3 -> main
    └── e3/real-log-capture         Draft PR #7 -> e2
        └── e4/interactive-har-discovery  Draft PR #9 -> e3
```

The lower staged integration debt is separate from the active E4 workstream. Do not merge Draft PRs merely to clear UI warnings and do not blindly choose an older canonical-document side during conflict resolution.

Always re-check live state; stored SHAs/run numbers are checkpoints only.

## Product state

CoA-only localhost-first evidence-first raid intelligence.

Primary question:

> **Почему конкретный человек нужен именно текущему составу?**

Planner scoring remains blocked until its required semantics are independently proven.

## Current paradigm

```text
official documented public API
-> official documented site semantics
-> pinned executable Companion source
-> persisted first-party report/API evidence
-> narrow browser/network fallback
-> structural inference last
```

This supersedes the old Browser-first/difficulty-first operating priority.

## Official API — real evidence + implemented normalization path

Contract:

```text
OpenAPI 3.1.0
API version 1.0.0
stats:read: /phases, /bosses, /statistics
```

Real public-safe evidence:

```text
phase records: 3
active/current candidate: 1
boss records: 285
unique stable boss_id values: 285
/statistics capture: HTTP 200, archived
statistics top-level entries: 21
statistics max depth: 5
objects with documented metric fields: 83
statistics normalization ready: true
```

Canonical real receipts currently present:

```text
evidence/real-data/coa-public-api-catalog-real.json
evidence/real-data/coa-public-api-statistics-capture-real.json
evidence/real-data/coa-public-api-statistics-shape-real.json
```

Implementation now present and deterministic-test verified:

```text
src/coa_workbench/normalizer/public_api_statistics.py
src/coa_workbench/collector/public_api_archive.py
src/coa_workbench/storage/public_api_statistics.py
src/coa_workbench/analytics/public_api_population_priors.py
migrations/0013_public_api_statistics.sql
scripts/persist_public_api_statistics.py
```

It provides:

```text
exact fail-closed parser for the reviewed aggregate shape
private request-scope provenance for new captures
normalized batch/class/spec persistence
analysis_run + raw_object artifact dependency
insert-or-match replay semantics
population-prior read model by documented dimensions
scalar-safe persistence/replay receipt generation
```

### Real replay gate: why a new capture is required

The historical real `/statistics` observation stored query **keys** only. Its request included `role`, but the response does not echo `role`; therefore the exact requested role value cannot be reconstructed from archived provenance.

Do not infer it from the capture CLI default. The parser fails closed and requires a bounded recapture instead.

New captures now keep exact prepared query values only in **private RawArchive observation metadata**. Public receipts still contain no query values or source scalar values.

Current real-evidence gate:

```text
one new bounded /statistics capture
-> parse/persist against the new private request provenance
-> persist the same archived capture twice
-> prove insert-or-match idempotence
-> emit/review scalar-safe persistence receipt
```

The old capture remains valid structural evidence; only full scope-aware persistence proof needs recapture.

## Official API credential boundary

Default local key file:

```text
data/private/coa-logs-api-key.txt
```

The key is local/private only and must never be copied into Git, query strings, CLI values, RawArchive metadata, public receipts, logs or screenshots.

Private query-dimension provenance is not a credential and is intentionally stored only in ignored RawArchive observation metadata for new aggregate captures. It must not be promoted to public receipts.

## Report-specific E3 runtime — retained proven state

Six current-report source families remain real-observed/reviewed:

```text
GET /api/reports/{reportId}
GET /api/reports/{reportId}/encounters?includeTrash=...
GET /api/reports/{reportId}/combatants-roster?encounterIds=...
GET /api/reports/{reportId}/encounters/{encounterId}/throughput-timeline?...
GET /api/reports/{reportId}/character_damage_taken_abilities?...
GET /api/reports/{reportId}/character_spell_healing?...
```

First-report generic persistence:

```text
derived observations: 2031
replay matched all 2031
analytics observations: 19660
replay matched all 19660
```

Second independent report:

```text
derived inserted: 2920
analytics inserted: 28213
throughput points: 16907
```

Structural benchmark:

```text
reports: 2
input profiles: 45
eligible peer cohorts: 3
eligible profiles: 6
eligible ranked rows: 133
```

Scope-aware repair:

```text
623 false/legacy events superseded
open events: 645 -> 22
new scoped schema changes on replay: 0
pending reanalysis: 0
```

## Historical difficulty/equivalence gate

Still:

```text
status: insufficient_evidence
verified difficulty reports: 0
numeric historical cross-report scoring: blocked
```

This is an evidence gap, not proof of different difficulties. No v4 heuristic is planned simply to force equivalence.

The aggregate public `/statistics` lane is independent because its dimensions are explicit in the documented API contract.

## Upstream executable source

Pinned evidence provider:

```text
FangYuanWoW/AscensionLogsCompanion
main @ 0f63fe9c50b470402e3a29fba2e0322095856fd4
version 0.67.2
```

Use for client-state/capture/build/gear/telemetry evidence. Backend comments remain hypotheses until corroborated.

## Browser Observatory / HAR

Retained as fallback for undocumented gaps only. It is not the current default Ascension Logs path.

Do not add stealth/fingerprint/challenge-bypass behavior.

## Local workspace integrity

The real Windows metadata inventory and the only Git-visible untracked implementation candidate have both been reviewed.

Observed local Git state at the inventory checkpoint:

```text
modified tracked files: 0
missing tracked files: 0
Git-visible untracked files: 1
```

The single untracked candidate was a historical E3 helper-analysis patch. Content review established:

```text
patch lines: 2668
tracked files changed by patch: 10
insertions/deletions reported by git apply --stat: +690 / -349
obvious added credentials/URLs/secrets: none found
baseline: directly matches the current tracked helper-analysis files
status: valuable incomplete WIP; preserve privately; do not apply as-is
```

The patch improves structural JavaScript helper analysis but depends on absent shared module:

```text
coa_workbench.collector.guild_progression_js_lexical
```

Expected API:

```text
StructuralIndex
exact_symbol_positions
in_excluded_intervals
scan_javascript_structure
```

That module is absent from both the patch and tracked Git history. Reconstructing it would be a separate reviewed task if that lane becomes active again.

Current integrity status:

```text
tracked repository audit: complete
local metadata/file-state inventory: complete
local-only exact file audit: complete/classified
historical helper patch: preserved private, intentionally not integrated
raw private evidence bulk-content review: intentionally outside repository-integrity scope
```

Unknown/untracked files must not be deleted merely to make Git clean.

## Current boundary

```text
official API contract: reviewed
real phase/boss catalog: proven
real current statistics capture: proven
real statistics structural review: proven
statistics parser/model: implemented + deterministic-test verified
migration 0013 aggregate persistence: implemented + deterministic-test verified
population-prior read model: implemented + deterministic-test verified
real statistics persistence/idempotence: pending one provenance-aware recapture
report pipeline generalization: proven on two reports
report analytics persistence: proven + idempotent
scope-aware source schema repair: proven
historical difficulty equivalence: insufficient evidence
cross-report identity: unproven
fight-duration comparison semantics: unproven
site Tier List algorithm: undocumented
guild-progression helper historical lexical refactor: incomplete private WIP, not integrated
planner scoring: blocked
```
