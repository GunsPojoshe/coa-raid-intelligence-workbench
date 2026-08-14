# Фактическое состояние проекта

Дата актуализации: **2026-08-14**.

## GitHub

Active branches:

```text
main
e2/log-evidence-refactor
e3/real-log-capture
```

PR #7 remains Draft: `e3/real-log-capture -> e2/log-evidence-refactor`.

Newer HEAD/CI must always be checked live.

## Product target

CoA-only localhost-first evidence-first raid intelligence platform.

Main product question:

> Почему конкретный человек нужен именно текущему составу?

The platform must remain adaptive to new bosses, phases, fields, logs and source contracts.
Source change handling must be automatic, scoped and provenance-preserving rather than implemented
as one-off collectors.

## Network-first Source Observatory

Canonical source path:

```text
browser/network observation
-> reviewed contract
-> immutable RawArchive
-> acquisition observation
-> schema/dimension observation
-> source change event
-> artifact dependency
-> scoped reanalysis
-> Source & Analysis Health
```

SPA/static evidence is supporting evidence, not a replacement for current browser Network observations.

Generic dynamic-template ingestion is disabled. Dynamic browser paths are accepted only after
cross-contract corroboration and exact known-static-route exclusion. Dynamic path values remain
local/private.

## Progression baseline

Current real browser-origin progression baseline:

```text
GET /api/phases
GET /api/guilds/phase-progression?phase=<value>&difficulty=<value>
```

Both are persisted locally as immutable captures with schema/dimension observations.

Historical guessed `POST /api/guilds/progression` remains superseded. Archived SPA alternate GET
contracts remain reviewed but are not current-runtime evidence.

## Reports-list baseline

Real `/reports` Network observation and local replay persisted:

```text
reports_public_api
reports_public_filter_options_api
reports_queue_status_api
```

Current derived dimension state:

```text
observed dimension endpoints: 3
active source_endpoint dependencies: 3
dimension names represented: 5
dimension values represented: 49
pending reanalysis requests: 0
```

The earlier `queue-status -> /api/reports/{reportId}` collision was repaired locally without deleting
raw objects or raw fetch observations.

## Current report runtime

A browser Network capture of one concrete report plus one selected encounter has now been fully
consumed by the reviewed Source Observatory.

Current runtime families actually observed and persisted:

```text
GET /api/reports/{reportId}
GET /api/reports/{reportId}/encounters?includeTrash=...
GET /api/reports/{reportId}/combatants-roster?encounterIds=...
GET /api/reports/{reportId}/encounters/{encounterId}/throughput-timeline?...
GET /api/reports/{reportId}/character_damage_taken_abilities?...
GET /api/reports/{reportId}/character_spell_healing?...
```

Profile-aware replay result:

```text
dynamic routes resolved: 6
dynamic concrete paths: 9
reviewed route observations: 18
Source Health endpoints: 11
captured endpoints: 11
acquisition-problem endpoints: 0
pending reanalysis requests: 0
```

Historical exact routes remain reviewed but were not observed in this current capture:

```text
GET /api/reports/{reportId}/encounters/{encounterId}
GET /api/reports/{reportId}/encounters/{encounterId}/combatants-info
```

They must not override the current runtime model.

## Throughput schema-profile correction

The first persisted current-report replay produced false schema churn because
`throughput-timeline` is a multi-mode endpoint.

Profile-unaware state:

```text
open source-change events total: 799
throughput endpoint: 789
all other endpoints combined: 10
```

Registry schema v6 defines reviewed response-shaping keys:

```text
schema_profile_keys:
  - metric
  - perspective
```

A bounded repair then superseded only the legacy profile-unaware schema-change events:

```text
repair status: repaired
superseded legacy events: 788

field_added:        256
field_removed:      515
field_type_changed:   7
schema_changed:      10

linked downstream reanalysis requests: 0

raw objects deleted: false
raw fetch observations deleted: false
source captures deleted: false
schema snapshots deleted: false
```

The same HAR was replayed under `network-source-cycle-v6`.

Result after profile-aware replay:

```text
open source-change events total: 34
throughput endpoint: 24
all other endpoints combined: 10
pending reanalysis requests: 0
```

This validates the profile partition and removes the original 789-event false-churn signal.
The remaining 34 open events are baseline/profile-aware observations and are **not** automatically
interpreted as 34 upstream source changes. Their semantics still require structural review before
they are used as health alarms or planner signals.

Public structural receipt:

```text
evidence/real-data/coa-current-report-profile-replay-v3-review.json
```

HAR, raw payloads, report/encounter IDs, query values, headers, cookies, dimension values and schema
profile values/hashes remain local/private.

## Source & Analysis Health

Localhost endpoints:

```text
/source-health
/api/source-health
```

Current real local summary after profile-aware repair/replay:

```text
endpoint count: 11
captured endpoint count: 11
open change event count: 34
acquisition-problem endpoint count: 0
active dependency count: 3
completed analysis runs: 2
pending reanalysis requests: 0
```

## Current boundary

```text
Network-first discovery implemented: true
browser-origin phases/progression persisted: true
reports public/filter-options/queue-status persisted: true
false report-detail collision cleaned locally: true
correlated dynamic resolver implemented: true
current report detail runtime observed: true
current encounter catalog runtime observed: true
current combatants-roster runtime observed: true
current throughput runtime observed: true
current character damage/healing runtime observed: true
current report runtime persisted in Source Observatory: true
reviewed schema-profile mechanism implemented: true
legacy profile-unaware throughput churn repaired locally: true
profile-aware replay against real HAR proven: true
raw evidence preserved through repairs: true
real later upstream change -> scoped reanalysis proven: false
ready for autonomous full source coverage: false
planner scoring promoted automatically: false
```

## Next product work

The transport/discovery loop is now sufficiently proven for this slice. Do not create another browser
capture merely to re-prove current report routes.

Next:

```text
inspect the private current-report payloads already present in the HAR/local corpus
-> document real report/encounter/roster/throughput/damage/healing schemas
-> bind current combatants-roster into existing combatants observation persistence
-> bind encounter/report identity and provenance
-> add deterministic current-report derived analysis
-> then expand rankings/statistics/characters
-> Armory/talent-grid
-> BisBeard
```

A new browser capture is required only when a new source surface must be observed or an existing
contract changes.
