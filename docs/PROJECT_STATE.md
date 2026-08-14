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

The canonical source path is:

```text
browser/network observation
-> reviewed contract
-> immutable RawArchive
-> acquisition observation
-> schema/dimension snapshot
-> source change event
-> artifact dependency
-> scoped reanalysis
-> Source & Analysis Health
```

SPA/static evidence is supporting evidence, not a replacement for current browser Network observations.

## Current progression baseline

The real browser-origin progression baseline contains:

```text
GET /api/phases
GET /api/guilds/phase-progression?phase=<value>&difficulty=<value>
```

Both are persisted locally as immutable captures with schema/dimension observations.

The historical guessed `POST /api/guilds/progression` path remains superseded.

Archived SPA alternate GET contracts remain reviewed but are not evidence of current runtime usage:

```text
GET /api/guilds/progression/rankings
GET /api/guilds/progression/full-clears
GET /api/guilds/progression/rankings/{bossId}
```

## Reports baseline

The real browser Network `/reports` observation confirmed and the local replay persisted:

```text
reports_public_api
reports_public_filter_options_api
reports_queue_status_api
```

Current derived local result:

```text
observed dimension endpoints: 3
active source_endpoint dependencies: 3
dimension names represented: 5
dimension values represented: 49
pending reanalysis requests: 0
```

Actual dimension values, HAR, raw bodies, headers, cookies and query values remain local/private.

## Report-detail collision repair

The first Reports replay exposed a generic dynamic-template collision:

```text
/api/reports/queue-status
```

was incorrectly eligible for:

```text
/api/reports/{reportId}
```

The local bounded repair has now been applied and independently replayed.

Observed repair result:

```text
repair status: repaired
derived acquisitions removed: 1
derived captures removed: 1
derived change events removed: 1
raw objects deleted: false
raw fetch observations deleted: false
```

After replay the only reviewed Reports endpoints observed were:

```text
reports_public_api
reports_public_filter_options_api
reports_queue_status_api
```

`report_detail_api` is no longer present in Source Health after cleanup.

Public structural receipt:

```text
evidence/real-data/coa-reports-observatory-repair-replay-v3-review.json
```

## Safe dynamic HAR resolution

Generic dynamic-template ingestion remains disabled.

The repository now resolves dynamic reviewed routes only when:

```text
1. the concrete HAR path is not any known static route;
2. its placeholder binding is corroborated across multiple reviewed dynamic contracts;
3. only the pre-resolved concrete paths are passed to HAR acquisition;
4. concrete path/identifier values remain local-only.
```

This is intended to prevent static routes such as `queue-status` from being reclassified as report IDs without guessing what a report ID looks like.

Current reviewed historical dynamic templates are:

```text
GET /api/reports/{reportId}
GET /api/reports/{reportId}/encounters/{encounterId}
GET /api/reports/{reportId}/encounters/{encounterId}/combatants-info
```

They remain historical reviewed contracts until a new browser HAR for a concrete report supplies current-runtime corroboration.

## Source & Analysis Health

Localhost endpoints:

```text
/source-health
/api/source-health
```

Current repaired local Source Health summary:

```text
endpoint count: 5
captured endpoint count: 5
acquisition-problem endpoint count: 0
completed analysis runs: 2
pending reanalysis requests: 0
```

## Current boundary

```text
Network-first discovery implemented: true
browser-origin phases/progression baseline persisted: true
reports public/filter-options/queue-status persisted: true
false report-detail classification cleaned locally: true
raw evidence preserved during cleanup: true
generic dynamic HAR ingestion: disabled
correlated dynamic resolver implemented: true
report detail current runtime observed: false
real later source change -> scoped reanalysis proven: false
ready for autonomous full source coverage: false
planner scoring promoted automatically: false
```

## Next product work

```text
observe one concrete report in browser Network
-> let the correlated resolver validate current report/encounter/combatants paths
-> persist current report-detail observations
-> bind existing report-slice/combatants parsers into Source Observatory
-> expand rankings/statistics/characters
-> Armory/talent-grid
-> BisBeard
```

Do not ask the user to replay the old Reports HAR again merely to rediscover the repaired baseline.
