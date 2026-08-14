# Фактическое состояние проекта

Дата актуализации: **2026-08-14**.

## GitHub

Active branches:

```text
main
e2/log-evidence-refactor
e3/real-log-capture
```

PR #7 remains Draft: `e3/real-log-capture -> e2/log-evidence-refactor`.

Newer HEAD/CI must always be checked live.

## Product target

CoA-only localhost-first evidence-first raid intelligence platform.

Main product question:

> Почему конкретный человек нужен именно текущему составу?

The platform must remain adaptive to new bosses, phases, fields, logs and source contracts. Source
change handling must be automatic, scoped and provenance-preserving rather than implemented as
one-off collectors.

## Network-first Source Observatory

Canonical source path:

```text
browser/network observation
-> reviewed contract
-> immutable RawArchive
-> acquisition observation
-> schema/dimension observation
-> source change event
-> artifact dependency
-> scoped reanalysis
-> Source & Analysis Health
```

SPA/static evidence is supporting evidence, not a replacement for current browser Network observations.

Generic dynamic-template ingestion is disabled. Dynamic browser paths are accepted only after
cross-contract corroboration and exact known-static-route exclusion. Dynamic path values remain
local/private.

## Progression baseline

Current real browser-origin progression baseline:

```text
GET /api/phases
GET /api/guilds/phase-progression?phase=<value>&difficulty=<value>
```

Both are persisted locally as immutable captures with schema/dimension observations.

Historical guessed `POST /api/guilds/progression` remains superseded. Archived SPA alternate GET
contracts remain reviewed but are not current-runtime evidence.

## Reports-list baseline

Real `/reports` Network observation and local replay persisted:

```text
reports_public_api
reports_public_filter_options_api
reports_queue_status_api
```

Current derived dimension state:

```text
observed dimension endpoints: 3
active source_endpoint dependencies: 3
dimension names represented: 5
dimension values represented: 49
pending reanalysis requests: 0
```

The earlier `queue-status -> /api/reports/{reportId}` collision was repaired locally without deleting
raw objects or raw fetch observations.

## Current report runtime

A browser Network capture of one concrete report plus one selected encounter has been fully consumed by
the reviewed Source Observatory.

Current runtime families actually observed and persisted:

```text
GET /api/reports/{reportId}
GET /api/reports/{reportId}/encounters?includeTrash=...
GET /api/reports/{reportId}/combatants-roster?encounterIds=...
GET /api/reports/{reportId}/encounters/{encounterId}/throughput-timeline?...
GET /api/reports/{reportId}/character_damage_taken_abilities?...
GET /api/reports/{reportId}/character_spell_healing?...
```

Profile-aware replay result:

```text
dynamic routes resolved: 6
dynamic concrete paths: 9
reviewed route observations: 18
Source Health endpoints: 11
captured endpoints: 11
acquisition-problem endpoints: 0
pending reanalysis requests: 0
```

Historical exact routes remain reviewed but were not observed in this current capture:

```text
GET /api/reports/{reportId}/encounters/{encounterId}
GET /api/reports/{reportId}/encounters/{encounterId}/combatants-info
```

They must not override the current runtime model.

## Private current-report payload review

The same private browser HAR has now been inspected as source data, not only as route evidence.

Public scalar-free receipt:

```text
evidence/real-data/coa-current-report-private-structure-review.json
```

Observed report slice:

```text
report encounters: 19
encounter-catalog rows: 19
roster characters: 25
roster snapshots: 29
throughput responses: 12
```

The current `/combatants-roster` response already embeds the build-enrichment families previously
studied through historical `combatants-info`:

```text
player / guild / instance
specialization
resolved_ca_talent_ranks
hero_build
talent-grid tree entries
gear
resolved item/enchant/set/gems
resolved BisBeard metadata
```

Across all 29 reviewed snapshots, three independently present talent structures had exactly the same
entry-ID membership:

```text
resolved_ca_talent_ranks.cao_id
hero_build[].entry_id
talents.trees[].talents[].entry_id
```

The current parser therefore performs the join only under this invariant and fails closed on a
mismatch.

Current scalar-free parser counts from the private capture:

```text
characters:              25
snapshots:                29
joined talent entries:  1466
gear slot observations: 491
resolved item rows:      490
resolved BisBeard rows:  490
```

`character_spell_healing` and `character_damage_taken_abilities` are also confirmed as report-level
analytical maps with large numeric-key dictionaries. Raw map keys and source scalar values remain
private.

## Report parser compatibility

The existing verified mapping:

```text
config/mappings/coa_report_detail_v1.json
```

still matches every promoted report/encounter selector and reviewed JSON type in the current response.
The old sample-specific whole-payload fingerprint/count gates are not reusable because the live report
contains additive fields and a different encounter count.

`compatible_normalization.py` now uses the manually verified field contracts as the generic gate:

```text
verified selected field remains type-compatible -> normalize
mapped field missing/type-changed              -> fail closed
new unrelated upstream field                   -> ignore for this mapping
```

This is parser compatibility only. It does not promote gameplay semantics or planner scoring.

## Throughput schema-profile correction

The first persisted current-report replay produced false schema churn because `throughput-timeline` is
a multi-mode endpoint.

