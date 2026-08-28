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
6. active technical contract documents
7. historical milestone / experiment documents
```

Always verify live GitHub branch/PR/CI state rather than trusting stored SHAs/run numbers.

## Read first

```text
AGENTS.md
docs/DOCUMENTATION_INDEX.md
docs/CURRENT_PARADIGM.md
docs/PROJECT_MASTER_CONTEXT.md
docs/PROJECT_STATE.md
docs/OFFICIAL_PUBLIC_API.md
docs/CONTINUATION_PROMPT.md
docs/NEXT_CHAT_HANDOFF.md
```

## Canonical current operating documents

- `AGENTS.md` — evidence/privacy/development rules.
- `README.md` — repository entry point.
- `docs/CURRENT_PARADIGM.md` — current source priority and evidence architecture.
- `docs/PROJECT_MASTER_CONTEXT.md` — durable product/architecture context.
- `docs/PROJECT_STATE.md` — current proven/blocked/next state.
- `docs/OFFICIAL_PUBLIC_API.md` — official aggregate contract and real proofs.
- `docs/SOURCE_OBSERVABILITY_AND_REANALYSIS.md` — source profile/change/dependency architecture.
- `docs/CONTINUATION_PROMPT.md` — full restart instructions.
- `docs/NEXT_CHAT_HANDOFF.md` — compact restart card.
- `docs/LOCAL_WORKSPACE_BOUNDARY.md` / `docs/LOCAL_WORKSPACE_AUDIT.md` — local/private state rules.
- `docs/CI_OPERATIONS.md` — verification and exact-head CI policy.

## Current official-API real evidence ledger

```text
evidence/real-data/coa-public-api-catalog-real.json
  phase/boss catalog

evidence/real-data/coa-public-api-statistics-provenance-capture-real.json
  provenance-aware bounded /statistics capture

evidence/real-data/coa-public-api-statistics-persistence-real.json
  exact normalization + DuckDB persistence + idempotence

evidence/real-data/coa-public-api-statistics-profile-reanalysis-real.json
  Source Observatory + source_endpoint_profile reanalysis proof

evidence/real-data/coa-public-api-population-coverage-real.json
  bounded generic population coverage 4/4

evidence/real-data/coa-public-api-encounter-context-real.json
  bounded encounter-scoped context 4/4

evidence/real-data/coa-public-api-encounter-comparator-real.json
  matched same-location/no-boss comparator 4/4 and scalar-safe differential summary
```

Retained implementation anchors:

```text
migrations/0013_public_api_statistics.sql
scripts/capture_public_api_population_coverage.py
Source Observatory/Health
```

`evidence/real-data/*.json` is an evidence ledger, not permanent configuration. Observed counts are not universal contracts.

## Current aggregate operating state

```text
single-slice capture/persistence: proven
aggregate Source Observatory/Health: proven
source_endpoint_profile migration: proven
bounded population coverage v1: proven 4/4
bounded encounter context v1: proven 4/4
matched encounter/location comparator v1: proven 4/4
planner scoring: blocked
```

Current next gate:

```text
independent report encounter -> boss/difficulty source correlation
```

Do not cartesian-expand population collection and do not rerun already closed proofs merely because a session restarted.

## Stable product/domain documents

- `docs/COA_TARGET_PRODUCT_DEFINITION.md`
- `docs/COA_DOMAIN_BOUNDARY.md`
- `docs/ADR_011_LOCALHOST_ONLY.md`
- `docs/ADR_012_LOG_EVIDENCE_TRUTH_MODEL.md`

## Active source/acquisition contracts

- `docs/OFFICIAL_PUBLIC_API.md`
- `docs/UPSTREAM_ASCENSION_LOGS_EVIDENCE.md`
- `docs/SOURCE_OBSERVABILITY_AND_REANALYSIS.md`
- `docs/REAL_LOG_CAPTURE.md`
- `docs/CURRENT_REPORT_RUNTIME_PARSER_STATUS.md`
- `docs/CURRENT_REPORT_ANALYTICS_READ_MODELS.md`
- `docs/CURRENT_REPORT_ANALYTICS_API.md`
- `docs/CURRENT_REPORT_COMPARISON_READ_MODEL.md`

## Fallback/supporting discovery documents

- `docs/BROWSER_OBSERVATORY.md`
- `docs/INTERACTIVE_HAR_DISCOVERY.md`
- `docs/ARMORY_MAPPING_REVIEW_V1.md`
- `docs/REPORT_DISCOVERY_MAPPING_REVIEW_V1.md`
- `docs/GUILD_WIDE_COLLECTION_CONTRACT.md`

Browser/HAR documents describe fallback tooling, not current source priority.

## Historical experiments

Difficulty-binding experiments and dated milestone documents remain historical evidence. They do not authorize a new heuristic merely to force equivalence.

## Repository implementation families

```text
src/coa_workbench/analytics/    deterministic analytics/review logic
src/coa_workbench/collector/    source contracts/acquisition/observability
src/coa_workbench/normalizer/   normalization
src/coa_workbench/planner/      trust-gated planner/application layer
src/coa_workbench/storage/      DuckDB persistence/read models
src/coa_workbench/web/          localhost application API/UI
scripts/                        durable operator/review commands
config/                         reviewed source/mapping configuration
migrations/                     forward-only migrations
tests/                          deterministic coverage
evidence/real-data/             public-safe real receipts only
```

## Documentation maintenance rule

A meaningful architecture/source-priority/proven-state shift must update at least:

```text
docs/CURRENT_PARADIGM.md
docs/PROJECT_STATE.md
docs/CONTINUATION_PROMPT.md
README.md
```

If source/access/privacy behavior changes, also update `AGENTS.md` and the relevant technical contract.
