# Фактическое состояние проекта

Дата актуализации: **2026-08-17**.

## GitHub

Active branches:

```text
main
e2/log-evidence-refactor
e3/real-log-capture
```

PR #7 remains Draft: `e3/real-log-capture -> e2/log-evidence-refactor`.

Live HEAD and exact-head CI must always be checked before extending or merging the branch.

## Product target

CoA-only localhost-first evidence-first raid intelligence platform.

Main product question:

> Почему конкретный человек нужен именно текущему составу?

The platform must adapt to new reports, bosses, phases, fields and source contracts without turning
sample-specific observations into permanent assumptions. Source changes are observed, registered and
reprocessed only for affected artifacts with preserved provenance.

Planner scoring remains fail-closed. Schema names, field names, class/spec labels and one observed
combat result do not establish mechanic semantics.

## Canonical source path

```text
browser/network observation
-> reviewed request contract
-> immutable RawArchive
-> acquisition observation
-> schema/dimension observation
-> source change event
-> artifact dependency
-> scoped reanalysis
-> deterministic derived analysis
-> Source & Analysis Health
```

Generic dynamic-template HAR ingestion is disabled. Dynamic browser paths are accepted only through
correlated resolution with known static-route exclusion. Private path/query values are not published.

## Current report runtime

Six current-report dynamic source families are real browser-observed, reviewed and persisted:

```text
GET /api/reports/{reportId}
GET /api/reports/{reportId}/encounters?includeTrash=...
GET /api/reports/{reportId}/combatants-roster?encounterIds=...
GET /api/reports/{reportId}/encounters/{encounterId}/throughput-timeline?...
GET /api/reports/{reportId}/character_damage_taken_abilities?...
GET /api/reports/{reportId}/character_spell_healing?...
```

Historical encounter-detail/combatants-info routes remain evidence only and do not override the
current browser runtime.

The current `/combatants-roster` payload supplies observation-only roster/build evidence including
specialization, mutually checked talent structures, gear/resolved-item information and BisBeard
metadata. These observations are not mechanic truth by themselves.

## First-report persistence and analytics

The generic report/roster/build path is proven real and idempotent:

```text
derived observations: 2031
first run: inserted 2031 / matched 0
replay:    inserted 0    / matched 2031
```

The first real combat-analytics persistence produced:

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

Immediate replay inserted zero new observations and matched all 19660 existing observations.

Report/analytics artifacts use private `reportId`-scoped Source Observatory dependencies.

## Local comparison/API layer

`current-report-comparison-read-model-v1` is proven on the real local DuckDB.

Typed localhost/private API:

```text
GET /api/current-report-analytics/reports
GET /api/current-report-analytics/latest
GET /api/current-report-analytics/reports/{report_id}
```

The read model/API are explicitly local/private. They perform no collection and do not promote
mechanic semantics or planner scoring.

## Second independent report

A second independent report has passed the same generic current-report pipeline.

Real proof:

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

Public-safe receipt:

```text
evidence/real-data/coa-second-report-generalization-real.json
```

This establishes multi-report ingestion/generalization without creating report-specific parser forks.

## Structural cross-report benchmark

`cross-report-structural-benchmark-v1` groups only exact observed structural peers:

```text
exact report.zone
+ exact encounter_name
+ exact throughput metric
+ exact throughput perspective
```

Real two-report result:

```text
reports:                         2
input profiles:                 45
candidate peer cohorts:          3
eligible peer cohorts:           3
ambiguous peer cohorts:          0
eligible profiles:               6
eligible ranked player rows:   133
single-report profile groups:   33
```

A repeated matching profile within one report makes that cohort ambiguous and excludes it from numeric
comparison. The current three real candidate cohorts are eligible structurally and deterministic on
requery.

Still explicitly unverified:

```text
difficulty equivalence:        false
cross-report player identity:  false
numeric cross-report scoring:  false
mechanic semantics:            false
planner scoring:               false
```

Public-safe receipt:

```text
evidence/real-data/coa-cross-report-structural-real.json
```

## Scope-aware schema baselines

The second report exposed a Source Observatory comparison defect: schemas from different `reportId`
scopes were being compared as sequential versions of one source object.

Before repair:

```text
open source-change events: 645
report_combatants_roster_api: 614
report_encounter_throughput_timeline_api: 16
pending reanalysis: 0
```

`scope-schema-cycle-v1` and `network-source-cycle-v9` make the reviewed path scope part of the schema
peer boundary. For current report routes that scope is private `reportId`; throughput additionally uses
its reviewed `metric + perspective` response profile.

Real replay of the already captured second-report corpus proved:

```text
scope-schema endpoints processed:        6
member events superseded:              619
legacy profile events superseded:        4
total events superseded:               623
new aggregate scoped schema changes:     0

open source-change events:          645 -> 22
pending reanalysis requests:          0 -> 0
active dependencies:                 21 -> 21
completed analysis runs:              6 -> 6
```

Raw objects, raw fetch observations, source captures and exact source-schema snapshots were preserved.
The same replay left the cross-report benchmark at three eligible / zero ambiguous cohorts.

The remaining 22 open Source Observatory signals are not automatically interpreted as genuine upstream
changes. This replay only proves that the 623 cross-report/member/legacy events were invalid schema
peers and that no new scope-cycle aggregate change was created.

Public-safe receipt:

```text
evidence/real-data/coa-scope-schema-cycle-real.json
```

## Public/private boundary

Git/public evidence excludes HAR/raw bodies, report/encounter/player/guild IDs and names, query values,
dynamic group keys, source-capture IDs, private scope/profile values or hashes, and private
input/output fingerprints.

Local comparison/API payloads may contain those private local identifiers and are marked
`public_release_safe=false`.

## Current boundary

```text
Network-first Source Observatory: implemented
current report runtime persistence: real proven
current roster/build parser: real proven
combat analytics persistence: real proven + idempotent
report-scoped dependencies: real proven
current-report comparison model: real proven
typed localhost analytics API: implemented
second independent report ingestion: real proven
structural cross-report peer cohorts: real proven
scope-aware schema cycles: implemented + real proven
cross-report schema-noise cleanup: 645 -> 22 real proven
new scoped schema changes on replay: 0
numeric cross-report scoring: blocked
planner scoring promoted automatically: false
```

## Next product work

The transport, persistence, multi-report generalization and schema-peer boundaries are sufficiently
proven for the current source surface. Do not capture another HAR merely to re-prove them.

Next promotion sequence:

```text
establish defensible difficulty + encounter equivalence for structural peer cohorts
-> establish fight-duration/comparison-unit semantics
-> permit guarded numeric cross-report benchmark only if those gates pass
-> define explicit cross-report character identity only where a stable source identity supports it
-> rankings/statistics/character history
-> Armory/talent-grid enrichment
-> BisBeard planning evidence
-> planner scoring only from corroborated/confirmed mechanics
```

A new browser capture is required only for a genuinely new source surface, a changed contract, or a
deliberate later generalization observation.
