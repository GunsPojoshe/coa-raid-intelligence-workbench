# Фактическое состояние проекта

Дата актуализации: **2026-08-28**.

Canonical restart order:

```text
AGENTS.md
docs/DOCUMENTATION_INDEX.md
docs/CURRENT_PARADIGM.md
docs/PROJECT_MASTER_CONTEXT.md
docs/PROJECT_STATE.md
docs/OFFICIAL_PUBLIC_API.md
docs/CONTINUATION_PROMPT.md
docs/NEXT_CHAT_HANDOFF.md
```

## GitHub / workstreams

```text
main
└── e2/log-evidence-refactor        Draft PR #3 -> main
    └── e3/real-log-capture         Draft PR #7 -> e2
        └── e4/interactive-har-discovery  Draft PR #9 -> e3
```

Always re-check live branch/PR/CI state; stored SHAs are checkpoints only.

## Product state

CoA-only localhost-first evidence-first raid intelligence.

Primary question:

> **Почему конкретный человек нужен именно текущему составу?**

Planner scoring remains blocked until selected-report player/build evidence, freshness, mechanic requirements and composition semantics are independently proven.

## Source priority

```text
official documented public API
-> official documented site semantics
-> pinned executable Companion source
-> persisted first-party report/API evidence
-> narrow browser/network fallback
-> structural inference last
```

## Official API / encounter evidence — closed real gates

Reviewed contract:

```text
OpenAPI 3.1.0
API version 1.0.0
stats:read: /phases, /bosses, /statistics
```

Closed real gates:

```text
/phases + /bosses catalog
single-slice provenance-aware /statistics
exact normalization
DuckDB persistence + idempotence
population-prior read model
Source Observatory / Source & Analysis Health
source_endpoint_profile dependency migration
bounded population coverage v1: 4/4
bounded encounter context v1: 4/4
matched encounter/location comparator v1: 4/4
report encounter boss/difficulty source correlation v2: proven
machine-correlated encounter population binding v1: proven
```

Retained canonical status markers:

```text
real statistics normalization: proven
real DuckDB persistence/idempotence: proven
aggregate Source Observatory/Health integration: proven real
profile-scoped aggregate invalidation: proven real
bounded multi-profile population coverage v1: proven 4/4
```

Scalar-safe encounter receipts include:

```text
evidence/real-data/coa-public-api-encounter-comparator-real.json
evidence/real-data/coa-report-encounter-source-correlation-real.json
evidence/real-data/coa-report-encounter-population-binding-real.json
```

Historical two-report difficulty equivalence remains `insufficient_evidence`.

## Persisted report-scoped player/build provenance — closed real gate

Real receipt:

```text
evidence/real-data/coa-current-roster-build-provenance-real.json
```

Real result:

```text
catalog version: current-roster-build-provenance-catalog-v1
persisted report count: 2
reviewed report scope count: 2
report scope with roster count: 2
report-scoped player identity complete count: 2
observed build linkage complete count: 2
source provenance complete count: 2
observed build provenance complete count: 2
character count: 52
snapshot count: 70
talent entry count: 3558
gear slot observation count: 1195
observed timestamp coverage complete count: 0
selected reference present: false
selected reference report-scoped player identity complete: false
selected reference observed build provenance complete: false
selected reference same-report build binding proven: false
current build freshness verified: false
latest snapshot semantics verified: false
cross-report identity verified: false
player capability semantics verified: false
mechanic semantics verified: false
planner scoring allowed: false
public release safe: true
```

Interpretation:

```text
all persisted report scopes have deterministic report-scoped player identity: proven real
all persisted report scopes have observed build linkage/provenance: proven real
selected encounter report is one of those roster/build scopes: false
same-report selected encounter -> roster/build binding: unproven
full timestamp coverage for freshness selection: 0/2
```

No network, Browser/HAR or `events:read` was used for this proof.

## Current implementation gate — selected-report roster/build binding

The immediate gap is not generic roster parsing. The selected encounter report is absent from persisted `current_report_observation` roster/build scopes.

Proceed fail-closed:

```text
inspect existing local persisted/raw first-party evidence for the selected report
reuse archived roster/build evidence if present
if absent, inspect official documented site semantics and pinned Companion executable for the narrow source contract
acquire only the missing selected-report evidence when genuinely necessary
Browser/HAR remains fallback only for an exact undocumented gap
never substitute another report by player/name similarity
```

After selected-report same-report binding is proven, establish current/latest snapshot semantics. `observed_timestamp_coverage_complete_count = 0` means freshness is still independently blocked.

## Aggregate implementation

Current implementation includes:

```text
src/coa_workbench/analytics/public_api_population_coverage.py
src/coa_workbench/analytics/public_api_encounter_context.py
src/coa_workbench/analytics/public_api_encounter_comparator.py
src/coa_workbench/analytics/report_encounter_source_correlation.py
src/coa_workbench/analytics/report_encounter_population_binding.py
src/coa_workbench/analytics/current_roster_build_provenance.py
src/coa_workbench/analytics/current_roster_build_provenance_catalog.py
scripts/capture_public_api_population_coverage.py
scripts/review_current_roster_build_provenance.py
```

`request_contract_changed` remains endpoint-global; schema/profile-local changes target only matching private query profiles. Events older than dependency registration cannot back-trigger newer artifacts.

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

Two independent reports passed the generic persistence/analytics pipeline.

## Upstream executable source

```text
FangYuanWoW/AscensionLogsCompanion
main @ 0f63fe9c50b470402e3a29fba2e0322095856fd4
version 0.67.2
```

Executable code may establish client behavior and emitted structure. Backend comments remain hypotheses until independently corroborated.

## Browser Observatory / HAR

Fallback for exact undocumented gaps only. No stealth/fingerprint/challenge-bypass behavior.

## Local workspace integrity

The historical helper patch remains valuable incomplete private WIP because `guild_progression_js_lexical` is absent. Preserve it; do not apply as-is.

## Current boundary

```text
official API contract: reviewed
real statistics normalization: proven
real DuckDB persistence/idempotence: proven
aggregate Source Observatory/Health: proven
profile-scoped aggregate invalidation: proven
bounded population coverage v1: proven 4/4
bounded encounter context v1: proven 4/4
matched encounter/location comparator v1: proven 4/4
report encounter -> selected boss/difficulty machine correlation: proven
machine-correlated encounter -> population-context provenance binding: proven
persisted report-scoped player identity: proven 2/2
persisted observed build provenance: proven 2/2
selected encounter report -> roster/build same-report binding: unproven
current/latest build freshness: unproven
cross-report player identity: unproven
historical difficulty equivalence: insufficient evidence
encounter mechanic semantics: unproven
site Tier List algorithm: undocumented
planner scoring: blocked
```
