# Scope-aware schema cycles

## Why this exists

Current-report routes are high-cardinality path-scoped resources. Two different `reportId` values may
legitimately return different optional structures without the upstream API contract changing.

Comparing the latest response from report B with the previous response from report A therefore creates
false source-change events.

`scope-schema-cycle-v1` makes the reviewed path scope part of the schema baseline boundary without
publishing path values or their private fingerprints.

## Partitioning

For every route with `scope_path_keys`, one cycle is built for:

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
distinguished by `metadata_json.scope_schema_cycle_aggregated=true` and use a domain-separated opaque
partition key in `observation_profile_key`.

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

## Safety boundary

This mechanism does not:

- infer report, encounter, player, spell, or mechanic semantics from opaque values;
- publish report IDs, scope fingerprints, query values, raw bodies, or schema fingerprints;
- convert source observations into planner scoring;
- rewrite immutable raw or exact-schema evidence.

It only changes which observations are valid peers for schema-change detection.
