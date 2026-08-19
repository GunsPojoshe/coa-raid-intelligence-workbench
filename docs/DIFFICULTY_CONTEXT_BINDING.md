# Difficulty context binding v2 — pull-scoped private review

Status date: **2026-08-19**.

This reviewer follows the real `difficulty-value-binding-v1` run. It does not replace or reinterpret the v1 receipt.

## Why v2 exists

The real two-report v1 review observed:

```text
report_count = 2
roster_snapshot_count = 70
ambiguous_client_difficulty_report_count = 2
stable_difficulty_index_report_count = 0
stable_difficulty_name_report_count = 0
client_server_corroborated_report_count = 0
status = insufficient_evidence
```

That result rejects the working assumption that one client difficulty value can be required to remain stable across every Combatant Info snapshot in an entire report.

The current roster parser already preserves two stronger private capture-context fields:

```text
captured_for_pull_id
captured_for_boss
```

v2 therefore changes the unit of review from **report** to **private pull context**.

## Evidence path

```text
combatants-roster snapshots
  -> group by PRIVATE captured_for_pull_id
  -> require difficulty fields to be stable inside that pull context
  -> test PRIVATE typed scalar equality:
       captured_for_pull_id == encounters[].id
  -> independently test captured_for_boss == encounters[].name
  -> compare difficulty_name only after a relation candidate exists
  -> publish counts/booleans only
```

This is a relation test, not a semantic promotion. Even an exact numeric/string equality does not by itself prove what `captured_for_pull_id` means.

## Why request `encounterIds` is not used

The observed `/combatants-roster` request contract includes an `encounterIds` query key, but historical RawArchive request URLs are intentionally sanitized. Query values are replaced before persistence.

Therefore v2 does **not** attempt to reconstruct old `encounterIds` values from `request_url_sanitized` and does not manufacture a scope relation that the archive no longer contains.

If a future acquisition needs query-value scope, it must preserve that relation privately through an explicit reviewed mechanism rather than weakening public URL sanitization.

## Private checks

For every unique `captured_for_pull_id` inside each report, v2 measures:

```text
snapshot count
stable difficulty_index
stable difficulty_name
stable player_difficulty
stable map_id
stable instance name
stable captured_for_boss
```

It then builds private encounter indexes by:

```text
typed encounter id
text representation of encounter id
encounter name
```

The distinction is deliberate:

```text
typed_pull_id_exact_match
  = same JSON scalar type + same private scalar value

text_only_pull_id_match
  = same textual representation but different JSON scalar type
  = diagnostic candidate only
```

A text-only match is never promoted to verified identity.

For typed exact ID-linked contexts, v2 additionally records only aggregate counts for:

```text
client boss name == server encounter name
client difficulty_name == server encounter difficulty
```

Boss-name matching is also reported separately as a fallback diagnostic. It is never used as verified encounter identity by this reviewer.

## Cross-report diagnostic

v2 compares stable client difficulty pairs only for private encounter names that occur in both reports.

Two views are kept separate:

```text
client boss context
  captured_for_boss + stable client difficulty pair

server-linked encounter context
  typed pull-id relation -> server encounter name + stable client difficulty pair
```

Only the second view can produce:

```text
cross_report_difficulty_context_candidate_observed = true
```

Even then:

```text
final_cross_report_encounter_equivalence_verified = false
numeric_cross_report_scoring_allowed = false
planner_scoring_allowed = false
```

The candidate must still be joined to the existing E3 structural peer cohorts before the old equivalence gate can be revised.

## Privacy

The public receipt excludes:

```text
report IDs
pull IDs
encounter IDs
boss names
character IDs/names
difficulty values
instance names
map values
captured_at values
raw payloads/raw paths
request URLs/query values
private hashes
```

Only counts, booleans, version names, and reviewed basis descriptions are emitted.

## Implementation

```text
src/coa_workbench/analytics/difficulty_context_binding.py
scripts/review_difficulty_context_binding.py
tests/unit/test_difficulty_context_binding.py
```

## Local command

```powershell
uv run --no-sync python scripts/review_difficulty_context_binding.py `
  --output data/exchange/out/coa-difficulty-context-binding.json
```

Default inputs:

```text
data/warehouse/coa.duckdb
data/raw
```

The command performs no network acquisition.

## Next decision

```text
cross_report_context_candidate_observed
-> bind the private candidate to the existing E3 structural cohorts
-> implement guarded cross-report-equivalence v2 only if the relation survives

pull_context_id_relation_observed
-> relation exists, but shared comparable cross-report context is still missing/ambiguous
-> inspect aggregate mismatch/availability counters

client_pull_context_observed
-> client pull-scoped structure is usable but typed ID relation is absent
-> evaluate the next strongest existing private relation before requesting new capture

insufficient_evidence
-> existing archive lacks stable pull-scoped evidence
-> only then consider a narrow additional observation
```
