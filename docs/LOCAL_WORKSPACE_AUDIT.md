# Local workspace audit

Status: **canonical operator procedure; 2026-08-26 workstation audit completed/classified**  
Updated: **2026-08-26**

GitHub contains the versioned implementation, but it cannot see ignored/untracked/private files or local working-tree changes on the operator workstation. Project-integrity reviews therefore use one bounded read-only local inventory instead of guessing from `git diff`.

## What the inventory does

`scripts/inventory_local_workspace.py` enumerates existing project files without reading their contents. It also reads Git path metadata so the handoff distinguishes the local working tree from the checked-in branch.

Private metadata includes:

```text
current branch and HEAD
relative path
size
mtime
tracked/nontracked state
modified tracked path state
Git-visible untracked path state
missing/deleted tracked paths
known privacy/generated class
file suffix
raw-transport candidates placed under data/exchange/out/
```

It skips Git internals and disposable tooling/build directories such as `.git/`, `.venv/`, `.venv-capture/`, `*.egg-info/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`, `playwright-report/` and `test-results/`.

It does **not**:

```text
read file bodies
read diff contents
read the API key value
hash private scalar content
delete/rename/modify project files
run git clean/reset/checkout
publish raw/private filenames in the public summary
```

## Outputs

Private exact manifest:

```text
data/private/local-workspace-inventory.json
```

Schema v3 contains exact local paths plus modified/untracked/missing tracked path lists and exact local paths for raw-transport candidates under `data/exchange/out/`. It stays ignored/local. It may be shared privately for analysis when an exact local audit is requested; sharing it does not make it publishable.

Public-safe summary:

```text
data/exchange/out/local-workspace-inventory-summary.json
```

The public-safe summary contains counts only, including:

```text
total existing files
tracked existing files
nontracked existing files
modified tracked files
Git-visible untracked files
missing tracked files
raw-transport candidate count under data/exchange/out/
workspace-class counts
suffix counts
skipped tooling-directory counts
```

No local paths or file contents are included in the public summary.

`data/exchange/out/` itself is **not** a blanket publication-safe directory. It is ignored local exchange/staging state and may contain historical/private generated material. Only an individually reviewed scalar-safe artifact may be promoted to `evidence/real-data/` or otherwise published.

## Run

From repository root:

```powershell
uv run --no-sync python scripts/inventory_local_workspace.py
```

For a full documentation/project-integrity audit, provide the **private manifest** as the single local handoff. Do not manually paste the API key, raw payloads, diffs or dozens of directory listings.

## Interpretation

The manifest lets the reviewer distinguish:

```text
tracked Git state
tracked local modifications/deletions
Git-visible untracked source/helper files
ignored/private authoritative data
local generated artifacts
```

Unknown untracked files and local modifications are evidence to inspect, not cleanup targets.

The manifest intentionally inventories content **existence/state**, not all private file bodies. After it is reviewed, only untracked/modified implementation or documentation files relevant to project integrity need content inspection. Raw private evidence remains a separate evidence corpus and does not need to be bulk-published to prove repository integrity.

## Real workstation review — 2026-08-26

The real Windows manifest established:

```text
modified tracked files: 0
missing tracked files: 0
Git-visible untracked files: 1
```

The single Git-visible untracked item was then content-reviewed separately. It is a 2668-line historical helper-analysis patch affecting 10 existing tracked source/test files (`+690/-349` by `git apply --stat`). Its old blob IDs match the current tracked helper-analysis baseline, so it is genuine local WIP from the current development lineage rather than an unrelated ancient patch.

### Historical patch classification

The patch contains useful correctness work:

```text
fail-closed selection among multiple helper-definition candidates
structural evidence ranking rather than first-match selection
separation of executable helper references from strings/comments/literal template chunks
explicit template-interpolation handling
additional ambiguity and lexical-boundary tests
```

It also removes duplicated local JavaScript masking/brace logic and makes three modules depend on a shared lexical scanner:

```text
coa_workbench.collector.guild_progression_js_lexical
```

Expected imported symbols:

```text
StructuralIndex
exact_symbol_positions
in_excluded_intervals
scan_javascript_structure
```

The shared module itself is **not present in the patch** and no tracked Git history for that path was found. The patch is therefore incomplete and must **not** be applied as-is. Recreating the missing module from assumptions would violate the project's evidence-first/fail-closed discipline.

A bounded scan of added patch lines found no obvious API keys, Authorization/Bearer material, URLs or other credential strings. This is a content-safety classification only; it does not make the patch a public artifact.

Final classification:

```text
valuable historical WIP
not disposable
not self-contained
not part of the current official-API statistics gate
preserve privately
revisit only as a separate helper-analysis workstream
```

If that lane is resumed, implement/review the shared JavaScript lexical scanner explicitly, then port the relevant patch behavior/tests deliberately. Do not blindly `git apply` the historical savepoint.

### Other local findings

The large `untracked_other` count in the first manifest was dominated by a dedicated `.venv-capture` environment plus ignored `*.egg-info` build metadata, not by thousands of unknown project source files. Schema v3 now skips those generated tooling directories.

The same manifest exposed one historical `.har` under `data/exchange/out/`. It is preserved as local ignored state, but a HAR is raw transport evidence and must not be treated as automatically publication-safe. Schema v3 flags such placement explicitly.

The API-key file, local DuckDB, RawArchive corpus, Browser Observatory private profile/session state and HAR inputs were all present as expected private/local project families. Their contents were not read by the inventory.

## Completion statement

For the 2026-08-26 workstation checkpoint:

```text
tracked repository audit: complete
local metadata/workspace inventory: complete
Git-visible untracked implementation/documentation candidates: classified
private evidence corpus: metadata-classified; bulk content review intentionally out of scope
```

A future inventory is needed only after the local workspace changes materially or a new unknown modified/untracked implementation candidate appears. Do not ask for the same historical patch again merely to restart a chat.
