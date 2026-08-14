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

Current derived dimension state before report-detail expansion:

```text
observed dimension endpoints: 3
active source_endpoint dependencies: 3
dimension names represented: 5
dimension values represented: 49
pending reanalysis requests: 0
```

The earlier `queue-status -> /api/reports/{reportId}` collision was repaired locally without deleting
raw objects or raw fetch observations.

## Current report runtime: observed and persisted

A browser Network capture of one concrete report plus one selected encounter was replayed through the
current reviewed registry.

The correlated dynamic resolver accepted six current-runtime families:

```text
GET /api/reports/{reportId}
GET /api/reports/{reportId}/encounters?includeTrash=...
GET /api/reports/{reportId}/combatants-roster?encounterIds=...
GET /api/reports/{reportId}/encounters/{encounterId}/throughput-timeline?...
GET /api/reports/{reportId}/character_damage_taken_abilities?...
GET /api/reports/{reportId}/character_spell_healing?...
```

Observed replay result:

```text
dynamic routes resolved: 6
dynamic concrete paths: 9
reviewed route observations: 18
Source Health endpoints: 11
captured endpoints: 11
acquisition-problem endpoints: 0
pending reanalysis requests: 0
```

All reviewed report-runtime observations in this capture were `200 JSON` and produced schema
observations. Report IDs, encounter IDs, query values, raw bodies, headers and cookies remain private.

Public receipts:

```text
evidence/real-data/coa-current-report-browser-network.json
evidence/real-data/coa-current-report-runtime-replay-v2-review.json
```

Historical exact routes remain reviewed but were not observed in this current capture:

```text
GET /api/reports/{reportId}/encounters/{encounterId}
GET /api/reports/{reportId}/encounters/{encounterId}/combatants-info
```

They must not override the current runtime model.

## Throughput schema-profile correction

The first persisted report-runtime replay produced:

```text
open source-change events total: 799
report_encounter_throughput_timeline_api: 789
all other endpoints combined: 10
```

This is not evidence of 789 upstream changes. The same HAR contains a multi-mode throughput endpoint:

```text
without perspective query key: 8 responses, 3 structural schema fingerprints
with perspective query key:    4 responses, 1 structural schema fingerprint
```

Sequentially diffing every throughput response against the immediately previous response therefore
compares legitimate response modes against one another and creates false schema churn.

Registry schema v6 now supports explicit `schema_profile_keys`. For the current throughput contract:

```text
schema_profile_keys:
  - metric
  - perspective
```

Rules:

```text
path parameter values do not partition schema baselines
bucket_size_ms does not partition schema baselines
metric/perspective values partition only local schema comparison state
profile values and profile hashes are never included in public cycle output
schema changes are compared only against the previous snapshot of the same reviewed profile
```

A bounded repair exists:

```text
scripts/repair_throughput_schema_profile_churn.py
```

It supersedes only legacy profile-unaware schema change events, refuses to run if those events already
have downstream reanalysis requests, and preserves raw objects, raw fetch observations, source
captures and schema snapshots.

Local repair + profile-aware replay against the real HAR is the next required proof.

## Source & Analysis Health

Localhost endpoints:

```text
/source-health
/api/source-health
```

Before the profile-aware repair/replay, the current real local summary is:

```text
endpoint count: 11
captured endpoint count: 11
open change event count: 799
acquisition-problem endpoint count: 0
completed analysis runs: 2
pending reanalysis requests: 0
```

The 799 count must not be used as a source-instability signal until the bounded profile repair and
profile-aware replay are applied.

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
throughput multi-mode schema churn identified: true
reviewed schema-profile mechanism implemented: true
bounded legacy profile-churn repair implemented: true
real local profile repair + replay proven: false
real later upstream change -> scoped reanalysis proven: false
ready for autonomous full source coverage: false
planner scoring promoted automatically: false
```

## Next product work

```text
apply bounded throughput profile-churn repair locally
-> replay the existing current-report HAR once under schema-profile-aware cycle
-> verify false churn collapses without losing raw evidence
-> inspect real report/encounter/roster/throughput/damage/healing schemas from local corpus
-> bind existing report-slice/combatants parsers into Source Observatory
-> expand rankings/statistics/characters
-> Armory/talent-grid
-> BisBeard
```

Do not ask the user to make another browser capture until the existing current-report HAR has been
fully consumed by the profile-aware Observatory.
