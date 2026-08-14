# E3 guild progression evidence status

Дата актуализации: **2026-08-14**.

## 1. Historical correction

The exact legacy literal:

```text
/api/guilds/progression
```

is not a direct POST endpoint in the reviewed SPA evidence. The old helper/owner chain is retained only as audit history and must not drive request selection.

Alternate SPA contracts remain present:

```text
GET /api/guilds/progression/rankings
GET /api/guilds/progression/full-clears
GET /api/guilds/progression/rankings/{bossId}
```

A direct empty-parameter rankings acquisition was attempted and produced a managed-edge `403` HTML challenge. That is acquisition evidence only; it does not prove the route absent and does not provide JSON semantics.

## 2. Current browser Network evidence

A sanitized browser HAR from `/guilds/progression` captured the actual runtime requests used by the current page:

```text
GET /api/phases                                      -> 200 application/json
GET /api/guilds/phase-progression?phase=...&difficulty=... -> 200 application/json
```

The phase-progression response contains the structural domains:

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

Timestamped 2026-08-14 observation:

```text
phase catalog entries: 3
active phase number: 2
boss rows: 12
per-boss ranking groups: 12
guild progression rows: 16
locations observed: Molten Core, Onyxia's Lair
raid-size classes observed: 25-man, flex, mixed
```

These values are observations and must never become hardcoded permanent game configuration.

Current SPA request construction supports:

```text
phase      always mapped
board      optional
difficulty optional
```

## 3. Canonical evidence

Historical SPA contract receipt:

```text
evidence/real-data/argentum-guild-progression-frontend-request-contract.json
```

Current browser-network receipt:

```text
evidence/real-data/coa-guild-phase-progression-browser-network.json
```

The browser-network receipt publishes no raw HAR, headers, cookies, user identity, guild names/IDs, report IDs, encounter IDs or raw response bodies.

## 4. Registry / Observatory boundary

Reviewed Source Observatory routes:

```text
phases_api
guild_phase_progression_api
guild_progression_rankings_api
```

The first two are supported by current browser Network evidence. Rankings remains an alternate SPA-reviewed contract.

Generic same-origin HAR discovery:

```text
scripts/inventory_network_har.py
```

It is scalar-free and is the preferred way to discover future route changes before adding a reviewed contract.

## 5. Decision boundary

```text
Network-first discovery: active
current phase-progression browser request observed: true
phase-progression JSON structure observed: true
current browser raw response persisted in user's Observatory: pending
pagination semantics verified: false
termination semantics verified: false
completeness verified: false
ready for autonomous full guild crawl: false
planner scoring allowed from progression evidence alone: false
```

## 6. Next step

```text
persist /api/phases + /api/guilds/phase-progression browser responses locally
-> establish schema/dimension baseline
-> capture again later
-> detect new phase/boss/location/schema automatically
-> emit scoped reanalysis requests
```

Do not resume global helper/owner archaeology unless a concrete future network request cannot be explained without it.
