# Project integrity audit — 2026-08-26

Status: **tracked repository and local-workspace integrity audit complete for the current workstation checkpoint**.

## Scope completed remotely

The full tracked Git tree on `e4/interactive-har-discovery` was structurally inventoried, including root files and the implementation/config/documentation/evidence families:

```text
.github/
baseline/
config/
data/
docs/
evidence/
migrations/
scripts/
src/
tests/
workbook/
```

Canonical documentation, source-acquisition modules, current scripts, config registries, migration inventory, public-safe real evidence, package metadata and CI rules were cross-checked against the current official-API/source-first paradigm.

## Main integrity problems found

### 1. Documentation authority was undefined

The repository contained many accurate historical milestone documents alongside stale files that still called old E3/browser steps “current”. This created a high risk that a fresh session would restart old work.

Resolution:

```text
docs/DOCUMENTATION_INDEX.md
docs/CURRENT_PARADIGM.md
```

now define authority/supersession and source priority.

### 2. README / project state / handoffs lagged behind E4

Several canonical entry points still described the project primarily as an E3 browser/network effort and did not include the official public API, Companion evidence, local key boundary or the completed real `/statistics` capture.

Resolution: canonical state/handoff documents are rewritten around the new paradigm.

### 3. Browser Observatory documentation was over-promoted

The Browser Observatory document called itself the current E4 operating document and described a first real browser difficulty session as the next gate. That is obsolete.

Resolution: Browser Observatory is retained as a reusable fallback for undocumented gaps; official API and pinned executable source take precedence.

### 4. Public API documentation stopped before real evidence

The initial API document described the contract but still listed `/phases`, `/bosses` and first `/statistics` capture as future work.

Resolution: real catalog, capture and statistics-shape evidence are now part of canonical state. The next gate is exact StatisticsResponse normalization/persistence.

### 5. Migration/version summaries were stale

Older README/docs referred to earlier migration ceilings. Exact CI verification exposed the current tracked sequence as:

```text
0001_initial.sql
...
0011_source_dimension_index.sql
0012_profile_schema_cycle.sql
```

The canonical documentation now records `0001-0012`, including `source_profile_schema_cycle`, and the machine integrity audit checks continuity through at least migration 12.

### 6. Local workspace required a real workstation inventory

Ignored/untracked files are legitimate project state and are invisible to GitHub-only tooling. The read-only inventory was run on the actual Windows checkout and its private manifest was reviewed.

Observed workstation state at the checkpoint:

```text
modified tracked files: 0
missing tracked files: 0
Git-visible untracked files: 1
```

The large initial nontracked count was dominated by generated/private state, including a dedicated `.venv-capture` environment and ignored build metadata. Inventory schema v3 skips this tooling noise and flags raw-transport candidates placed under local `data/exchange/out/`.

The private corpus contains expected local project families: RawArchive data, DuckDB, API credential file, Browser Observatory profile/session state, HAR inputs and generated exchange outputs. Their bodies were intentionally not bulk-read merely to prove workspace integrity.

One historical raw `.har` was detected under ignored `data/exchange/out/`. This does not make it public: `data/exchange/out/` is local staging, not a publication boundary.

### 7. The one Git-visible untracked patch was genuine but incomplete WIP

The sole untracked implementation candidate was reviewed directly after the metadata inventory.

Structural facts:

```text
patch lines: 2668
existing tracked files modified: 10
git apply --stat: +690 / -349
baseline blob IDs: match the current tracked helper-analysis lineage
obvious added credential/URL markers: none found
```

The patch contains valuable helper-analysis improvements: fail-closed multi-candidate definition selection, stronger structural selection evidence, executable-code versus literal/comment reference separation, template-interpolation handling and new ambiguity/lexical tests.

However, it makes three modules import a new shared scanner:

```text
coa_workbench.collector.guild_progression_js_lexical
```

Expected API:

```text
StructuralIndex
exact_symbol_positions
in_excluded_intervals
scan_javascript_structure
```

The shared module is absent from the patch and absent from tracked Git history. Therefore the savepoint is not self-contained and cannot be safely applied. The correct classification is:

```text
valuable incomplete historical WIP
preserve privately
not integrated into E4
not a blocker for the current official-API workstream
reconstruct only as a separate reviewed helper-analysis task if that lane resumes
```

Blindly recreating the missing scanner merely to satisfy imports would be contrary to the project's fail-closed evidence discipline.

### 8. Integrity rules were prose-only

Documentation drift could recur without failing normal verification.

Resolution:

```text
scripts/audit_project_integrity.py
scripts/verify_repo.py
.github/workflows/verify.yml
```

The machine audit now checks required canonical files/receipts, documentation authority markers, stale operating markers, migration continuity, tracked private paths and temporary staging files on Ubuntu and Windows verification paths.

## Current coherent architecture

```text
official documented API / official semantics / pinned client source
-> reviewed source contract
-> immutable RawArchive
-> structural schema/dimensions
-> deterministic normalization/persistence
-> source change + dependency graph
-> scoped reanalysis
-> reproducible analytics
-> Source & Analysis Health
-> planner reasoning only after explicit trust gates
```

Parallel evidence lanes are deliberate:

```text
public API     -> population aggregates/priors
report corpus  -> private report-specific analytics
Companion      -> client-state/source lineage
Browser/HAR    -> narrow fallback for undocumented gaps
```

Historical helper-analysis lexical WIP is preserved outside this active chain and does not redefine current source priority.

## Proven real API state at audit time

```text
phase records:                     3
active/current phase candidates:  1
boss records:                    285
unique stable boss_id values:    285
/statistics capture:              HTTP 200, archived
statistics top-level entries:     21
statistics max nested depth:       5
objects with documented metrics:  83
statistics normalization ready: true
```

No class/spec names or numeric source values are published by these receipts.

## Intentionally blocked claims

The overhaul does not change evidence status merely by changing documentation:

```text
historical two-report difficulty equivalence: unresolved
numeric historical cross-report scoring: blocked
cross-report player identity: blocked
site Tier List algorithm: undocumented
population prior persistence/idempotence: next gate
planner scoring: blocked
universal gameplay mechanic semantics: evidence-specific only
```

## Branch integration finding

Live PR checks during the audit showed:

```text
PR #9 E4 -> E3: mergeable
PR #7 E3 -> E2: mergeable
PR #3 E2 -> main: lower-chain integration conflict debt
```

Therefore a conflict warning in the staged chain must not be “fixed” by blindly selecting an older copy of the canonical docs. Draft integration remains a separate task from this documentation overhaul.

## Completion condition

The 2026-08-26 repository/workspace integrity audit is complete for the captured workstation checkpoint:

```text
tracked repository: audited
modified/missing tracked state: audited
Git-visible untracked implementation candidates: audited/classified
known ignored/private families: metadata-classified
raw private evidence bodies: intentionally outside bulk integrity inspection
```

No additional RawArchive, DuckDB, API-key, Browser Observatory or HAR upload is required to close this audit. A new local inventory is warranted only after material workspace changes or when a new unknown modified/untracked implementation candidate appears.
