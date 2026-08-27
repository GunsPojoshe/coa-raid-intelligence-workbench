# Documentation index and authority map

Status: **canonical**  
Updated: **2026-08-27**

The repository contains live operating documentation and historical milestone evidence. This index prevents an old handoff from overriding the current architecture.

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
docs/CURRENT_PARADIGM.md
docs/COA_DOMAIN_BOUNDARY.md
docs/COA_TARGET_PRODUCT_DEFINITION.md
docs/PROJECT_MASTER_CONTEXT.md
docs/PROJECT_STATE.md
docs/OFFICIAL_PUBLIC_API.md
docs/SOURCE_OBSERVABILITY_AND_REANALYSIS.md
docs/UPSTREAM_ASCENSION_LOGS_EVIDENCE.md
docs/LOCAL_WORKSPACE_BOUNDARY.md
docs/CI_OPERATIONS.md
docs/WINDOWS_DEVELOPMENT_ENVIRONMENT.md
docs/CONTINUATION_PROMPT.md
```

## Canonical current operating documents

- `AGENTS.md` — development/evidence/privacy operating rules.
- `README.md` — repository entry point and current high-level workflow.
- `docs/CURRENT_PARADIGM.md` — current source priority and evidence architecture.
- `docs/PROJECT_MASTER_CONTEXT.md` — durable product + architecture context.
- `docs/PROJECT_STATE.md` — current proven/blocked/next state.
- `docs/OFFICIAL_PUBLIC_API.md` — official aggregate/event contract and real aggregate proof.
- `docs/SOURCE_OBSERVABILITY_AND_REANALYSIS.md` — source profile/change/dependency/reanalysis architecture.
- `docs/CONTINUATION_PROMPT.md` — fresh-session resume instructions.
- `docs/NEXT_CHAT_HANDOFF.md` — compact current restart card.
- `docs/LOCAL_WORKSPACE_BOUNDARY.md` / `docs/LOCAL_WORKSPACE_AUDIT.md` — private workstation rules.
- `docs/CI_OPERATIONS.md` — verification and exact-head CI policy.
- `docs/WINDOWS_DEVELOPMENT_ENVIRONMENT.md` — supported local operator workflow.

## Current official-API real evidence ledger

```text
evidence/real-data/coa-public-api-catalog-real.json
  phase/boss catalog and stable boss_id counts

evidence/real-data/coa-public-api-statistics-capture-real.json
  historical bounded statistics capture receipt

evidence/real-data/coa-public-api-statistics-shape-real.json
  scalar-safe real response structure review

evidence/real-data/coa-public-api-statistics-provenance-capture-real.json
  successful provenance-aware bounded capture

evidence/real-data/coa-public-api-statistics-persistence-real.json
  real exact normalization + DuckDB persistence + second-pass idempotence proof

evidence/real-data/coa-public-api-statistics-profile-reanalysis-real.json
  real no-network Source Observatory + source_endpoint_profile migration/reanalysis proof
