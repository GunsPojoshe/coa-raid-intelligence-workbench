# Scope-aware schema cycles

## Why this exists

Current-report routes are high-cardinality path-scoped resources. Two different `reportId` values may
legitimately return different optional structures without the upstream API contract changing.

Comparing the latest response from report B with the previous response from report A therefore creates
false source-change events.

`scope-schema-cycle-v1` makes the reviewed path scope part of the schema baseline boundary without
publishing path values or their private fingerprints.

## Partitioning

For every reviewed route with a schema scope, one aggregate cycle is built for:

```text
reviewed path scope
+ optional reviewed response profile
+ one observed HAR cycle
```

For current report routes the reviewed scope is `reportId`.

Throughput keeps its existing response profile boundary (`metric`, `perspective`) inside the report
scope. Responses from different encounters may therefore be unioned only when both the report scope
and reviewed response profile agree.

The private scope/profile partition is stored only as an opaque local key. Public summaries expose
only reviewed key names and counts.

## Compatibility with existing observations

Raw objects, raw fetch observations, `source_capture`, and exact `source_schema_snapshot` rows remain
immutable.

The scope cycle reuses `source_profile_schema_cycle` as the aggregate-cycle store. New rows are
distinguished by scope-cycle metadata and use a domain-separated opaque partition key in
`observation_profile_key`.

When historical member-level or legacy profile-cycle schema events are reaggregated, they are
superseded only if downstream reanalysis has not started. The new aggregate diff is calculated against
the latest historical schema from the same reviewed path scope. This preserves legitimate same-report
schema changes while removing cross-report churn.

## Reanalysis

Aggregate scope-cycle events still use the original source capture as provenance. The existing
`source_endpoint_scope` resolver therefore matches them to only artifacts with the same private path
scope.

A new report scope establishes a new baseline. It does not invalidate artifacts derived from another
report merely because its response contains different optional fields.

## Real two-report proof

The second independently persisted report exposed the exact defect this layer is designed to prevent.
Before scope-aware reaggregation, Source Health contained 645 open events, including 614 on
`report_combatants_roster_api` and 16 on `report_encounter_throughput_timeline_api`.

Replaying the already captured second-report HAR through `network-source-cycle-v9` produced:

```text
scope-schema endpoints processed:        6
member events superseded:              619
legacy profile events superseded:        4
total false/legacy events superseded:  623
new aggregate scoped schema changes:     0

open source-change events:          645 -> 22
pending reanalysis requests:          0 -> 0
active dependencies:                 21 -> 21
completed analysis runs:              6 -> 6
```

The same replay preserved the independent cross-report structural benchmark:

```text
reports:                     2
candidate peer cohorts:      3
eligible peer cohorts:       3
ambiguous peer cohorts:      0
eligible profiles:           6
eligible ranked player rows: 133
```

The remaining 22 open events are pre-existing Source Observatory signals; this replay created no new
scope-cycle aggregate schema event. They must still be interpreted by their own provenance/status and
must not be promoted automatically to upstream contract changes.

Public-safe receipt:

```text
evidence/real-data/coa-scope-schema-cycle-real.json
```

## Safety boundary

This mechanism does not:

- infer report, encounter, player, spell, or mechanic semantics from opaque values;
- publish report IDs, scope fingerprints, query values, raw bodies, or schema fingerprints;
- convert source observations into planner scoring;
- rewrite immutable raw or exact-schema evidence.

It only changes which observations are valid peers for schema-change detection.
