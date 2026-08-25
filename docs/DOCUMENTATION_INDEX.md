# Documentation index and authority map

Status: **canonical**  
Updated: **2026-08-26**

The repository contains both live operating documentation and historical milestone evidence. This index prevents an old handoff from silently overriding the current architecture.

## Authority order

When documents disagree, use this order:

```text
1. executable code + reviewed config + migrations + scalar-safe real evidence
2. docs/CURRENT_PARADIGM.md
3. docs/PROJECT_STATE.md
4. docs/PROJECT_MASTER_CONTEXT.md
5. stable product/domain documents
6. active technical contract documents
7. historical milestone / experiment documents
```

Always verify live GitHub branch/PR/CI state instead of trusting a stored SHA or run number.

## Read first

For a fresh continuation, read in this order:

```text
AGENTS.md
docs/CURRENT_PARADIGM.md
docs/COA_DOMAIN_BOUNDARY.md
docs/COA_TARGET_PRODUCT_DEFINITION.md
docs/PROJECT_MASTER_CONTEXT.md
docs/PROJECT_STATE.md
docs/OFFICIAL_PUBLIC_API.md
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
- `docs/CONTINUATION_PROMPT.md` — fresh-session resume instructions.
- `docs/NEXT_CHAT_HANDOFF.md` — concise handoff alias for the same current state.
- `docs/LOCAL_WORKSPACE_BOUNDARY.md` — private/untracked/ignored workspace rules.
- `docs/LOCAL_WORKSPACE_AUDIT.md` — exact local-file inventory procedure.
- `docs/CI_OPERATIONS.md` — verification and exact-head CI policy.
- `docs/WINDOWS_DEVELOPMENT_ENVIRONMENT.md` — supported operator workflow.

## Integrity / audit documents

- `docs/PROJECT_INTEGRITY_AUDIT_2026-08-26.md` — findings from the tracked-tree documentation/project audit and explicit local-only limitations.
- `docs/DOCS_OVERHAUL_PLAN.md` — scope record for the 2026-08-26 documentation overhaul.
- `scripts/audit_project_integrity.py` — machine-enforced canonical-document/migration/private-path integrity gate.
- `scripts/inventory_local_workspace.py` — read-only metadata inventory for ignored/untracked workstation state.

## Stable product/domain documents

These remain authoritative for product intent/domain boundaries unless explicitly superseded by a later canonical document:

- `docs/COA_TARGET_PRODUCT_DEFINITION.md`
- `docs/COA_DOMAIN_BOUNDARY.md`
- `docs/ADR_011_LOCALHOST_ONLY.md`
- `docs/ADR_012_LOG_EVIDENCE_TRUTH_MODEL.md`

Historical product baselines retained for provenance, not current state:

- `docs/PROJECT_BASELINE_v0.5.md`
- `docs/PROJECT_BASELINE_v0.5.docx`
- `baseline/`
- `workbook/`

## Active source/acquisition contracts

- `docs/OFFICIAL_PUBLIC_API.md` — preferred source for documented public API surfaces and the current aggregate statistics normalization/persistence contract.
- `docs/UPSTREAM_ASCENSION_LOGS_EVIDENCE.md` — pinned Companion/source evidence for client-state gaps.
- `docs/SOURCE_OBSERVABILITY_AND_REANALYSIS.md` — source schema/change/dependency architecture.
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

These contracts remain valid where their evidence scope still applies. They do not override the current source-priority ladder.

## Fallback / supporting discovery documents

- `docs/BROWSER_OBSERVATORY.md` — reusable fallback for undocumented gaps; not the primary Ascension Logs acquisition path.
- `docs/INTERACTIVE_HAR_DISCOVERY.md` — manual HAR/interaction fallback and historical E4 protocol.
- `docs/ARMORY_MAPPING_REVIEW_V1.md`
- `docs/REPORT_DISCOVERY_MAPPING_REVIEW_V1.md`
- `docs/GUILD_WIDE_COLLECTION_CONTRACT.md`
- `docs/E3_GUILD_PROGRESSION_EVIDENCE_STATUS.md`

## Historical experiments and milestone snapshots

The following are retained as dated evidence/history. Statements such as “current next gate” inside them are historical and must not be treated as live instructions:

- `docs/DEVELOPMENT_CONCEPT_PIVOT_2026-08-19.md`
- `docs/PARALLEL_WORKSTREAMS_2026-08-19.md`
- `docs/DIFFICULTY_VALUE_BINDING.md`
- `docs/DIFFICULTY_CONTEXT_BINDING.md`
- `docs/DIFFICULTY_SEQUENCE_BINDING.md`
- `docs/COA_RAID_UTILITY_BASELINE_2026-08-02.md`
- `docs/IMPLEMENTATION_LOG.md`
- `docs/ISSUE_E0_001_APPROVED_25_FIXTURE.md`
- `docs/START_30_MIN_RESULT.md`

The difficulty-binding series is especially important as negative evidence: it records why the historical two-report equivalence gate remains unresolved. It is not a roadmap for a v4 heuristic.

## Repository implementation families

Tracked implementation is organized as:

```text
src/coa_workbench/analytics/    deterministic analytics/review logic
src/coa_workbench/collector/    source contracts, acquisition, observability
src/coa_workbench/normalizer/   normalization
src/coa_workbench/planner/      planner/application layer; trust-gated
src/coa_workbench/storage/      DuckDB persistence/read models
src/coa_workbench/web/          localhost application API/UI
scripts/                        durable operator/review commands
config/                         reviewed source/mapping configuration
migrations/                     forward-only DuckDB migrations
tests/                          deterministic coverage
evidence/real-data/             public-safe real receipts only
```

The current tracked migration series reaches `0013_public_api_statistics.sql`.

Current aggregate-statistics implementation families:

```text
src/coa_workbench/normalizer/public_api_statistics.py
src/coa_workbench/collector/public_api_archive.py
src/coa_workbench/storage/public_api_statistics.py
src/coa_workbench/analytics/public_api_population_priors.py
scripts/persist_public_api_statistics.py
migrations/0013_public_api_statistics.sql
```

## Real-evidence rule

`evidence/real-data/*.json` is a public-safe evidence ledger, not configuration. Counts from one receipt must not be hardcoded as universal source contracts.

Current official-API real evidence includes catalog, capture and statistics-shape receipts. The aggregate parser/persistence/read model is implemented and deterministic-test verified, but a real persistence receipt is intentionally absent until one new provenance-aware bounded `/statistics` capture is replayed twice.

Historical E3 report/difficulty receipts remain useful for their exact scope.

## Documentation maintenance rule

A meaningful architecture/source-priority shift must update at least:

```text
docs/CURRENT_PARADIGM.md
docs/PROJECT_STATE.md
docs/CONTINUATION_PROMPT.md
README.md
```

If source/access/privacy behavior changes, also update the corresponding technical contract and `AGENTS.md`. Historical snapshot documents should normally remain unchanged and be classified here instead of rewriting past evidence.
