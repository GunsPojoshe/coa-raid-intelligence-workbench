# Difficulty sequence binding - E4 private ordered-context review

Status date: **2026-08-19**.

This reviewer follows `difficulty-context-binding-v2`. The real v2 receipt established two
facts at the same time:

```text
client pull contexts observed: 13
stable client difficulty pairs: 11
captured_for_pull_id == encounters[].id typed matches: 0
captured_for_pull_id no-match contexts: 13
```

The client pull ID is therefore useful as a private grouping/order key, but the observed values
are not backend encounter IDs.

## Pinned source semantics

Pinned Companion source:

```text
FangYuanWoW/AscensionLogsCompanion
0f63fe9c50b470402e3a29fba2e0322095856fd4
```

`Capture/EncounterTracker.lua` initializes `pullId` locally and increments it on every
`PLAYER_REGEN_DISABLED` combat enter. `SnapshotPipeline.lua` stamps the current local pull ID
and boss label onto outgoing CI data. This proves an ordered client combat-context counter; it
does not prove equality with any backend encounter identifier.

`Capture/LocalScan.lua` writes `captured_at = time() * 1000` for both local and inspect CIs.
Peer CIs can later be re-stamped with a newer pull/boss context without rebuilding their original
capture timestamp. For that reason v3 uses only `source == local` timestamps as an independent
client-order diagnostic and never uses peer timestamps for server binding.

## Existing private inputs only

No network request is performed. The reviewer reads already archived payloads for:

```text
report_combatants_roster_api
report_detail_api
report_encounters_api
```

The verified report-detail parser surface already exposes encounter `name`, `start_time`,
`end_time`, and ID fields. v3 uses the private server start-time field only to establish a
chronological structural ordering. Its backend semantics remain unverified.

## Relation candidate

For each report:

```text
client CI snapshots
-> group by private captured_for_pull_id
-> require integer pull keys from the pinned client counter
-> order by the private pull counter
-> keep exact stable boss labels

report detail encounter rows
-> require parseable start-time fields
-> order chronologically

client boss-label sequence
-> exact-name monotonic subsequence alignment
-> accept only when the entire alignment is unique
```

The exact boss label is a constraint inside an independently ordered sequence. It is not promoted
as verified identity. A repeated name that permits two or more monotonic alignments fails closed.

After a unique sequence alignment, v3 uses typed equality between the aligned report-detail
encounter ID and `report_encounters_api` ID as an additional server-internal relation candidate.
Only then does it compare available client `difficulty_name` against available server difficulty
fields.

## Public receipt

The receipt contains counts and booleans only, including:

```text
unique_full_sequence_alignment_report_count
ambiguous_full_sequence_alignment_report_count
sequence_linked_pull_count
sequence_linked_catalog_id_match_count
sequence_linked_difficulty_name_match_count
sequence_linked_difficulty_name_mismatch_count
shared_sequence_linked_boss_context_count
same_client_difficulty_pair_count
different_client_difficulty_pair_count
```

It excludes report IDs, pull IDs, encounter IDs, boss names, difficulty values, timestamps,
request URLs, raw payloads, private hashes, and raw paths.

## Decision boundary

Even a successful sequence relation remains a candidate:

```text
server_encounter_start_time_semantics_verified = false
sequence_relation_semantics_verified = false
final_cross_report_encounter_equivalence_verified = false
fight_duration_comparison_unit_verified = false
cross_report_player_identity_verified = false
numeric_cross_report_scoring_allowed = false
mechanic_semantics_verified = false
planner_scoring_allowed = false
```

A successful v3 result can be joined to the existing E3 structural peer cohorts. It does not
bypass the cross-report equivalence gate.

## Local command

```powershell
uv run --no-sync python scripts/review_difficulty_sequence_binding.py `
  --output data/exchange/out/coa-difficulty-sequence-binding.json
```

Upload only the scalar-safe output JSON for review.
