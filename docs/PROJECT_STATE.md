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

Latest fully verified checkpoint before the current derived-dimension change:

```text
HEAD: a448d9cd9dd0cbd45891352a9a246b9e6f1c44b2
Verify repository #673: success
public-release-audit: success
ubuntu: success
windows: success
```

Newer HEAD/CI must always be checked live.

## Network-first Source Observatory baseline

The real browser `/guilds/progression` baseline is persisted locally for:

```text
GET /api/phases
GET /api/guilds/phase-progression?phase=<value>&difficulty=<value>
```

Both returned `200 application/json` and have immutable raw captures plus schema/dimension snapshots.

Public structural receipt:

```text
evidence/real-data/source-observatory-network-baseline-2026-08-14.json
```

HAR, raw bodies, query values, cookies, headers and dimension values remain private/local.

## Source Observatory operating layer

```text
browser/network observation
-> sanitized same-origin API inventory
-> reviewed route registry
-> immutable raw capture
-> schema/dimension snapshot
-> change registry
-> dependency graph
-> scoped reanalysis
-> Source & Analysis Health
```

Operational tooling:

```text
scripts/inventory_network_har.py
scripts/observe_source.py
scripts/observe_network_cycle.py
scripts/rebuild_source_dimensions.py
scripts/source_health.py
```

## Real derived dependency: source dimension index

Migration `0011_source_dimension_index.sql` adds the first actual derived Source Observatory artifact.

`source_dimension_index` materializes the **latest complete observed dimension sets** from reviewed endpoint snapshots into the local warehouse. Values remain private/local; summaries expose only counts and fingerprints.

Current intended dependencies are derived automatically from registry routes that are both Observatory-ready and declare `dimension_keys`. For the current registry these are the real baseline routes:

```text
phases_api
guild_phase_progression_api
```

The behavior is now:

```text
source change event
-> active source_endpoint dependency
-> pending reanalysis_request
-> deterministic source_dimension_index rebuild
-> completed analysis_run
-> matching reanalysis_request completed
```

A unit test proves the complete chain with a synthetic new boss dimension value: first build registers the dependency, the later source observation creates exactly one scoped reanalysis request, and the rebuild completes it while materializing the new dimension set.

`observe_network_cycle.py` now performs this approved deterministic rebuild automatically after ingesting matching reviewed HAR responses.

## Source & Analysis Health UI

Localhost endpoints:

```text
/source-health
/api/source-health
```

The page reports source state, captures, changes, active dependencies, pending reanalysis, completed analysis runs and dimension counts without exposing raw payloads or dimension values.

## Important progression route correction

Do not resume the historical helper/owner investigation or guessed `POST /api/guilds/progression`.

Actual runtime capture observed `/api/phases` and `/api/guilds/phase-progression`. Archived SPA `progression/rankings*` GET contracts remain alternate reviewed contracts only.

## Next product work

```text
initialize the dimension index against the user's already-persisted baseline
-> capture a later browser/network cycle
-> observe real change/no-change behavior end-to-end
-> minimize operator work needed to produce recurring browser captures
-> expand Network-first coverage to reports/encounters/rankings/statistics/characters
-> Armory/talent-grid
-> BisBeard
```

No unknown write contracts. No automatic semantic trust promotion. New dimensions are observations, not automatic mechanic/scoring truth.
