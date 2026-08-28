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
```

Retained implementation anchors:

```text
forward-only migrations 0001-0013
public_api_population_prior_v1
bounded public population coverage model/workflow
```

Current real comparator checkpoint:

```text
encounter context: 59 class summaries / 148 spec records / 1924 percentile values
location comparator: 59 class summaries / 150 spec records / 1950 percentile values
matched records: 148
encounter-only records: 0
location-only records: 2
records with avg delta+ratio: 148
records with median delta+ratio: 148
records with parse-share delta+ratio: 148
exact dimension match: proven
temporal day_number match: proven
missing spec zero coercion: false
source_endpoint_profile dependencies: 12
pending reanalysis: 0
actionable source changes: 0
health attention_required: false
planner scoring: false
```

The comparator holds phase, concrete difficulty, location, metric, role, bracket, damage mode and capture day fixed while omitting only `bossId`.

Public receipt:

```text
evidence/real-data/coa-public-api-encounter-comparator-real.json
```

## 7. Encounter binding boundary

The current encounter workflow establishes:

```text
valid report/encounter reference shape
operator-reviewed concrete boss/location/difficulty
unique official boss catalog match by reviewed boss+location
exact encounter-scoped aggregate context
exact matched same-location comparator
```

It does not yet independently establish from a report-side source:

```text
report encounter -> boss identity
report encounter -> difficulty
```

These are the next explicit trust gates.

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

Historical cross-report difficulty equivalence remains `insufficient_evidence`; numeric comparison of that historical pair stays blocked.

## 9. Pinned Companion source

```text
FangYuanWoW/AscensionLogsCompanion
main @ 0f63fe9c50b470402e3a29fba2e0322095856fd4
version 0.67.2
```

Executable code can establish client behavior and emitted structure. Comments/backend claims require corroboration.

## 10. Browser/HAR lane

Reusable fallback only for an exact undocumented gap after stronger sources are exhausted. No stealth, challenge bypass or anti-bot evasion.

## 11. Current next gate

Independently correlate the selected report encounter to boss and difficulty.

Implementation present, real proof pending:

```text
src/coa_workbench/analytics/report_encounter_source_correlation.py
scripts/capture_report_encounter_source_correlation.py
```

Priority:

```text
official documented report API if already accessible
-> official site semantics / persisted first-party report response
-> pinned Companion executable source
-> Browser/HAR only for the exact unresolved gap
```

Gate requirements:

```text
boss correlation and difficulty correlation are separate outcomes
fail closed on ambiguity or absent semantics
reuse already selected local report/encounter
publish scalar-safe booleans/counts/version markers only
no operator request for API key, RawArchive, DuckDB or private scalars
no historical difficulty-v4 heuristic
planner scoring remains blocked
```

## 12. Privacy/publication boundary

Raw/private data is local by default. Public-safe receipts may expose static field names, endpoint codes, route templates, scalar-free structures, counts, booleans and version names.

Do not publish private report/encounter/player identities, query values, dynamic class/spec keys, private dimension values, raw payloads, raw IDs/paths or low-entropy hashes of private scalars.

## 13. Local workspace boundary

Unknown ignored/untracked operator state must be preserved. The historical helper-analysis patch is incomplete private WIP because `guild_progression_js_lexical` is absent. Do not apply it as-is.

## 14. Branch/integration model

```text
main
└── e2/log-evidence-refactor        Draft PR #3
    └── e3/real-log-capture         Draft PR #7
        └── e4/interactive-har-discovery  Draft PR #9
```

Resolve lower-chain integration debt deliberately and preserve the newest canonical docs.

## 15. Current product path

```text
aggregate capture/normalization/persistence/idempotence: proven
aggregate Source Observatory/Health: proven
profile-scoped invalidation: proven
bounded population coverage: proven
encounter-scoped population context: proven
matched location comparator: proven
-> independent report encounter boss/difficulty source correlation
-> combine correlated encounter identity with population context
-> separately prove player identity and mechanic semantics
-> encounter requirement/capability model
-> attendance-aware explainable roster recommendations
```
