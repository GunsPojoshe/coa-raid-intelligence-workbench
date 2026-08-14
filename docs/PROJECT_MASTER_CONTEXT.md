# CoA Raid Intelligence Workbench — канонический контекст проекта

Дата актуализации: **2026-08-14**.

## 1. Цель

Создать localhost-first evidence-first платформу рейдовой аналитики для **Conquest of Azeroth**,
которая связывает фактическую явку, проверенные build/performance observations и encounter
requirements и объясняет конкретные решения по составу.

Главный вопрос:

> Почему конкретный игрок нужен именно этому текущему составу?

Не использовать Bronzebeard/Classless/Mystic/Hero Architect/shared Ascension сведения как CoA-факты
без exact CoA evidence.

## 2. Truth model

```text
combat-log event = observation
combat-log event != automatic mechanic proof
class/spec presence != verified capability coverage
timestamped source response != permanent source semantics
```

Only `corroborated` and `confirmed` mechanics may enter canonical planner scoring.

## 3. Canonical evidence/change architecture

```text
browser/network/source discovery
-> reviewed request contract
-> immutable raw payload
-> acquisition observation
-> schema/dimension snapshot
-> source-change events
-> artifact dependency
-> scoped reanalysis request
-> deterministic derived analysis
-> supporting / contradicting evidence
-> trust decision
-> explainable recommendation
```

Upstream change is normal: new bosses, phases, reports, fields, routes and meta must not require
hardcoded product rewrites.

## 4. Implemented foundation

- localhost FastAPI planner;
- DuckDB migrations `0001`–`0011`;
- immutable raw archive;
- retrieval/acquisition observations;
- privacy-safe JSON/HAR tooling;
- Source Observatory contract/schema/change/reanalysis foundation;
- `source_dimension_index` derived artifact;
- Source & Analysis Health UI/API;
- report/encounter/actor/participant/aura normalization;
- hypothesis/evidence/trust layers;
- repository verifier;
- Ubuntu/Windows CI and public-release audit.

## 5. Verified guild/report baseline

```text
public reports: 6454
unique public report IDs: 6454
exact Argentum label reports: 17
guild identity verified: true
private selected baseline: 17 unique reports
full-crawl collection contract reviewed: true
```

Private report/guild identifiers are not publication material.

## 6. Network-first source discovery

Preferred evidence path:

```text
real browser Fetch/XHR
-> scalar-free HAR inventory
-> reviewed route contract
-> Source Observatory capture
```

SPA JavaScript is supporting evidence when Network does not expose enough request construction detail.

Generic inventory:

```text
scripts/inventory_network_har.py
```

It does not publish query values, headers, cookies, response bodies or response record scalars.

## 7. Guild progression — current runtime evidence

Historical helper/owner work and the guessed exact `POST /api/guilds/progression` path are superseded.

The current browser capture actually exercised:

```text
GET /api/phases
GET /api/guilds/phase-progression?phase=<value>&difficulty=<value>
```

Both returned `200 application/json`.

The phase-progression response structurally exposes:

```text
phase
board
totalBosses
bossList
perBossRankings
guilds
```

Current SPA request construction supports:

```text
phase      always mapped
board      optional
difficulty optional
```

Archived SPA still contains alternate reviewed contracts:

```text
GET /api/guilds/progression/rankings
GET /api/guilds/progression/full-clears
GET /api/guilds/progression/rankings/{bossId}
```

Their static presence is not evidence that the captured current page used them.

## 8. Persisted real Source Observatory baseline

The user's local immutable corpus already contains the browser-origin observations for:

```text
phases_api
guild_phase_progression_api
```

Current structural observation counts:

```text
observed endpoints: 2
dimension names represented: 5
dimension values represented: 19
active dependencies: 2
completed source_dimension_index analysis runs: 1
```

Canonical public receipts:

```text
evidence/real-data/source-observatory-network-baseline-2026-08-14.json
evidence/real-data/source-observatory-derived-baseline-2026-08-14.json
```

The original HAR, raw JSON, headers, cookies, query values and dimension values remain private/local.

## 9. Dynamic reanalysis

`source_dimension_index` is the first real deterministic derived Source Observatory artifact.

```text
source change event
-> matching active source_endpoint dependency
-> pending reanalysis_request
-> source_dimension_index rebuild
-> completed analysis_run
-> matching reanalysis_request completed
```

A synthetic test proves the scoped-change path.

The same real HAR was also replayed against the persisted baseline:

```text
open change events: 2 -> 2
pending reanalysis: 0 -> 0
new change events: 0
new reanalysis requests: 0
Source Health before/after: identical
network requests performed by replay: false
```

So same-input idempotence is proven on real local data. A genuinely later upstream change is not yet
proven end-to-end.

## 10. Current decision boundary

```text
Network-first discovery implemented: true
current progression runtime requests observed: true
real browser baseline persisted: true
schema/dimension baseline persisted: true
real derived source_dimension_index initialized: true
same-input/no-change replay proven: true
synthetic source-change -> scoped reanalysis proven: true
real later source-change -> scoped reanalysis proven: false
ready for autonomous full source coverage: false
planner scoring allowed from progression evidence alone: false
```

No source field automatically becomes mechanic truth or planner scoring input.

## 11. Next product path

```text
obtain a genuinely later browser/network observation when needed
-> prove real source-change/no-change handling
-> minimize recurring browser-capture work
-> expand Network-first discovery to reports/encounters/rankings/statistics/characters
-> Armory/talent-grid/BisBeard adapters
-> multi-report character identity
-> verified build/capability observations
-> encounter requirement models
-> dynamic attendance-aware roster completion
```

Do not rerun the same historical helper/owner investigation or the same baseline initialization unless
a concrete regression requires it.

## 12. Development model

The agent performs GitHub/PR/CI/repository work directly whenever tools permit it. The user is involved
only for Windows/local/private/browser boundaries the agent cannot access directly.

Private/raw files may be inspected for analysis. Publication/versioning remains separately controlled.

Use focused tests while iterating, one aggregate `scripts/verify_repo.py` before a meaningful push,
then exact-head CI.
