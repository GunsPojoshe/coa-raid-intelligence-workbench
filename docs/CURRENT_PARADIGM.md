# Current paradigm — CoA Raid Intelligence Workbench

Status: **canonical operating model**  
Updated: **2026-08-28**

## Product question

> **Почему конкретный человек нужен именно текущему составу?**

The answer must combine actual composition state, player/build evidence, encounter needs, population context and corroborated mechanics. It must not collapse into a DPS ranking.

## Evidence-first architecture

```text
strongest available source
-> reviewed source/request contract
-> immutable raw capture
-> acquisition observation
-> schema/profile/scope observation
-> deterministic normalization
-> provenance + dependency tracking
-> source change detection
-> scoped reanalysis
-> reproducible analytics
-> Source & Analysis Health
-> planner reasoning only after explicit trust gates
```

Never promote automatically:

```text
field name -> gameplay meaning
UI label -> backend contract
character name -> cross-report identity
one report -> universal mechanic
one structural match -> semantic equivalence
population metric -> planner recommendation
```

## Source priority

```text
1. official documented CoA Ascension Logs public API
2. official documented site semantics
3. pinned executable AscensionLogsCompanion source
4. persisted first-party report/API responses
5. narrow browser/network observation for exact undocumented gaps
6. structural inference only after stronger sources are exhausted
```

## Official aggregate lane — proven state

Self-service `stats:read` routes:

```text
GET /phases
GET /bosses
GET /statistics
```

Real-proven gates:

```text
phase/boss catalog
provenance-aware /statistics capture
exact StatisticsResponse normalization
DuckDB persistence + deterministic replay
population-prior read model
Source Observatory + Source & Analysis Health
source_endpoint_profile dependency migration
bounded population coverage v1: 4/4
bounded encounter context v1: 4/4
matched encounter/location comparator v1: 4/4
report encounter boss/difficulty source correlation v2: proven
machine-correlated encounter population binding v1: proven
```

Retained canonical status markers:

```text
population aggregate persistence/idempotence: proven
aggregate Source Observatory/Health: proven
profile-scoped aggregate invalidation: proven
bounded multi-profile population coverage: proven 4/4
```

Comparator real result:

```text
encounter context: 59 class summaries / 148 spec records / 1924 percentile values
location comparator: 59 class summaries / 150 spec records / 1950 percentile values
matched records: 148
encounter-only records: 0
location-only records: 2
records with avg/median/parse-share delta+ratio: 148
dimension match verified: true
temporal day_number match verified: true
missing spec treated as zero: false
source_endpoint_profile dependencies: 12
pending reanalysis: 0
actionable source changes: 0
health attention_required: false
planner scoring allowed: false
```

The comparator holds phase, concrete difficulty, location, metric, role, bracket, damage mode and capture day fixed and removes only `bossId`.

`local_parse_share`, avg/median deltas and ratios are descriptive population context. They are not the site's Tier List algorithm, mechanic proof, composition-fit proof or planner scoring.

Scalar-safe evidence:

```text
evidence/real-data/coa-public-api-population-coverage-real.json
evidence/real-data/coa-public-api-encounter-context-real.json
evidence/real-data/coa-public-api-encounter-comparator-real.json
evidence/real-data/coa-report-encounter-source-correlation-real.json
evidence/real-data/coa-report-encounter-population-binding-real.json
```

## Encounter binding trust boundary — real proven

The selected report encounter is independently machine-correlated and deterministically bound to the exact persisted population context used by the comparator:

```text
valid report/encounter URL shape: proven
operator-reviewed concrete boss/location/difficulty: retained private input scope
exact boss name + location -> unique official /bosses record: proven
exact report + encounter identity from first-party encounter catalog: proven
report encounter -> selected boss identity: proven
report encounter -> selected difficulty: proven
boss encounter flag: proven true
encounter-scoped aggregate context: proven 4/4
same-location/no-boss comparator: proven 4/4
same private selected scope inputs reused: proven
exact comparator dimensions: proven
comparator temporal day_number match: proven
machine-correlated encounter population binding: proven
```

Binding receipt:

```text
evidence/real-data/coa-report-encounter-population-binding-real.json
```

The binding path was offline. It reused the successful archived first-party encounter catalog plus already-persisted official `/statistics` data. No Browser/HAR, `events:read`, historical difficulty heuristic or repeat acquisition was used.

## Persisted report-scoped player/build provenance — real proven

A zero-network catalog review now proves deterministic player identity and observed build provenance for every currently persisted `current_report_observation` scope.

Real receipt:

```text
evidence/real-data/coa-current-roster-build-provenance-real.json
```

Real checkpoint:

```text
catalog version: current-roster-build-provenance-catalog-v1
persisted report scopes: 2
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
public release safe: true
```

What is proven is **report-scoped identity plus observed build linkage/provenance for the two persisted report scopes**. This does not prove that those observations belong to the selected encounter report, does not establish cross-report identity, and does not establish which snapshot is current/latest.

The zero complete timestamp-coverage count is an explicit freshness blocker, not a reason to discard the proven report-scoped identity/build linkage.

## Current next gate — selected-report build binding, then freshness semantics

The selected encounter report is not among persisted roster/build report scopes. Do not silently substitute another report and do not use name equality to bridge the gap.

Proceed in source-priority order:

```text
1. inspect existing local persisted/raw first-party evidence for the selected report
2. if matching roster/build evidence is already archived, normalize/persist it deterministically
3. otherwise inspect official documented site semantics and pinned executable Companion source for the narrow acquisition contract
4. use Browser/HAR only if an exact undocumented gap remains
5. after same-report build binding exists, establish timestamp/source semantics before selecting a latest/current build
```

Required fail-closed state:

```text
selected encounter report -> roster/build same-report binding: unproven
current/latest build freshness: unproven
cross-report identity: unproven
mechanic semantics: unproven
planner scoring: blocked
```

Do not infer `latest snapshot = current build` solely from row order or timestamp syntax. A source must establish what capture time means and what the snapshot is scoped to.

## Other retained lanes

E3 report persistence/analytics/generalization remains proven on two reports. Historical two-report difficulty equivalence remains `insufficient_evidence`; numeric comparison of that historical pair stays blocked.

Pinned Companion source remains:

```text
FangYuanWoW/AscensionLogsCompanion
main @ 0f63fe9c50b470402e3a29fba2e0322095856fd4
version 0.67.2
```

Browser/HAR remains fallback only. No stealth, challenge bypass or anti-bot evasion.

## Privacy boundary

Keep private/local:

```text
API key
query/profile values
report/encounter ids in public receipts
boss/location/difficulty values in public receipts
phase/metric/role values in public receipts
player identities in public receipts unless separately approved
class/spec names
metric/parse-share scalar values
build/talent/gear values
snapshot hashes
source capture ids
raw IDs/paths
request/schema/profile fingerprints
DuckDB/raw payloads
```

Planner scoring remains fail-closed.
