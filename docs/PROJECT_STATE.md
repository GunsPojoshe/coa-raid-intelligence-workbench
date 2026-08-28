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

Planner scoring remains blocked until identity, mechanic, encounter and composition semantics are independently proven.

## Source priority

```text
official documented public API
-> official documented site semantics
-> pinned executable Companion source
-> persisted first-party report/API evidence
-> narrow browser/network fallback
-> structural inference last
```

## Official API — closed real gates

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
```

All public receipts exclude query values, report/encounter IDs, boss/location/difficulty values, class/spec names, metric scalars, raw IDs/paths/fingerprints and credentials.

## Encounter binding trust boundary

Proven:

```text
reference URL shape validated
operator-reviewed concrete boss/location/difficulty scope
unique official /bosses binding for reviewed boss+location
encounter-scoped aggregate context
same-location matched comparator
```

Not proven yet:

```text
report encounter -> selected boss machine correlation
report encounter -> selected difficulty machine correlation
```

Do not describe the current binding as machine-verified encounter identity.

## Current implementation gate

The next gate is independent report encounter -> boss/difficulty source correlation.

Implementation now present, real run still pending:

```text
src/coa_workbench/analytics/report_encounter_source_correlation.py
scripts/capture_report_encounter_source_correlation.py
```

Use the strongest available evidence in this order:

```text
official documented report API if accessible without new assumptions
-> official site semantics / persisted first-party report response
-> pinned Companion executable source
-> Browser/HAR only for the exact remaining undocumented gap
```

The gate must:

```text
consume the already selected report/encounter locally
identify an independent report-side source record
correlate boss identity independently
correlate difficulty independently or leave it unproven
publish only scalar-safe booleans/counts/version markers
fail closed on ambiguity
not request API key/raw archive/DuckDB/private values from the operator
not revive historical difficulty-v4 heuristics
```

## Aggregate implementation

Current implementation includes:

```text
src/coa_workbench/analytics/public_api_population_coverage.py
src/coa_workbench/analytics/public_api_encounter_context.py
src/coa_workbench/analytics/public_api_encounter_comparator.py
scripts/capture_public_api_population_coverage.py
scripts/capture_public_api_encounter_context.py
scripts/capture_public_api_encounter_comparator.py
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

Two reports passed the generic persistence/analytics pipeline. Historical two-report difficulty equivalence remains `insufficient_evidence`; numeric comparison of that historical pair stays blocked.

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
report encounter -> selected boss/difficulty machine correlation: not yet proven
historical difficulty equivalence: insufficient evidence
cross-report identity: unproven
site Tier List algorithm: undocumented
planner scoring: blocked
```
