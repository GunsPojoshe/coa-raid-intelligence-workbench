# Difficulty value binding — E4 private runtime proof

Status date: **2026-08-19**.

This reviewer is the next gate after upstream Lua lineage and scalar-free source-field correspondence.

```text
pinned Companion executable evidence
-> upstream field lineage
-> persisted server schema correspondence
-> PRIVATE exact runtime value binding
-> scalar-safe public receipt
```

Implementation:

```text
src/coa_workbench/analytics/difficulty_value_binding.py
scripts/review_difficulty_value_binding.py
tests/unit/test_difficulty_value_binding.py
```

## Purpose

The old `cross-report-equivalence-review-v1` required:

```text
report.difficulty == reports[].highest_difficulty
```

The real two-report corpus did not provide usable values on those two exact surfaces, so the result was `insufficient_evidence`.

The Companion source now gives a stronger client-side starting point. Current `/combatants-roster` snapshots already preserve:

```text
instance.difficulty_index
instance.difficulty_name
instance.player_difficulty
instance.map_id
instance.name
captured_for_boss
```

The reviewer therefore tests whether those private client-derived values are stably bound to already persisted Ascension Logs server surfaces inside the same report.

## Inputs

No network request is performed.

The reviewer reads the existing local DuckDB and RawArchive for:

```text
report_detail_api
report_encounters_api
report_combatants_roster_api
reports_public_api
```

Report-scoped raw payloads are bound using the already archived sanitized request URL path. Report IDs remain private and are never emitted.

## Exact checks

Per report the reviewer measures:

```text
stable roster difficulty_index
stable roster difficulty_name
stable player_difficulty
stable map_id
stable instance name

roster difficulty_name == report.difficulty
roster difficulty_name == encounter catalog reportDifficulty
roster difficulty_name == stable encounter-row difficulty
roster difficulty_name == public highest_difficulty
```

When `captured_for_boss` and encounter-row `name` are both present, it also performs a private exact-name join and compares the two difficulty labels. Boss names are never published.

A report becomes `client_server_corroborated` only when:

```text
client difficulty_index is stable
+ client difficulty_name is stable
+ at least one server difficulty surface exactly equals the client name
+ no observed comparable server surface disagrees
+ no exact boss-name binding disagrees
```

For a cross-report candidate all target reports must be corroborated and must have exact private equality for both the stable client difficulty index and stable client difficulty name.

## What the result does NOT prove

Even a successful result keeps:

```text
final_cross_report_encounter_equivalence_verified = false
backend_transformation_semantics_verified = false
fight_duration_comparison_unit_verified = false
cross_report_player_identity_verified = false
numeric_cross_report_scoring_allowed = false
mechanic_semantics_verified = false
planner_scoring_allowed = false
```

The successful runtime binding is intended to become a corroborating input to a later `cross-report-equivalence` revision, not a shortcut around that gate.

## Privacy

The public receipt contains counts and booleans only. It excludes:

```text
report IDs
encounter IDs
boss names
character IDs/names
difficulty values
instance names
map values
raw payloads/raw paths
request URLs
private hashes
```

## Local command

```powershell
uv run --no-sync python scripts/review_difficulty_value_binding.py `
  --output data/exchange/out/coa-difficulty-value-binding.json
```

Default inputs:

```text
data/warehouse/coa.duckdb
data/raw
```

The command opens evidence queries read-only and performs no acquisition.

## Decision tree

```text
cross_report_client_server_correlated
-> integrate this corroboration into guarded cross-report equivalence v2
-> re-run the existing 3 structural peer cohorts

client_server_correlated_but_not_equal
-> reports are not equivalent on the observed client difficulty evidence
-> do not compare them numerically

insufficient_evidence
-> inspect the exact missing/mismatch counts
-> use one narrow additional observation only if the existing archive truly lacks the needed surface
```