```

The first aggregate slice is now proven through capture, normalization, persistence, source health and profile-scoped invalidation. Current next gate is bounded multi-profile population coverage.

`evidence/real-data/*.json` is an evidence ledger, not permanent configuration. Do not hardcode observed counts as universal contracts.

## Active source/acquisition contracts

- `docs/OFFICIAL_PUBLIC_API.md`
- `docs/UPSTREAM_ASCENSION_LOGS_EVIDENCE.md`
- `docs/SOURCE_OBSERVABILITY_AND_REANALYSIS.md`
- `docs/SOURCE_OBSERVATORY_BASELINE.md`
- `docs/SOURCE_OBSERVATORY_V1_STATUS.md`
- `docs/SCOPE_SCHEMA_CYCLE.md`
- `docs/SOURCE_FIELD_CORRESPONDENCE.md`
- `docs/REAL_LOG_CAPTURE.md`
- `docs/CURRENT_REPORT_RUNTIME_PARSER_STATUS.md`
- `docs/CURRENT_REPORT_ANALYTICS_READ_MODELS.md`
- `docs/CURRENT_REPORT_ANALYTICS_API.md`
- `docs/CURRENT_REPORT_COMPARISON_READ_MODEL.md`
- `docs/CROSS_REPORT_STRUCTURAL_BENCHMARK.md`
- `docs/CROSS_REPORT_EQUIVALENCE.md`

These remain authoritative within their proven scope but do not override the source-priority ladder.

## Stable product/domain documents

- `docs/COA_TARGET_PRODUCT_DEFINITION.md`
- `docs/COA_DOMAIN_BOUNDARY.md`
- `docs/ADR_011_LOCALHOST_ONLY.md`
- `docs/ADR_012_LOG_EVIDENCE_TRUTH_MODEL.md`

Historical product baselines retained for provenance:

```text
docs/PROJECT_BASELINE_v0.5.md
docs/PROJECT_BASELINE_v0.5.docx
baseline/
workbook/
```

## Integrity / audit documents

- `docs/PROJECT_INTEGRITY_AUDIT_2026-08-26.md`
- `docs/DOCS_OVERHAUL_PLAN.md`
- `scripts/audit_project_integrity.py`
- `scripts/inventory_local_workspace.py`

Local workspace audit is already completed for the reviewed checkpoint. The historical helper patch is preserved privately and classified as incomplete; do not request/apply it again without a new reason.

## Fallback / supporting discovery documents

- `docs/BROWSER_OBSERVATORY.md`
- `docs/INTERACTIVE_HAR_DISCOVERY.md`
- `docs/ARMORY_MAPPING_REVIEW_V1.md`
- `docs/REPORT_DISCOVERY_MAPPING_REVIEW_V1.md`
- `docs/GUILD_WIDE_COLLECTION_CONTRACT.md`
- `docs/E3_GUILD_PROGRESSION_EVIDENCE_STATUS.md`

Browser/HAR documents describe fallback tooling, not current Ascension Logs source priority.

## Historical experiments and snapshots

Examples:

```text
docs/DEVELOPMENT_CONCEPT_PIVOT_2026-08-19.md
docs/PARALLEL_WORKSTREAMS_2026-08-19.md
docs/DIFFICULTY_VALUE_BINDING.md
docs/DIFFICULTY_CONTEXT_BINDING.md
docs/DIFFICULTY_SEQUENCE_BINDING.md
docs/COA_RAID_UTILITY_BASELINE_2026-08-02.md
docs/IMPLEMENTATION_LOG.md
```

The difficulty-binding series is retained as negative evidence explaining why historical two-report equivalence remains unresolved. It is not a roadmap for a v4 heuristic.

## Repository implementation families

```text
src/coa_workbench/analytics/    deterministic analytics/review logic
src/coa_workbench/collector/    source contracts, acquisition, observability
src/coa_workbench/normalizer/   normalization
src/coa_workbench/planner/      trust-gated planner/application layer
src/coa_workbench/storage/      DuckDB persistence/read models
src/coa_workbench/web/          localhost application API/UI
scripts/                        durable operator/review commands
config/                         reviewed source/mapping configuration
migrations/                     forward-only DuckDB migrations 0001-0013
tests/                          deterministic coverage
evidence/real-data/             public-safe real receipts only
```

## Current aggregate implementation map

```text
config/coa_public_api_sources.yaml
src/coa_workbench/collector/public_api_stats_capture.py
src/coa_workbench/collector/public_api_archive.py
src/coa_workbench/collector/public_api_source_health.py
src/coa_workbench/collector/source_profile_reanalysis.py
src/coa_workbench/normalizer/public_api_statistics.py
src/coa_workbench/storage/public_api_statistics.py
src/coa_workbench/analytics/public_api_population_priors.py
src/coa_workbench/analytics/public_api_population_coverage.py
migrations/0013_public_api_statistics.sql
scripts/capture_current_public_api_statistics.py
scripts/persist_public_api_statistics.py
scripts/capture_public_api_population_coverage.py
```

## Current aggregate operating state

```text
single-slice real capture/persistence: proven
aggregate Source Observatory/Health: proven
source_endpoint_profile migration: proven
legacy broad aggregate source_endpoint dependency: inactive
bounded population coverage v1: implemented/tested; real operator run pending
```

Coverage v1 intentionally uses a small fixed profile set and does not crawl boss/location/week/realm/class/spec combinations merely for completeness.

## Documentation maintenance rule

A meaningful architecture/source-priority/proven-state shift must update at least:

```text
docs/CURRENT_PARADIGM.md
docs/PROJECT_STATE.md
docs/CONTINUATION_PROMPT.md
README.md
```

If source/access/privacy behavior changes, also update `AGENTS.md` and the relevant technical contract. Historical snapshots should normally remain unchanged and be classified here rather than rewritten.
