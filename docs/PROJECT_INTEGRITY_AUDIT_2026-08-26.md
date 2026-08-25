# Project integrity audit — 2026-08-26

Status: **tracked-repository audit complete; exact local-only audit pending operator manifest**.

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

Several canonical entry points still described the project primarily as an E3 six-report-family/browser-network effort and did not include the official public API, Companion evidence, local key boundary or the completed real `/statistics` capture.

Resolution: canonical state/handoff documents are rewritten around the new paradigm.

### 3. Browser Observatory documentation was over-promoted

The Browser Observatory document called itself the current E4 operating document and described a first real browser difficulty session as the next gate. That is obsolete.

Resolution: Browser Observatory is retained as a reusable fallback for undocumented gaps; official API and pinned executable source take precedence.

### 4. Public API documentation stopped before real evidence

The initial API document described the contract but still listed `/phases`, `/bosses` and first `/statistics` capture as future work.

Resolution: real catalog, capture and statistics-shape evidence are now part of canonical state. The next gate is exact StatisticsResponse normalization/persistence.

### 5. Migration/version summaries were stale

Older README text referred to migrations only through `0008`. The tracked migration series now reaches `0011_source_dimension_index.sql`.

### 6. Local workspace could not be claimed as remotely inspected

Ignored/untracked files are legitimate project state and are invisible to GitHub-only tooling. Existing docs already recognized this boundary but no standard manifest existed.

Resolution:

```text
scripts/inventory_local_workspace.py
docs/LOCAL_WORKSPACE_AUDIT.md
```

provide one read-only local inventory. Until that manifest is supplied, the exact local-only portion of this audit remains intentionally marked pending.

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

## Local audit completion condition

After pulling this documentation overhaul, run:

```powershell
uv run --no-sync python scripts/inventory_local_workspace.py
```

Then review the private manifest:

```text
data/private/local-workspace-inventory.json
```

Only after that manifest is inspected can the project state honestly say that tracked **and** local-only files have both been inventoried for the current workstation.
