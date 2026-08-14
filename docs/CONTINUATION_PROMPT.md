# Continuation prompt — CoA Raid Intelligence Workbench

Continue development of `GunsPojoshe/coa-raid-intelligence-workbench`.

## Start

The agent performs GitHub/PR/CI/repository work itself. Use the user only for Windows/local/private boundaries that cannot be accessed directly, and bundle those operations into one action.

Read:

```text
AGENTS.md
docs/PROJECT_MASTER_CONTEXT.md
docs/PROJECT_STATE.md
docs/SOURCE_OBSERVABILITY_AND_REANALYSIS.md
docs/SOURCE_OBSERVATORY_V1_STATUS.md
docs/CI_OPERATIONS.md
```

Live GitHub and current local evidence override historical checkpoint text.

## Source discovery rule

Use **Network first**:

```text
real browser Fetch/XHR
-> sanitized HAR inventory
-> reviewed route contract
-> immutable capture
-> schema/dimension baseline
-> change detection
-> scoped reanalysis
```

Inspect SPA JavaScript only when Network evidence does not explain request construction or an additional contract detail is needed.

## Current progression correction

Do not resume the old helper/owner investigation.

A sanitized browser HAR of `/guilds/progression` on 2026-08-14 observed:

```text
GET /api/phases                                      -> 200 JSON
GET /api/guilds/phase-progression?phase=...&difficulty=... -> 200 JSON
```

Current SPA supports the phase-progression helper contract:

```text
phase      always mapped
board      optional
difficulty optional
```

The phase-progression response contains:

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

Canonical receipt:

```text
evidence/real-data/coa-guild-phase-progression-browser-network.json
```

The older `/api/guilds/progression/rankings*` contracts still exist in the SPA, but they were not exercised by this browser capture. Treat them as alternate reviewed contracts, not as the only/current progression path.

## Source Observatory

Reviewed registry routes now include:

```text
phases_api
guild_phase_progression_api
guild_progression_rankings_api
```

Generic HAR discovery:

```text
scripts/inventory_network_har.py
```

It must remain scalar-free: no query values, headers, cookies, response bodies or response record scalars.

## Next product path

```text
import the observed phases + phase-progression HAR responses into local Source Observatory
-> establish first real schema/dimension baseline
-> verify change detection on a later capture
-> connect boss/phase/source changes to scoped reanalysis
-> expand Network-first discovery to reports/encounters/characters/Armory/BisBeard
```

Do not hardcode current boss/phase counts into product logic. New bosses, phases, logs and meta changes are expected normal source evolution.

## Safety

- Do not rewrite published migrations.
- Do not delete `.gitkeep`.
- Do not publish raw HAR/session/user/private evidence.
- Do not raise semantic/scoring gates by inference.
- Do not treat one timestamped response as permanent source semantics.
