# Cross-report structural benchmark

`cross-report-structural-benchmark-v1` is the first multi-report comparison layer over persisted current-report analytics.

It deliberately does **not** create a performance score, percentile, mechanic grade or planner score.

## Exact structural peer key

A candidate peer cohort requires exact equality of:

```text
report.zone
+ encounter_name
+ throughput metric
+ throughput perspective
```

No aliases, fuzzy matching or mechanic inference are used.

A candidate becomes `eligible_structural_peer` only when:

- at least two distinct persisted reports contribute the key;
- each contributing report has exactly one throughput profile for that key.

If the same report contributes multiple matching profiles, the cohort is retained as
`ambiguous_repeated_profile_per_report` and is not eligible for numeric comparison.

## Explicitly unverified boundaries

The v1 cohort does not claim:

```text
difficulty equivalence
cross-report player identity
metric mechanic meaning
numeric cross-report scoring
planner scoring
```

Those remain false in both the private model and the public-safe review.

This is intentional. Exact zone + encounter name + request profile is sufficient to prove that two reports contain structurally comparable slices, but not sufficient to assert identical difficulty or to merge a player identity across reports.

The second real report already proves generic ingestion across two independent report identities. The next local proof only measures how much exact structural overlap exists between those persisted reports; it does not perform another network capture.

## Local review

```powershell
uv run --no-sync python scripts/review_cross_report_benchmark.py `
  --output "$HOME\Desktop\coa-cross-report-benchmark-real.json"
```

The command performs no network requests. It builds the private benchmark twice from the local DuckDB and emits only scalar-safe counts and verification booleans.

The public review does not include report IDs, encounter IDs, character IDs/names, zone values, encounter names, metric/perspective values, player totals or private fingerprints.

## Source-health note

The second independent report raised the current open Source Observatory change-event count to 645 while pending reanalysis remained zero. This does not invalidate the report/analytics persistence proof, but it is treated as schema-observation noise until endpoint-level distribution is reviewed. The bundled real benchmark proof records only per-endpoint open-change counts so that this can be repaired without exposing private payload values.

## Next promotion boundary

Before numeric cross-report player benchmarking is allowed, the project must establish at least:

1. a defensible difficulty identity for both reports;
2. a defensible comparison unit for throughput values, including fight-duration handling;
3. an explicit cross-report character identity rule if longitudinal player aggregation is desired.

Until those are proven, the cross-report layer remains structural-only.
