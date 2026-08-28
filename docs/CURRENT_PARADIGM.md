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
```

## Encounter binding trust boundary

Currently proven:

```text
valid report/encounter URL shape
operator-reviewed concrete boss/location/difficulty
exact boss name + location -> unique official /bosses record
exact encounter-scoped aggregate capture
exact same-location/no-boss comparator capture
```

Not yet proven:

```text
report encounter -> selected boss identity from independent report source
report encounter -> selected difficulty from independent report source
```

The current binding is operator-reviewed + official-catalog-bound, not independently machine source-correlated.

## Current next gate

Independently correlate the already selected report encounter to boss and difficulty using the reviewed current-report encounter catalog.

Implementation:

```text
src/coa_workbench/analytics/report_encounter_source_correlation.py
scripts/capture_report_encounter_source_correlation.py
```

Execution priority:

```text
persisted current_encounter_observation catalog evidence
-> small reviewed /api/reports/{reportId}/encounters?includeTrash=false response
-> fail closed
```

The first real operator attempt against the heavier `/api/reports/{reportId}/encounters/{encounterId}` payload reached HTTP response reading but timed out after two 30-second attempts. That is a transport result only, not boss/difficulty evidence. The heavy route is no longer the operator path and remains only as deterministic compatibility coverage.

The compact encounter catalog was already privately observed in the current-report runtime with `id`, `name`, `boss_id`, `difficulty`, `is_boss_encounter`, `zone` and related fields. Public structural evidence remains scalar-free.

Trust rules:

```text
exact report identity required
exactly one selected encounter row required
boss name and boss flag checked independently
difficulty checked independently
conflicting persisted observations fail closed
network does not override persisted conflicts
no events:read
no Browser/HAR
no historical difficulty-v4 heuristic
```

Do not request a new API scope merely to repeat facts already available in persisted first-party report evidence. The source-correlation gate remains unproven until a successful real scalar-safe receipt is versioned.

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
