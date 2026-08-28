# Current report runtime parser status

Date: **2026-08-14**.

## Private runtime review

The private browser HAR for one current report was inspected directly. Raw bodies, IDs, names, query values, headers and cookies remain local/private.

The current report surface contains:

```text
report detail
encounter catalog
combatants roster
throughput timeline
character spell healing
character damage-taken abilities
```

Public scalar-free structural receipt:

```text
evidence/real-data/coa-current-report-private-structure-review.json
```

## Report mapping reuse

The existing verified mapping:

```text
config/mappings/coa_report_detail_v1.json
```

still matches every promoted report/encounter selector and reviewed JSON type in the current report response. The current response has additional fields and a different encounter count, so the old sample-specific whole-payload fingerprint/count gates must not be reused as a generic runtime gate.

`compatible_normalization.py` adds an additive-compatible parser boundary:

```text
verified field contracts unchanged -> normalize selected fields
mapped field removed/type changed   -> fail closed
new unrelated upstream field        -> ignore for this parser mapping
```

This does not promote gameplay mechanics or planner scoring.

## Current combatants roster

The current `/combatants-roster` response already contains the enrichment families previously studied through historical `combatants-info` observations:

```text
player
guild
instance
specialization
resolved_ca_talent_ranks
hero_build
talent trees / talent grid
gear
resolved item
resolved enchant / set / gems
resolved BisBeard metadata
```

The first current-runtime parser is:

```text
src/coa_workbench/collector/current_combatants_roster.py
```

It preserves source scalar values only in the private parse result and exposes a count-only public summary.

For the reviewed private capture:

```text
characters:              25
snapshots:                29
talent entries joined:  1466
gear slot observations: 491
resolved items:          490
resolved BisBeard rows:  490
```

For every one of the 29 snapshots, the entry-ID membership of all three independently present talent structures matched exactly:

```text
resolved_ca_talent_ranks
hero_build values
talents.trees[].talents[]
```

The parser therefore joins them only when this invariant holds and fails closed instead of silently dropping unmatched talent data.

## Dynamic object-key safety

The private payloads also prove that several current APIs use numeric object keys as map indexes/IDs:

```text
throughput series
healing source/target/spell maps
damage-taken target maps
roster gear
hero build
```

Literal numeric keys must not become public schema fingerprints or long-lived field paths.

`json_structure.py` defines:

```text
numeric-object-key-wildcard-v1
```

HAR inventory v2 removes numeric map keys before generating public structural fingerprints. Source Observatory schema snapshots now apply the same path normalization before fingerprinting and change comparison.

Backward compatibility is fail-safe rather than a history rewrite:

```text
legacy literal numeric paths are normalized in memory when selected as the previous snapshot
stored historical snapshot rows are not rewritten
replaying the exact same raw observation returns the already-persisted snapshot
new captures compare against normalized historical structure
```

Synthetic integration coverage proves that a legacy `/series/123/...` snapshot followed by the same shape under `/series/999/...` does not create a false source change.

A real second-report capture is still required before claiming multi-report production proof.

## Throughput optional field presence

After numeric-key normalization, the existing private HAR still contains legitimate structural variation inside one reviewed `metric/perspective` profile. Across the three private throughput profiles, normalized structural variant counts are:

```text
1
2
1
```

Therefore response-profile partitioning plus dynamic-key normalization is necessary but not sufficient to treat every per-response field removal as an upstream change. The next schema-observation refinement should aggregate optional field presence across one endpoint/profile observation cycle before declaring removals.

## Current boundary

```text
private current-report payload inspection: complete
current report verified-field compatibility: implemented
current combatants-roster parser: implemented
current talent three-way structural join: implemented
public HAR dynamic numeric-key fingerprints: normalized
Source Observatory numeric-key path normalization: implemented
legacy literal-key compatibility: synthetic integration proven
same-observation replay idempotency across snapshot normalization: proven
real multi-report numeric-key normalization: not yet proven
profile-cycle optional-field aggregation: pending
generic current-report derived persistence: pending
mechanic semantics: unverified
planner scoring: disallowed
```

## Next implementation

```text
aggregate schema observations per endpoint/profile cycle so data-dependent optional fields do not churn
-> add generic current-report derived persistence
-> persist report/encounter identity + roster/build observations
-> register artifact dependencies for report/roster/analytics derived datasets
-> add throughput/healing/damage analytical read models
-> prove the generalized path on a later independent report capture
```
