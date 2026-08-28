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

Planner scoring remains blocked until player/build identity, mechanic requirements and composition semantics are independently proven.

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

Real comparator checkpoint:

```text
encounter context class summaries: 59
encounter context spec records: 148
encounter context percentile values: 1924
location comparator class summaries: 59
location comparator spec records: 150
location comparator percentile values: 1950
matched records: 148
encounter-only records: 0
location-only records: 2
records with avg delta/ratio: 148
records with median delta/ratio: 148
records with parse-share delta/ratio: 148
exact dimension match verified: true
temporal day_number match verified: true
missing spec treated as zero: false
source_endpoint_profile dependencies: 12
pending reanalysis: 0
actionable open source changes: 0
source health attention required: false
planner scoring allowed: false
```

Comparator semantics:

```text
same phase
+ same concrete difficulty
+ same location
+ same metric
+ same role
+ same bracket
+ same damage mode
+ same capture day_number
+ bossId omitted only
```

Scalar-safe receipts:

```text
evidence/real-data/coa-public-api-catalog-real.json
evidence/real-data/coa-public-api-statistics-provenance-capture-real.json
evidence/real-data/coa-public-api-statistics-persistence-real.json
evidence/real-data/coa-public-api-statistics-profile-reanalysis-real.json
evidence/real-data/coa-public-api-population-coverage-real.json
evidence/real-data/coa-public-api-encounter-context-real.json
evidence/real-data/coa-public-api-encounter-comparator-real.json
evidence/real-data/coa-report-encounter-source-correlation-real.json
evidence/real-data/coa-report-encounter-population-binding-real.json
```

All public receipts exclude query values, report/encounter IDs, boss/location/difficulty values, class/spec names, metric scalars, raw IDs/paths/fingerprints and credentials.

## Encounter provenance boundary — closed real gate

Proven:

```text
reference URL shape validated
operator-reviewed concrete boss/location/difficulty scope
unique official /bosses binding for reviewed boss+location
exact report + encounter identity from first-party encounter catalog
report encounter -> selected boss machine correlation
report encounter -> selected difficulty machine correlation
boss encounter flag = true
encounter-scoped aggregate context 4/4
same-location matched comparator 4/4
same private selected scope inputs reused
exact comparator dimensions
temporal day_number match
machine-correlated encounter -> population-context provenance binding
```

Real binding receipt:

```text
evidence/real-data/coa-report-encounter-population-binding-real.json
```

Real binding result:

```text
schema version: 1
binding version: report-encounter-population-binding-v1
report catalog source kind: archived_first_party_encounter_catalog
archived report catalog reused: true
report catalog observation count: 1
existing public API persistence reused: true
network request count: 0
source correlation complete: true
exact reference identity verified: true
report encounter boss source correlated: true
report encounter difficulty source correlated: true
encounter context complete: true
encounter context slices: 4
location comparator complete: true
location comparator slices: 4
differential built: true
matched records: 148
encounter-only records: 0
location-only records: 2
exact dimension match verified: true
temporal scope match verified: true
same private scope inputs reused: true
machine-correlated encounter population binding complete: true
player identity verified: false
mechanic semantics verified: false
site Tier List algorithm verified: false
planner scoring allowed: false
public release safe: true
```

The binding was offline and reused already archived/persisted evidence. No Browser/HAR, `events:read`, historical difficulty heuristic or repeat acquisition was used.

## Current implementation gate — player/current-build identity

The encounter-scope provenance blocker is closed. The next independent gate is to establish deterministic player identity and current-build evidence before any player capability claim.

Required trust rules:

```text
name equality alone is not cross-report identity proof
current-report actor/roster identity is scoped to its report evidence
cross-report identity must have explicit corroboration or remain unproven
build/talent/gear observations require source + freshness/provenance
missing or stale build evidence fails closed
population participation/performance does not establish individual capability
mechanic semantics remain separate
planner scoring remains blocked
```

Prefer already persisted first-party report evidence and pinned executable Companion source before Browser/HAR. Do not request new API scope merely to repeat locally available facts.

After player/build identity closes, proceed independently to encounter mechanics / requirement semantics, then capability model and attendance-aware composition fit.

Do not rerun population coverage, encounter context, comparator, source correlation or binding merely to reconfirm them.

## Aggregate implementation

Current implementation includes:

```text
src/coa_workbench/analytics/public_api_population_coverage.py
src/coa_workbench/analytics/public_api_encounter_context.py
src/coa_workbench/analytics/public_api_encounter_comparator.py
src/coa_workbench/analytics/report_encounter_source_correlation.py
src/coa_workbench/analytics/report_encounter_population_binding.py
scripts/capture_public_api_population_coverage.py
scripts/capture_public_api_encounter_context.py
scripts/capture_public_api_encounter_comparator.py
scripts/capture_report_encounter_source_correlation.py
scripts/build_report_encounter_population_binding.py
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

The current encounter catalog real structural review includes `id`, `name`, `boss_id`, `difficulty`, `is_boss_encounter`, `zone` and related fields. Two reports passed the generic persistence/analytics pipeline. Historical two-report difficulty equivalence remains `insufficient_evidence`; numeric comparison of that historical pair stays blocked.

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
real phase/boss catalog: proven
real statistics normalization/persistence/idempotence: proven
aggregate Source Observatory/Health: proven
profile-scoped aggregate invalidation: proven
bounded population coverage v1: proven 4/4
bounded encounter context v1: proven 4/4
matched encounter/location comparator v1: proven 4/4
exact comparator dimensions: proven
comparator temporal day match: proven
missing-spec zero coercion: prohibited/proven false
report encounter -> selected boss/difficulty machine correlation: proven
machine-correlated encounter -> population-context provenance binding: proven
historical difficulty equivalence: insufficient evidence
cross-report player identity: unproven
current-build evidence: unproven
encounter mechanic semantics: unproven
site Tier List algorithm: undocumented
planner scoring: blocked
```
