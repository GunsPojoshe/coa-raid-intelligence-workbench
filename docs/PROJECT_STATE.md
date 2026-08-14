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

Latest fully verified checkpoint before this documentation/evidence update:

```text
HEAD: 3ebf2186623b7dffd4033e2b4e9428dd175c91c5
Verify repository #677: success
public-release-audit: success
ubuntu: success
windows: success
```

Newer HEAD/CI must always be checked live.

## Real Network-first baseline

The user's local Source Observatory contains the real browser-origin baseline for:

```text
GET /api/phases
GET /api/guilds/phase-progression?phase=<value>&difficulty=<value>
```

Both are `200 application/json`, with immutable raw captures and schema/dimension snapshots.

Public structural receipts:

```text
evidence/real-data/source-observatory-network-baseline-2026-08-14.json
evidence/real-data/source-observatory-derived-baseline-2026-08-14.json
```

HAR, raw bodies, query values, cookies, headers and actual dimension values remain private/local.

## Derived Source Observatory layer

Migration `0011_source_dimension_index.sql` adds the first real deterministic derived artifact.

Current real local result:

```text
source_dimension_index status: completed
observed endpoints: 2
active source_endpoint dependencies: 2
dimension names represented: 5
dimension values represented: 19
completed analysis runs: 1
acquisition-problem endpoints: 0
```

The two active dependencies are:

```text
phases_api
guild_phase_progression_api
```

The approved chain is:

```text
source change event
-> active source_endpoint dependency
-> pending reanalysis_request
-> deterministic source_dimension_index rebuild
-> completed analysis_run
-> matching reanalysis_request completed
```

A synthetic unit test proves the change -> scoped reanalysis path.

## Real same-input replay

The already-existing browser HAR was replayed locally through `observe_network_cycle.py`.

No new network request was performed.

Before and after replay:

```text
open source-change events: 2 -> 2
pending reanalysis requests: 0 -> 0
Source & Analysis Health payload: identical
new change events from replay: 0
new reanalysis requests from replay: 0
```

Therefore real same-input/no-change idempotence is proven for the current baseline.

This does **not** yet prove handling of a genuinely newer upstream source change.

## Source & Analysis Health

Localhost endpoints:

```text
/source-health
/api/source-health
```

They expose capture/acquisition state, schema/dimension counts, open changes, active dependencies,
pending reanalysis and completed analysis runs without exposing raw payloads or dimension values.

## Progression route correction

Do not resume the historical guessed `POST /api/guilds/progression` helper/owner investigation.

The current captured progression page used:

```text
/api/phases
/api/guilds/phase-progression
```

Archived SPA `progression/rankings*` GET contracts remain alternate reviewed contracts, not proof of
current runtime use.

## Current boundary

```text
Network-first discovery implemented: true
browser-origin phases/progression baseline persisted: true
schema/dimension baselines persisted: true
Source & Analysis Health UI implemented: true
real source_dimension_index initialized: true
real same-input/no-change replay proven: true
synthetic scoped reanalysis on source change proven: true
real later source change -> scoped reanalysis proven: false
ready for autonomous full source coverage: false
planner scoring promoted automatically: false
```

## Next product work

```text
capture a genuinely later browser/network observation when useful
-> prove real upstream change/no-change behavior
-> reduce operator effort for recurring browser capture
-> expand Network-first coverage to reports/encounters/rankings/statistics/characters
-> Armory/talent-grid
-> BisBeard
```

Do not ask the user to re-run the same HAR or reinitialize the same derived baseline merely to
rediscover the facts recorded above.
