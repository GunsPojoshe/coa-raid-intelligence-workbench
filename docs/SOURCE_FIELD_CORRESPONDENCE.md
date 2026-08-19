# Source field correspondence — E4 structural bridge

Status date: **2026-08-19**.

This layer bridges two already separate evidence providers without promoting semantics:

```text
pinned upstream Lua field lineage
+ persisted Source Observatory schema snapshots
-> structural correspondence candidates
```

Current implementation:

```text
src/coa_workbench/collector/source_field_correspondence.py
scripts/review_source_field_correspondence.py
tests/unit/test_source_field_correspondence.py
```

## Purpose

The first target is the cross-report difficulty blocker.

The Companion executable source already establishes client-side field lineage such as:

```text
GetInstanceInfo
-> CI instance.* fields
-> telemetry map.* fields
```

The server-side question is separate: which related structures are actually visible in persisted Ascension Logs API schemas?

The correspondence reviewer compares the public upstream field paths against the already persisted scalar-free `source_schema_snapshot.path_types_json` rows for reviewed server endpoints.

Default endpoints:

```text
report_detail_api
report_encounters_api
report_combatants_roster_api
reports_public_api
```

Default focus tokens:

```text
difficulty
instance
map_id
```

## Match strength

Two structural candidate classes exist:

```text
exact_suffix
leaf_name
```

`exact_suffix` means a server schema path ends with the same public field-path segments as the upstream record. For example, an upstream `instance.difficulty_index` field and a server structure ending in `instance.difficulty_index` produce an exact structural candidate.

`leaf_name` is deliberately weaker: only the final field name matches.

Neither class proves that runtime scalar values are equal or that the backend copied/transformed the source field with any particular semantics.

## Privacy boundary

The reviewer never publishes full server paths. Only the suffix beginning at the first requested focus token is emitted.

This prevents dynamic/private prefixes such as report, encounter, character or other object-key identities from entering a public receipt.

The output also excludes:

```text
report ids
encounter ids
character ids/names
difficulty values
raw payloads
private hashes
```

Public upstream source paths and line numbers may be included because the pinned Companion source is public.

## Local command

After producing a scalar-safe upstream lineage review from the pinned Companion source tree:

```powershell
uv run --no-sync python scripts/review_source_field_correspondence.py `
  <UPSTREAM_LINEAGE_JSON> `
  --output data/exchange/out/coa-source-field-correspondence.json
```

The command performs no network requests. It reads the local DuckDB Source Observatory schema snapshots and the already generated upstream lineage JSON.

## Decision gate

Interpret the first difficulty-focused receipt as follows:

```text
exact CI instance.* suffixes observed on report_combatants_roster_api
-> client/server structural pass-through is a strong candidate
-> next prove runtime value binding per report/encounter

only report/encounter difficulty labels observed
-> backend transformation remains unresolved
-> compare exact local scalar values under a private reviewer

no relevant server schema path observed
-> current persisted corpus does not expose the client field structurally
-> only then consider one narrow additional source observation
```

Even a perfect exact-suffix match keeps:

```text
runtime_value_equivalence_verified = false
backend_transformation_semantics_verified = false
numeric_cross_report_scoring_allowed = false
planner_scoring_allowed = false
```

The next promotion step must use actual locally bound values, not field-name similarity.
