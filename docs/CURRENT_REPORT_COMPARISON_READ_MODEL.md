# Current report comparison read model

`current-report-comparison-read-model-v1` turns already persisted current-report observations into a
local query surface. It does not make network requests and does not promote mechanic semantics or
planner scoring.

## Inputs

The read model uses two already proven local persistence layers:

```text
current-report-derived-persistence-v1
current-report-analytics-persistence-v1
```

The latest completed analytics run is matched to the latest persisted report/encounter/roster
observation for the same private source report ID.

## Safe joins

The read model performs only evidence-backed structural joins:

```text
throughput character -> roster
  exact source_character_id equality

throughput series point -> character
  parser's exact within-response character-id match status

healing spell/source/target -> roster
  explicit character-id fields from the source row

damage-taken group -> roster
  exact source_group_key equality only
```

The damage-taken exact-key join is deliberately named as a key match. It does **not** claim that the
dynamic map key has verified target semantics.

## Comparative output

For throughput only, each exact request profile already identifies one report, one encounter, one
metric and one perspective. The read model therefore creates an observed-total leaderboard within
that exact profile:

```text
rank basis = upstream characters[].total_amount descending
```

This rank is a comparison of the upstream observed total only. It is not a performance grade, mechanic
evaluation or roster/planner score.

Damage and healing families are exposed as structural match counts at this stage. They are not summed
across opaque grouping boundaries.

## Local/private boundary

The query result intentionally contains local report/player identifiers and names. It is suitable for
the localhost application and private operator tooling, but it is **not public-release-safe**.

Public Git evidence must continue to exclude source report/encounter/player IDs, names, raw payloads,
query values and private fingerprints.

## CLI

List available persisted report analytics:

```text
uv run --no-sync python scripts/query_current_report_analytics.py --list
```

Query the latest report:

```text
uv run --no-sync python scripts/query_current_report_analytics.py
```

Query one canonical local report ID:

```text
uv run --no-sync python scripts/query_current_report_analytics.py --report-id <canonical-report-id>
```
