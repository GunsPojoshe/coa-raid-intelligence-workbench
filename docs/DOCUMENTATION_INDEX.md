# Documentation index and authority map

Status: **canonical**  
Updated: **2026-08-28**

## Authority order

When documents disagree:

```text
1. executable code + reviewed config + migrations + scalar-safe real evidence
2. docs/CURRENT_PARADIGM.md
3. docs/PROJECT_STATE.md
4. docs/PROJECT_MASTER_CONTEXT.md
5. stable product/domain documents
6. maintained technical contracts
7. historical Git history
```

## Read first

```text
README.md
AGENTS.md
docs/CURRENT_PARADIGM.md
docs/PROJECT_STATE.md
docs/OFFICIAL_PUBLIC_API.md
```

## Canonical product/architecture documents

- `README.md` — repository/product entry point.
- `AGENTS.md` — trust, privacy and development rules.
- `docs/CURRENT_PARADIGM.md` — current source hierarchy and analytical architecture.
- `docs/PROJECT_STATE.md` — proven capabilities, open gaps and product boundary.
- `docs/PROJECT_MASTER_CONTEXT.md` — durable product/domain context.
- `docs/COA_TARGET_PRODUCT_DEFINITION.md` — target product definition.
- `docs/COA_DOMAIN_BOUNDARY.md` — CoA-only domain rules.
- `docs/ADR_011_LOCALHOST_ONLY.md` — localhost boundary.
- `docs/ADR_012_LOG_EVIDENCE_TRUTH_MODEL.md` — evidence/truth policy.

## Maintained source/data contracts

- `docs/OFFICIAL_PUBLIC_API.md` — official Ascension Logs public API role and contract.
- `docs/SOURCE_OBSERVABILITY_AND_REANALYSIS.md` — Source Observatory, dependencies and reanalysis.
- `docs/UPSTREAM_ASCENSION_LOGS_EVIDENCE.md` — pinned Companion evidence boundary.
- `docs/REAL_LOG_CAPTURE.md` — retained first-party report evidence pipeline.
- `docs/CURRENT_REPORT_RUNTIME_PARSER_STATUS.md` — current report parser/persistence status.
- `docs/CURRENT_REPORT_ANALYTICS_READ_MODELS.md` — report analytics read models.
- `docs/CURRENT_REPORT_ANALYTICS_API.md` — localhost report analytics API.
- `docs/CURRENT_REPORT_COMPARISON_READ_MODEL.md` — comparison boundary.
- `docs/LOCAL_WORKSPACE_BOUNDARY.md` / `docs/LOCAL_WORKSPACE_AUDIT.md` — local/private state rules.
- `docs/CI_OPERATIONS.md` — verification/CI policy.
- `docs/WINDOWS_DEVELOPMENT_ENVIRONMENT.md` — Windows operator environment.

## Fallback/reference documents

Browser/HAR and older mapping documents are retained only when they still describe reusable fallback tooling or a verified historical contract. They never outrank the official public API.

Examples:

```text
docs/BROWSER_OBSERVATORY.md
docs/INTERACTIVE_HAR_DISCOVERY.md
docs/ARMORY_MAPPING_REVIEW_V1.md
docs/REPORT_DISCOVERY_MAPPING_REVIEW_V1.md
docs/GUILD_WIDE_COLLECTION_CONTRACT.md
```

## Canonical real evidence ledger

Current high-value receipts:

```text
evidence/real-data/coa-public-api-catalog-real.json
evidence/real-data/coa-public-api-statistics-provenance-capture-real.json
evidence/real-data/coa-public-api-statistics-persistence-real.json
evidence/real-data/coa-public-api-statistics-profile-reanalysis-real.json
evidence/real-data/coa-public-api-population-coverage-real.json
evidence/real-data/coa-public-api-encounter-context-real.json
evidence/real-data/coa-public-api-encounter-comparator-real.json
evidence/real-data/coa-report-encounter-source-correlation-real.json
evidence/real-data/coa-report-encounter-population-binding-real.json
evidence/real-data/coa-current-roster-build-provenance-real.json
```

Receipts are scoped real-run evidence, not universal game contracts.

## Repository families

```text
src/coa_workbench/web/          product runtime/API/UI
src/coa_workbench/planner/      composition/planner primitives
src/coa_workbench/analytics/    deterministic analytics/review logic
src/coa_workbench/collector/    source contracts/acquisition/observability
src/coa_workbench/normalizer/   normalization
src/coa_workbench/storage/      DuckDB persistence/read models
scripts/                        maintained operators/reviews/verification
config/                         reviewed contracts/mappings
migrations/                     forward-only storage migrations
tests/                          deterministic coverage
evidence/real-data/             public-safe receipts
baseline/                       frozen workbook migration/reference exports
```

## Documentation maintenance rule

Architecture/source-priority/proven-state changes must update at least:

```text
README.md
docs/CURRENT_PARADIGM.md
docs/PROJECT_STATE.md
```

Update `AGENTS.md` when development/privacy/source rules change, and update the relevant technical contract when source semantics change.
