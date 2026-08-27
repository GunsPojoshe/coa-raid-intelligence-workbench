# CoA Raid Intelligence Workbench — canonical project context

Updated: **2026-08-27**.

## 1. Product goal

Build a localhost-first, evidence-first raid intelligence platform for **Conquest of Azeroth** that combines actual attendance, verified player/build observations, encounter evidence and population context to explain composition decisions.

Primary question:

> **Почему конкретный человек нужен именно текущему составу?**

The product is not a permanent “optimal 25” list and not a raw DPS leaderboard. It must adapt to actual attendance and explain alternatives/tradeoffs.

## 2. Domain boundary

CoA-only. Bronzebeard/Classless/Mystic/Hero Architect/shared Ascension material is not a CoA fact without exact evidence. See `docs/COA_DOMAIN_BOUNDARY.md` and `docs/COA_TARGET_PRODUCT_DEFINITION.md`.

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

## 4. Evidence architecture

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

Upstream change is normal. New phases, bosses, fields, routes and response shapes must not require report-specific parser forks.

## 5. Source hierarchy

```text
1. official documented CoA Ascension Logs public API
2. official documented site semantics
3. pinned executable AscensionLogsCompanion source
4. persisted first-party report/API responses
5. narrow browser/network observation for undocumented gaps
6. structural inference only after stronger sources are exhausted
```

## 6. Evidence lanes

### Official aggregate API

Preferred for documented population dimensions:

```text
GET /phases
GET /bosses
GET /statistics
```

The first complete aggregate vertical slice is real-proven end to end: bounded current-phase capture with private request provenance, exact normalization, DuckDB persistence, second-pass idempotence, population-prior read model, Source Observatory replay, Source & Analysis Health and profile-scoped reanalysis dependency migration.

Current real normalized checkpoint:

```text
21 classes
62 specs
806 percentile values
62 population-prior rows
```

Real dependency/health checkpoint:

```text
raw_object dependency: registered
source_endpoint_profile dependency: registered
legacy broad source_endpoint dependency: inactive
pending reanalysis: 0
actionable open source changes: 0
health attention required: false
```

The current aggregate gate is bounded multi-profile population coverage, not more single-slice plumbing.

### First-party report corpus

E3 has a generic report-specific pipeline with immutable capture, scope-aware schema cycles, deterministic derived persistence, combat analytics and local read models. Two independent reports passed the same generic path.

Historical cross-report difficulty/equivalence for that pair remains unresolved, so numeric comparison of those historical reports stays blocked.

### Pinned Companion source

Strong evidence for client-observed/build/gear/capture/telemetry structures. Executable code establishes client behavior; backend comments require corroboration.

### Browser/HAR

Reusable provider-neutral fallback for undocumented gaps. Not the default Ascension Logs acquisition path and never an anti-bot-evasion mechanism.

## 7. Implemented platform foundation

```text
localhost FastAPI application
DuckDB persistence
forward-only migrations 0001-0013
immutable RawArchive
retrieval/acquisition observations
reviewed mappings and parsers
Source Observatory + change/reanalysis graph
source_dimension_index
source_profile_schema_cycle
official public statistics normalization/persistence/read model
official public statistics Source Observatory adapter
raw-object + source-endpoint-profile dependencies
profile-scoped aggregate reanalysis resolver
bounded public population coverage model/workflow
Source & Analysis Health
report/encounter/actor/participant/aura normalization
current-report derived analytics/read models/API
privacy/public-release audit
Ubuntu + Windows CI
```

Migration `0013_public_api_statistics` adds normalized aggregate persistence and `public_api_population_prior_v1`. No new migration was required for profile-scoped dependencies because the generic `artifact_dependency` and `reanalysis_request` schema already supports them.

## 8. Official API real proof

Reviewed contract:

```text
OpenAPI 3.1.0
API version 1.0.0
```

Real scalar-safe checkpoint:

```text
phase records: 3
active/current phase candidate: 1
boss records: 285
unique stable boss_id values: 285
provenance-aware /statistics: HTTP 200, archived
bytes: 21306
normalized classes: 21
normalized specs: 62
normalized percentile values: 806
second-pass replay: idempotent
population-prior rows: 62
Source Observatory integrated: true
profile dependency count: 1
legacy broad endpoint dependency count: 0
pending reanalysis: 0
```