Profile-unaware state:

```text
open source-change events total: 799
throughput endpoint: 789
all other endpoints combined: 10
```

Registry schema v6 defines reviewed response-shaping keys:

```text
schema_profile_keys:
  - metric
  - perspective
```

A bounded repair superseded only the legacy profile-unaware schema-change events:

```text
superseded legacy events: 788
field_added:              256
field_removed:            515
field_type_changed:         7
schema_changed:             10
linked downstream reanalysis requests: 0
```

Raw objects, raw fetch observations, source captures and schema snapshots were preserved.

After the profile-aware replay:

```text
open source-change events total: 34
throughput endpoint: 24
all other endpoints combined: 10
pending reanalysis requests: 0
```

The remaining throughput observations must not yet be interpreted as 24 upstream changes. The private
HAR shows that even after profile partitioning and numeric-key normalization, one profile has two
legitimate field-presence variants across encounters. Optional/data-dependent field presence therefore
needs cycle/profile aggregation before `field_removed` becomes a reliable alarm.

## Dynamic numeric object keys

Current payloads use numeric object keys as map indexes/IDs in throughput, healing, damage-taken, gear
and hero-build structures.

Literal values such as those keys are now normalized to a structural wildcard:

```text
numeric-object-key-wildcard-v1
{integer-key}
```

This normalization is implemented in two places:

```text
HAR inventory v2 structural fingerprints
Source Observatory snapshot path/fingerprint comparison
```

Source Observatory preserves historical rows. Legacy literal numeric paths are normalized only in
memory when used as a previous comparison baseline. Replaying the exact same raw observation returns
the already persisted snapshot instead of trying to create a second snapshot under the new algorithm.

Synthetic integration proves:

```text
legacy /series/123/... + new /series/999/... with the same structure
-> no false source change
```

A later independent real report capture is still required before claiming multi-report production
proof.

## Generic current-report derived persistence

The current report now has a deterministic observation-only derived persistence path:

```text
current browser HAR
-> exact correlated one-report slice
-> verified compatible report normalization
-> current combatants-roster/build parser
-> exact persisted Source Observatory capture provenance
-> canonical_entity_observation envelope
-> completed analysis_run
```

Real local proof on the reviewed current report completed successfully:

```text
derived observations: 2031

current_report_observation:              1
current_encounter_observation:          19
current_roster_character_observation:   25
current_roster_snapshot_observation:    29
current_talent_entry_observation:     1466
current_gear_slot_observation:         491
```

The immediate replay of the same real corpus proves idempotence:

```text
first run: inserted 2031 / matched 0
replay:    inserted 0    / matched 2031
```

Core canonical report/encounter tables were not promoted or mutated. Mechanic semantics and planner
scoring remain disabled. Report-scoped reanalysis dependencies are intentionally not registered yet.

Public safe receipt:

```text
evidence/real-data/coa-current-report-derived-persistence-real.json
```

The receipt excludes HAR/raw bodies, source IDs/names, query values, source-capture IDs and private
input/output fingerprints.

## Source & Analysis Health

Localhost endpoints:

```text
/source-health
/api/source-health
```

Latest real local summary after the current-report derived persistence proof:

```text
endpoint count: 11
captured endpoint count: 11
open change event count: 34
acquisition-problem endpoint count: 0
active dependency count: 3
completed analysis runs: 3
pending reanalysis requests: 0
```

The derived persistence run changed only `completed analysis runs: 2 -> 3`; source changes,
dependencies and pending reanalysis remained unchanged.

## Current boundary

```text
Network-first discovery implemented: true
browser-origin phases/progression persisted: true
reports public/filter-options/queue-status persisted: true
false report-detail collision cleaned locally: true
correlated dynamic resolver implemented: true
current report/encounters/roster/throughput/damage/healing runtime persisted: true
private current-report payload structures inspected: true
current report verified-field compatible normalization: implemented
current combatants-roster parser: implemented
current talent three-way structural join: implemented
current roster contains resolved BisBeard observations: true
reviewed schema-profile mechanism implemented: true
legacy profile-unaware throughput churn repaired locally: true
Source Observatory numeric-key path normalization: implemented
legacy numeric-key compatibility synthetic integration: proven
real multi-report numeric-key proof: false
generic current-report derived persistence: implemented
real current-report derived persistence: proven
real current-report derived persistence idempotence: proven
profile-cycle optional-field aggregation: pending
safe report-scoped reanalysis dependencies: pending
real later upstream change -> scoped reanalysis proven: false
ready for autonomous full source coverage: false
planner scoring promoted automatically: false
```

## Next product work

The transport/discovery and current-report observation persistence loops are sufficiently proven for
this report slice. Do not create another browser capture merely to re-prove the same routes or parser.

Next:

```text
aggregate schema observation per endpoint/profile cycle so data-dependent optional fields do not churn
-> register report-scoped provenance/reanalysis dependencies
-> add deterministic throughput/healing/damage read models
-> expand rankings/statistics/characters
-> Armory/talent-grid
-> BisBeard
```

A new browser capture is required only when a new source surface must be observed, an existing contract
changes, or a later independent report is deliberately used as a generalization proof.
