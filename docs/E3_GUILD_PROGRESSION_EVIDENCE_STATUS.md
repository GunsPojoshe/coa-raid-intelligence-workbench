# E3 guild progression evidence status

Дата актуализации: **2026-08-14**.

## 1. Historical correction

The exact legacy literal:

```text
/api/guilds/progression
```

is not a direct POST endpoint in the reviewed current evidence. The old helper/owner chain is retained
only as audit history and must not drive request selection.

Alternate SPA contracts remain present:

```text
GET /api/guilds/progression/rankings
GET /api/guilds/progression/full-clears
GET /api/guilds/progression/rankings/{bossId}
```

A prior direct empty-parameter rankings acquisition produced a managed-edge `403` HTML challenge. That
is acquisition evidence only; it does not provide JSON semantics.

## 2. Current browser Network evidence

The current `/guilds/progression` browser HAR actually exercised:

```text
GET /api/phases
GET /api/guilds/phase-progression?phase=...&difficulty=...
```

Both returned `200 application/json`.

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

The captured point-in-time observation contained 3 phase catalog entries, 12 boss rows and 2 observed
locations. These are observations, not permanent configuration.

Current SPA request construction supports:

```text
phase      always mapped
board      optional
difficulty optional
```

## 3. Persisted Observatory evidence

The real browser responses are already persisted in the user's local immutable Source Observatory for:

```text
phases_api
guild_phase_progression_api
```

Current derived local state:

```text
source_dimension_index: completed
observed endpoints: 2
active dependencies: 2
dimension names represented: 5
dimension values represented: 19
completed analysis runs: 1
```

The original HAR and actual dimension values remain local/private.

Canonical public receipts:

```text
evidence/real-data/coa-guild-phase-progression-browser-network.json
evidence/real-data/source-observatory-network-baseline-2026-08-14.json
evidence/real-data/source-observatory-derived-baseline-2026-08-14.json
```

## 4. Real same-HAR idempotence

The existing browser HAR was replayed without making a new network request.

```text
open source-change events: 2 -> 2
pending reanalysis requests: 0 -> 0
new change events: 0
new reanalysis requests: 0
Source & Analysis Health before/after: identical
```

Therefore the current real baseline is idempotent for the same observed input.

This does not yet prove a genuinely newer upstream change.

## 5. Decision boundary

```text
Network-first discovery: active
current phase-progression browser request observed: true
current browser raw responses persisted locally: true
schema/dimension baseline persisted: true
real source_dimension_index initialized: true
real same-input/no-change replay proven: true
synthetic change -> scoped reanalysis proven: true
real later change -> scoped reanalysis proven: false
pagination semantics verified: false
termination semantics verified: false
completeness verified: false
ready for autonomous full guild crawl: false
planner scoring allowed from progression evidence alone: false
```

## 6. Next step

```text
do not replay this same baseline again
-> capture a genuinely later browser observation when useful
-> verify real change/no-change handling
-> reduce recurring browser-capture work
-> expand Network-first coverage beyond progression
```

Do not resume global helper/owner archaeology unless a future concrete network request cannot be
explained without it.
