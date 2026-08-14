# CoA Raid Intelligence Workbench — канонический контекст проекта

Дата актуализации: **2026-08-14**.

## 1. Цель

Создать localhost-first evidence-first платформу рейдовой аналитики для **Conquest of Azeroth**, которая связывает фактическую явку, проверенные build/performance observations и encounter requirements и объясняет конкретные решения по составу.

Главный вопрос:

> Почему конкретный игрок нужен именно этому текущему составу?

Не использовать Bronzebeard/Classless/Mystic/Hero Architect/shared Ascension сведения как CoA-факты без exact CoA evidence.

## 2. Truth model

```text
combat-log event = observation
combat-log event != automatic mechanic proof
class/spec presence != verified capability coverage
timestamped source response != permanent source semantics
```

Only `corroborated` and `confirmed` mechanics may enter canonical planner scoring.

## 3. Evidence and change architecture

```text
browser/network/source discovery
-> reviewed request contract
-> immutable raw payload
-> acquisition observation
-> SHA-256 / structural fingerprint
-> reviewed extractor or mapping
-> deterministic normalization/extraction
-> immutable derived observations
-> source-change events
-> dependency graph
-> scoped reanalysis requests
-> supporting / contradicting evidence
-> trust decision
-> explainable recommendation
```

The system is designed for changing upstream sources: new bosses, phases, reports, fields, routes and meta are normal events, not exceptional manual migrations.

## 4. Implemented foundation

- localhost FastAPI planner;
- DuckDB migrations `0001`–`0010`;
- immutable raw archive;
- retrieval/acquisition observations;
- privacy-safe JSON/HAR tooling;
- Source Observatory contract/schema/change/reanalysis foundation;
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

## 6. Network-first source discovery

Use real browser Fetch/XHR as the preferred discovery evidence.

```text
Network/HAR
-> scalar-free route inventory
-> contract review
-> Source Observatory capture
```

SPA JavaScript is supporting evidence when Network does not expose enough request construction detail.

Generic inventory:

```text
scripts/inventory_network_har.py
```

It must not publish query values, headers, cookies, response bodies or response record scalars.

## 7. Guild progression — current observed path

Historical helper/owner work and the old exact `/api/guilds/progression` POST hypothesis are superseded.

The current SPA still contains alternate rankings contracts:

```text
GET /api/guilds/progression/rankings
GET /api/guilds/progression/full-clears
GET /api/guilds/progression/rankings/{bossId}
```

A sanitized browser Network capture of the current `/guilds/progression` page on 2026-08-14 actually exercised:

```text
GET /api/phases
GET /api/guilds/phase-progression?phase=<value>&difficulty=<value>
```

Both returned JSON with HTTP 200.

The phase-progression response exposes the aggregate structural domains required for progression analysis:

```text
phase
board
totalBosses
bossList
perBossRankings
guilds
```

Current SPA request construction shows:

```text
phase      always mapped
board      optional
difficulty optional
```

Canonical browser-network receipt:

```text
evidence/real-data/coa-guild-phase-progression-browser-network.json
```

## 8. Dynamic source monitoring

Source Observatory should automatically detect low-cardinality source evolution such as:

```text
new phase
new boss
new location
new difficulty
request contract change
schema field add/remove/type change
```

High-cardinality guild/player/report IDs remain data observations and do not automatically become global source-change dimensions.

Each derived analysis declares dependencies. A relevant source change creates a scoped pending reanalysis request rather than rebuilding everything.

## 9. Current decision boundary

```text
Network-first discovery implemented: true
current phase-progression request observed in browser: true
phase-progression JSON structure observed: true
raw browser HAR versioned: false
current schema baseline persisted in user's local Observatory: pending
pagination semantics verified: false
termination semantics verified: false
completeness verified: false
ready for autonomous full guild crawl: false
planner scoring allowed from progression alone: false
```

## 10. Next product path

```text
persist phases + phase-progression browser observations locally
-> establish schema/dimension baseline
-> repeat later and prove automatic change detection
-> connect phase/boss/source changes to scoped reanalysis
-> generalize Network-first source discovery to reports/encounters/characters
-> Armory/talent-grid/BisBeard adapters
-> multi-report character identity
-> verified build/capability observations
-> encounter requirement models
-> dynamic attendance-aware roster completion
```

Do not hardcode today's boss/phase counts into product logic.

## 11. Development model

The agent performs GitHub/PR/CI/repository work directly whenever tools permit it. The user is involved only for Windows/local/private/browser boundaries the agent cannot access directly.

Private/raw files may be inspected for analysis. Publication/versioning remains separately controlled.

Use focused tests while iterating, one aggregate `scripts/verify_repo.py` before a meaningful push, then exact-head CI.
