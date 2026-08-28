# CoA Raid Intelligence Workbench — canonical project context

Updated: **2026-08-28**.

## 1. Product goal

Build a localhost-first, evidence-first raid intelligence platform for **Conquest of Azeroth** that combines actual attendance, verified player/build observations, encounter evidence and population context to explain composition decisions.

Primary question:

> **Почему конкретный человек нужен именно текущему составу?**

The product is not a permanent “optimal 25” list and not a raw DPS leaderboard. It must adapt to actual attendance and explain alternatives/tradeoffs.

## 2. Domain boundary

CoA-only. Bronzebeard/Classless/Mystic/Hero Architect/shared Ascension material is not a CoA fact without exact evidence.

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
-> schema/profile/scope observation
-> deterministic normalization
-> provenance + artifact dependency
-> source-change detection
-> scoped reanalysis
-> reproducible analytics
-> Source & Analysis Health
-> planner reasoning only after explicit trust gates
```

## 5. Source hierarchy

```text
1. official documented CoA Ascension Logs public API
2. official documented site semantics
3. pinned executable AscensionLogsCompanion source
4. persisted first-party report/API responses
5. narrow browser/network observation for exact undocumented gaps
6. structural inference only after stronger sources are exhausted
```

## 6. Official aggregate API lane

Preferred documented routes:

```text
GET /phases
GET /bosses
GET /statistics
```

Real-proven chain:

```text
catalog
-> provenance-aware statistics capture
-> exact normalization
-> DuckDB persistence/idempotence
-> population prior
-> Source Observatory
-> source_endpoint_profile dependency
-> profile-scoped reanalysis
-> bounded generic population coverage
-> bounded encounter context
-> matched same-location comparator
-> first-party report encounter boss/difficulty correlation
-> machine-correlated encounter population binding
```

Retained implementation anchors:

```text
forward-only migrations 0001-0013
public_api_population_prior_v1
source_endpoint_profile dependency
bounded public population coverage model/workflow
```

Public encounter receipts:

```text
evidence/real-data/coa-public-api-encounter-comparator-real.json
evidence/real-data/coa-report-encounter-source-correlation-real.json
evidence/real-data/coa-report-encounter-population-binding-real.json
```

## 7. Encounter provenance boundary — real proven through population binding

The current encounter workflow establishes exact first-party encounter identity, boss/difficulty correlation, bounded aggregate context, matched same-location comparator and machine-correlated encounter/population provenance binding.

The binding reused archived first-party report evidence and persisted official `/statistics` data in one zero-network local operation. No Browser/HAR or `events:read` was required.

## 8. First-party report lane

E3 retains a generic report pipeline with immutable capture, scope-aware schema cycles, deterministic derived persistence, combat analytics and local read models. Two independent reports passed the same generic path.

Current reviewed report source families include:

```text
GET /api/reports/{reportId}
GET /api/reports/{reportId}/encounters?includeTrash=...
GET /api/reports/{reportId}/combatants-roster?encounterIds=...
GET /api/reports/{reportId}/encounters/{encounterId}/throughput-timeline?...
GET /api/reports/{reportId}/character_damage_taken_abilities?...
GET /api/reports/{reportId}/character_spell_healing?...
```

The current-report encounter catalog is real-observed, real-correlated and archived for offline replay. Historical cross-report difficulty equivalence remains `insufficient_evidence`; numeric comparison of that historical pair stays blocked.

## 9. Persisted report-scoped player/build provenance — real proven

Scalar-safe receipt:

```text
evidence/real-data/coa-current-roster-build-provenance-real.json
```

The catalog review reused only persisted `canonical_entity_observation` data and performed zero network I/O.

Real checkpoint:

```text
persisted reports: 2
reviewed report scopes: 2
report scopes with roster: 2
report-scoped player identity complete: 2/2
observed build linkage complete: 2/2
source provenance complete: 2/2
observed build provenance complete: 2/2
characters: 52
snapshots: 70
talent entries: 3558
gear observations: 1195
complete timestamp coverage: 0/2
selected encounter reference present: false
selected reference same-report build binding proven: false
current build freshness verified: false
latest snapshot semantics verified: false
cross-report identity verified: false
player capability semantics verified: false
mechanic semantics verified: false
planner scoring allowed: false
```

This proves deterministic identity and observed build linkage **within each persisted report scope only**. It does not prove cross-report identity or selected-report linkage.

## 10. Current exact gate — selected-report build binding

The selected encounter report used by the encounter/population chain is not one of the two persisted roster/build report scopes.

Required next sequence:

```text
existing local persisted/raw first-party evidence for selected report
-> deterministic reuse/persistence if roster/build source already exists
-> official documented site semantics / pinned executable Companion contract if acquisition semantics are needed
-> narrow acquisition only for the missing selected-report evidence
-> Browser/HAR only for an exact remaining undocumented gap
-> prove same-report selected encounter -> roster/build binding
-> then establish timestamp/freshness semantics for latest/current build selection
```

Do not bridge reports by name equality or class/spec/build similarity.

The freshness gate is independently blocked because neither persisted report scope has complete observed timestamp coverage. Do not infer `latest snapshot = current build` from ordering alone.

## 11. Pinned Companion source

```text
FangYuanWoW/AscensionLogsCompanion
main @ 0f63fe9c50b470402e3a29fba2e0322095856fd4
version 0.67.2
```

Executable code can establish client behavior and emitted structure. Comments/backend claims require corroboration.

## 12. Browser/HAR lane

Reusable fallback only for an exact undocumented gap after stronger sources are exhausted. No stealth, challenge bypass or anti-bot evasion.

## 13. Privacy/publication boundary

Raw/private data is local by default. Public-safe receipts may expose static field names, endpoint codes, route templates, scalar-free structures, counts, booleans and version names.

Do not publish private report/encounter/player identities, query values, dynamic class/spec keys, private build/dimension values, raw payloads, snapshot hashes, source capture ids, raw IDs/paths or low-entropy hashes of private scalars.

## 14. Local workspace boundary

Unknown ignored/untracked operator state must be preserved. The historical helper-analysis patch is incomplete private WIP because `guild_progression_js_lexical` is absent. Do not apply it as-is.

## 15. Branch/integration model

```text
main
└── e2/log-evidence-refactor        Draft PR #3
    └── e3/real-log-capture         Draft PR #7
        └── e4/interactive-har-discovery  Draft PR #9
```

Resolve lower-chain integration debt deliberately and preserve the newest canonical docs.

## 16. Current product path

```text
aggregate capture/normalization/persistence/idempotence: proven
aggregate Source Observatory/Health: proven
profile-scoped invalidation: proven
bounded population coverage: proven
encounter-scoped population context: proven
matched location comparator: proven
report encounter boss/difficulty source correlation: proven
machine-correlated encounter + population-context provenance binding: proven
persisted report-scoped player identity: proven 2/2
persisted observed build provenance: proven 2/2
-> selected encounter report -> roster/build same-report binding
-> current/latest build freshness semantics
-> mechanic/requirement semantics
-> encounter requirement/capability model
-> attendance-aware explainable roster recommendations
```
