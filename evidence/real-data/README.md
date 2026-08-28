# Real-data evidence ledger

Updated: **2026-08-28**.

This directory contains public-safe receipts only. Raw payloads, query values, private IDs, HAR/browser state, API credentials and DuckDB remain local.

Receipts prove a scoped real run; they are not permanent configuration or universal game semantics.

## Canonical current receipts

```text
coa-public-api-catalog-real.json
coa-public-api-statistics-provenance-capture-real.json
coa-public-api-statistics-persistence-real.json
coa-public-api-statistics-profile-reanalysis-real.json
coa-public-api-population-coverage-real.json
coa-public-api-encounter-context-real.json
coa-public-api-encounter-comparator-real.json
coa-report-encounter-source-correlation-real.json
coa-report-encounter-population-binding-real.json
coa-current-roster-build-provenance-real.json
```

These receipts support the maintained aggregate/population/report-provenance chain. Other receipts in this directory may document earlier experiments or retained first-party evidence; they never override current source priority or canonical docs.

## Publication boundary

Allowed public-safe content includes static endpoint/field names, scalar-free shapes, counts, booleans and review/algorithm versions.

Do not publish secrets/tokens/cookies, raw payloads/HAR, private report/encounter/player/guild identities, query values, private build values, source capture IDs or private fingerprints.
