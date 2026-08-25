# CoA Raid Intelligence Workbench — canonical project context

Updated: **2026-08-26**.

## 1. Product goal

Build a localhost-first, evidence-first raid intelligence platform for **Conquest of Azeroth** that combines real attendance, verified player/build observations, encounter evidence and population context to explain composition decisions.

Primary question:

> **Почему конкретный человек нужен именно текущему составу?**

The product is not a permanent “optimal 25” list and not a raw DPS leaderboard. It must adapt to actual attendance and explain alternatives/tradeoffs.

## 2. Domain boundary

CoA-only. Bronzebeard/Classless/Mystic/Hero Architect/shared Ascension material is not a CoA fact without exact supporting evidence. See `docs/COA_DOMAIN_BOUNDARY.md` and `docs/COA_TARGET_PRODUCT_DEFINITION.md`.

## 3. Truth model

```text
observation != universal mechanic
field name != semantic proof
UI label != backend contract
character name != cross-report identity
one combat result != stable capability
population aggregate != planner recommendation
```

Planner trust is fail-closed.

## 4. Current evidence architecture

```text
strongest available source
-> reviewed source/request contract
-> immutable raw capture
-> acquisition observation
-> schema/profile/scope/dimension observation
-> deterministic normalization
-> provenance + artifact dependency
-> source-change detection
-> scoped reanalysis
-> reproducible analytics
-> Source & Analysis Health
-> planner reasoning only after explicit trust gates
```

Upstream change is normal. New phases, bosses, fields, routes and source shapes must not require report-specific parser forks.

## 5. Current source hierarchy

```text
1. official documented CoA Ascension Logs public API
2. official documented site semantics
3. pinned executable AscensionLogsCompanion source
4. persisted first-party report/API responses
5. narrow browser/network observation for undocumented gaps
6. structural inference only after stronger sources are exhausted
```

This is a priority order, not a single-source architecture.

## 6. Evidence lanes

### Official aggregate API

Preferred for documented population dimensions/priors:

```text
GET /phases
GET /bosses
GET /statistics
```

Real current-phase capture and scalar-safe shape review are complete. Exact statistics normalization/persistence is the next implementation gate.

### First-party report corpus

E3 has a generic report-specific pipeline with immutable capture, scope-aware schema cycles, deterministic derived persistence, combat analytics and local read models. Two independent reports passed the same generic path.

Historical cross-report difficulty/equivalence for that pair is still unresolved, so numeric comparison of those historical reports remains blocked.

### Pinned Companion source

Strong evidence for client-observed/build/gear/capture/telemetry structures. Executable code establishes client behavior; backend comments require corroboration.

### Browser/HAR

Reusable provider-neutral fallback for undocumented gaps. It is not the default Ascension Logs acquisition path and must not be used for anti-bot evasion.

## 7. Implemented platform foundation

```text
localhost FastAPI application
DuckDB persistence
forward-only migrations 0001-0011
immutable RawArchive
retrieval/acquisition observations
reviewed mappings and parsers
Source Observatory + change/reanalysis graph
source_dimension_index
Source & Analysis Health
report/encounter/actor/participant/aura normalization
current-report derived analytics/read models/API
privacy/public-release audit
Ubuntu + Windows CI
```

## 8. Important real E3 milestones retained

First report:

```text
derived observations: 2031, replay idempotent
analytics observations: 19660, replay idempotent
throughput points: 13244
```

Second independent report:

```text
derived inserted: 2920
analytics inserted: 28213
throughput points: 16907
```

Structural cross-report benchmark:

```text
reports: 2
input profiles: 45
eligible peer cohorts: 3
eligible profiles: 6
eligible ranked rows: 133
```

Scope-aware schema repair:

```text
false/legacy events superseded: 623
open source-change events: 645 -> 22
new scoped schema changes on replay: 0
pending reanalysis: 0 -> 0
```

These receipts prove exactly their scoped statements; they are not permanent source configuration.

## 9. Official public API current state

Reviewed OpenAPI:

```text
OpenAPI 3.1.0
API version 1.0.0
```

Real scalar-safe evidence:

```text
phase records: 3
active/current phase candidate: 1
boss records: 285
unique stable boss_id values: 285
/statistics: HTTP 200 and archived
statistics top-level entries: 21
max observed nested depth: 5
objects with documented metric fields: 83
statistics_normalization_ready: true
```

The public API does not document the site Tier List algorithm, Meta Builds/talents/gear, Armory or guild progression.

## 10. Privacy/publication boundary

Raw/private data is local by default. Public-safe receipts may expose static field names, endpoint codes, route templates, scalar-free structures, counts, booleans and algorithm versions.

Do not publish private report/encounter/player/guild identities, query values, dynamic class/spec keys, difficulty scalars, browser/session secrets, raw payloads or low-entropy hashes of private scalars.

API key default:

```text
data/private/coa-logs-api-key.txt
```

## 11. Local workspace boundary

GitHub cannot see ignored/untracked operator state. Unknown local files must be preserved and inspected rather than cleaned.

Exact read-only inventory:

```powershell
uv run --no-sync python scripts/inventory_local_workspace.py
```

See `docs/LOCAL_WORKSPACE_AUDIT.md`.

## 12. Branch/integration model

```text
main
└── e2/log-evidence-refactor        Draft PR #3
    └── e3/real-log-capture         Draft PR #7
        └── e4/interactive-har-discovery  Draft PR #9
```

E3 is the stable report-evidence baseline. E4 is the current source-discovery/official-API workstream. Its branch name is historical; Browser Observatory is only one fallback component.

The lower E2→main PR currently has integration conflict debt. Do not resolve it by blindly choosing one historical document version; preserve the newest canonical docs when the staged branch chain is eventually folded down.

## 13. Current product path

```text
exact StatisticsResponse parser
-> normalized population-statistics model
-> DuckDB persistence + idempotence proof
-> population-prior read model by documented dimensions
-> source/analysis health integration
-> combine with verified report/player/build evidence
-> separately prove identity, timing and mechanic semantics
-> encounter requirement/capability model
-> attendance-aware explainable roster recommendations
```

No HAR, Playwright session, difficulty-v4 heuristic or `events:read` scope is required for the current statistics gate.
