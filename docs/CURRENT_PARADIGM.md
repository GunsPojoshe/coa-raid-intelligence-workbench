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

The selected report encounter is now independently machine-correlated and deterministically bound to the exact persisted population context used by the comparator:

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

Real binding result:

```text
binding version: report-encounter-population-binding-v1
report catalog source: archived_first_party_encounter_catalog
archived report catalog reused: true
report catalog observations: 1
existing public API persistence reused: true
network requests: 0
source correlation complete: true
encounter context complete: true
encounter context slices: 4
location comparator complete: true
location comparator slices: 4
differential built: true
matched records: 148
encounter-only records: 0
location-only records: 2
exact dimension match: true
temporal scope match: true
same private scope inputs reused: true
machine-correlated encounter population binding complete: true
player identity verified: false
mechanic semantics verified: false
site Tier List algorithm verified: false
planner scoring allowed: false
public release safe: true
```

The binding path was offline. It reused the successful archived first-party encounter catalog plus already-persisted official `/statistics` data. No Browser/HAR, `events:read`, historical difficulty heuristic or repeat acquisition was used.

## Current next gate — player/current-build identity

Encounter scope provenance is no longer the blocker. The next independent trust lane is to establish who the selected/current player is and what build evidence is current enough to support capability reasoning.

Required semantics:

```text
same concrete player observation can be identified deterministically
current-report actor/roster identity remains separate from cross-report identity
build/talent/gear evidence must carry its own source + freshness/provenance
name equality alone is not cross-report identity proof
absence of build evidence must fail closed
no population metric is promoted to player capability
mechanic semantics remain unproven
planner scoring remains blocked
```

Prefer already persisted first-party report evidence and pinned executable source before Browser/HAR. Do not request new external scope merely to repeat facts already available locally.

After player/build identity, independently prove encounter mechanic/requirement semantics. Only then combine capabilities, requirements, actual attendance and descriptive population context.

Do not repeat population coverage, encounter-context, comparator, report-correlation or binding proof merely because a session restarted.

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
raw IDs/paths
request/schema/profile fingerprints
DuckDB/raw payloads
```

Planner scoring remains fail-closed.