Persistence provenance:

```text
analysis_run registered
raw_object dependency registered
source_endpoint_profile dependency registered
profile-scoped reanalysis resolver proven on real local replay
```

The public API does not document Meta Builds/talents/gear, Armory, guild progression or the site's Tier List algorithm. `total_parses` and workbench-derived `local_parse_share` remain descriptive aggregate evidence only.

## 9. Source Observatory integration for `/statistics`

The adapter replays private archived responses without another network call:

```text
RawArchive observation + private request dimensions
-> reconstruct reviewed request scope locally
-> source_capture
-> source_schema_snapshot
-> source_acquisition_observation
-> source_change_event if needed
-> source_endpoint_profile artifact dependency
-> profile-scoped reanalysis
-> Source & Analysis Health
```

All documented request-shaping `/statistics` query dimensions are schema-profile keys. Their values remain private; only the profile partition is used internally. This prevents incompatible request scopes from sharing one schema baseline.

Profile-local changes invalidate only matching aggregate artifacts. `request_contract_changed` remains endpoint-global. Events older than dependency registration cannot back-trigger a new artifact.

The initial registration can leave `endpoint_added` as an informational open event. Dedicated aggregate health treats warning/error changes as actionable while retaining informational baseline events for provenance.

## 10. Bounded population coverage v1

The first coverage expansion is deliberately small and resumable:

```text
required profile slices: 4
documented metric families represented: 3
role-qualified slices: 3
role-omitted slices: 1
current phase: selected privately from archived /phases
existing matching persisted slices: reused
network acquisition: missing slices only
failure behavior: stop after first incomplete capture
successful slice behavior: archive -> observe -> normalize -> persist -> deterministic replay
post-run: profile reanalysis reconciliation + Source & Analysis Health
bulk dataset mode: false
```

V1 intentionally does not fan out over boss/location/week/realm/class/spec. Those dimensions are future product-driven gates, not an automatic cartesian crawl.

Implementation:

```text
src/coa_workbench/analytics/public_api_population_coverage.py
scripts/capture_public_api_population_coverage.py
```

Real multi-profile execution is still pending.

## 11. Privacy/publication boundary

Raw/private data is local by default. Public-safe receipts may expose static field names, endpoint codes, route templates, scalar-free structures, counts, booleans and algorithm/version names.

Do not publish private report/encounter/player/guild identities, query values, dynamic class/spec keys, private dimension values, raw payloads, raw IDs/paths or low-entropy hashes of private scalars.

API key:

```text
data/private/coa-logs-api-key.txt
```

The key never enters RawArchive metadata. Exact `/statistics` request dimension values may be retained only in private RawArchive observation metadata as analytical provenance.

## 12. Important retained E3 milestones

First report:

```text
derived observations: 2031, replay idempotent
analytics observations: 19660, replay idempotent
```

Second report:

```text
derived inserted: 2920
analytics inserted: 28213
throughput points: 16907
```

Structural benchmark:

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
pending reanalysis: 0
```

## 13. Local workspace boundary

GitHub cannot see ignored/untracked operator state. Unknown local files must be preserved and inspected rather than cleaned. The historical helper-analysis patch has already been reviewed and classified as incomplete private WIP; do not re-request or apply it as-is.

## 14. Branch/integration model

```text
main
└── e2/log-evidence-refactor        Draft PR #3
    └── e3/real-log-capture         Draft PR #7
        └── e4/interactive-har-discovery  Draft PR #9
```

E3 is the stable report-evidence baseline. E4 is the current official-API/upstream-evidence workstream. Resolve lower-chain integration debt deliberately and preserve the newest canonical docs.

## 15. Current product path

```text
aggregate capture/normalization/persistence/idempotence: proven
aggregate Source Observatory/Health: proven
profile-scoped aggregate invalidation: proven
-> bounded multi-profile population coverage v1
-> validate coverage completeness + health + resumability on real local data
-> decide whether a second bounded population dimension expansion is product-necessary
-> combine with verified report/player/build evidence
-> separately prove identity, timing and mechanic semantics
-> encounter requirement/capability model
-> attendance-aware explainable roster recommendations
```

No HAR, Playwright session, difficulty-v4 heuristic or `events:read` scope is required for the current gate.
