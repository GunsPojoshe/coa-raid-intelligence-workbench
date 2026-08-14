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

Last fully verified checkpoint before the current Network-first update:

```text
HEAD: 269cbabe066137f2f27c33526e1cdeefa30970ad
Verify repository #647
public-release-audit: success
ubuntu: success
windows: success
```

Always verify newer HEAD/CI live.

## Source Observatory

Implemented shared infrastructure:

```text
reviewed contract
-> acquisition observation
-> immutable RawArchive
-> JSON schema snapshot when applicable
-> source change registry
-> dependency lookup
-> scoped reanalysis request
```

Migrations currently published: `0001`–`0010`.

Direct HTTP and browser-HAR acquisition outcomes are separated so a blocked/non-JSON response cannot be mistaken for schema evidence.

## Network-first correction

A sanitized Chrome HAR of the current `/guilds/progression` page was reviewed directly.

Same-origin API Fetch/XHR inventory contained 7 observations across 6 route shapes. The progression-relevant runtime path was:

```text
GET /api/phases                                      -> 200 JSON
GET /api/guilds/phase-progression?phase=...&difficulty=... -> 200 JSON
```

The phase-progression response structurally contains:

```text
phase
board
enabled
totalBosses
bossesCollapsed
bossList
perBossRankings
guilds
```

Timestamped observation at 2026-08-14:

```text
phase catalog entries: 3
active phase number: 2
bossList rows: 12
perBossRankings groups: 12
guild progression rows: 16
observed locations: Molten Core, Onyxia's Lair
observed raid-size classes: 25-man, flex, mixed
```

These counts are **observations**, not hardcoded product configuration.

Current SPA additionally confirms that `phase-progression` always maps `phase` and conditionally maps `board` and `difficulty`.

Canonical public receipt:

```text
evidence/real-data/coa-guild-phase-progression-browser-network.json
```

Raw HAR and user/session/guild/report record values remain private.

## Relation to rankings routes

The earlier reviewed SPA contracts still exist:

```text
GET /api/guilds/progression/rankings
GET /api/guilds/progression/full-clears
GET /api/guilds/progression/rankings/{bossId}
```

They were **not** exercised by this particular browser capture. Therefore they remain alternate reviewed contracts, not the primary runtime path observed for the current progression page.

The earlier direct rankings GET produced a managed-edge `403`; that remains a transport/acquisition observation only.

## Universal discovery direction

Generic sanitized HAR discovery is now part of the product path:

```text
scripts/inventory_network_har.py
```

It inventories same-origin API route shapes, query-key names, HTTP statuses, content families and JSON structural fingerprints without keeping query values, headers, cookies, response bodies or response scalar values.

This is the basis for detecting:

```text
new/changed endpoint
new phase
new boss
new location/difficulty
schema change
new report/data availability
```

and then requesting only the affected reanalysis.

## Next action

```text
import the observed /api/phases and /api/guilds/phase-progression responses
into the user's local Source Observatory
-> establish the first real schema/dimension baseline
-> repeat acquisition later
-> prove automatic source-change detection
-> bind change events to scoped reanalysis
-> expand the same Network-first discovery to reports, encounters, characters,
   Armory/talent-grid and BisBeard
```

No guessed POST. No open-ended helper/owner archaeology. No hardcoded current boss/phase counts.

## Development process

- Agent performs all GitHub work available to it.
- User participates only at inaccessible Windows/browser/private-runtime boundaries.
- Private/raw artifacts may be inspected for analysis; publication/versioning is separate.
- Prefer one coherent change, one aggregate verifier, one push, then exact-head CI.
