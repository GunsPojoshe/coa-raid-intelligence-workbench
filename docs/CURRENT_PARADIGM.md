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
```

## Encounter binding trust boundary — real proven

The selected report encounter is now independently machine-correlated from reviewed first-party report evidence:

```text
valid report/encounter URL shape: proven
operator-reviewed concrete boss/location/difficulty: retained input scope
exact boss name + location -> unique official /bosses record: proven
exact encounter-scoped aggregate capture: proven
exact same-location/no-boss comparator capture: proven
exact report + encounter identity from first-party encounter catalog: proven
report encounter -> selected boss identity: proven
report encounter -> selected difficulty: proven
boss encounter flag: proven true
```

Real source-correlation receipt:

```text
evidence/real-data/coa-report-encounter-source-correlation-real.json
```

Real correlation result:

```text
correlation version: report-encounter-source-correlation-v2
parser version: report-encounter-catalog-parser-v1
source kind: live_first_party_encounter_catalog
normalized encounter count: 1
reject count: 0
verified field contract count: 5
exact reference identity: true
boss field match: true
boss encounter flag: true
difficulty field match: true
boss source correlation: true
difficulty source correlation: true
complete: true
network requests: 1
persisted observation used: false
heavy encounter-detail used: false
events:read used: false
Browser/HAR used: false
historical difficulty-v4 heuristic used: false
planner scoring allowed: false
public release safe: true
```

The earlier heavy `/api/reports/{reportId}/encounters/{encounterId}` timeout remains transport evidence only. The successful proof used the compact reviewed encounter catalog instead.

## Current next gate

Bind the now machine-correlated report encounter to the already-proven encounter-scoped population context as one deterministic local trust result.

Target semantics:

```text
same locally selected report/encounter scope
+ source-correlation complete
+ encounter population context complete
+ matched same-location comparator complete
-> scalar-safe encounter-context binding receipt
```

This gate must not infer mechanics, player identity, capability or roster value. It exists only to close provenance between machine-correlated encounter identity and the descriptive population context already collected for that scope.

After that:

```text
separately prove player identity / current build evidence
separately prove encounter mechanic / requirement semantics
only then construct capability and composition-fit reasoning
planner scoring remains blocked
```

Do not repeat population coverage, encounter-context, comparator or report-correlation captures merely because a session restarted.

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
class/spec names
metric/parse-share scalar values
raw IDs/paths
request/schema/profile fingerprints
DuckDB/raw payloads
```

Planner scoring remains fail-closed.
