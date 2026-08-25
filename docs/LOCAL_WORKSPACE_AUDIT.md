# Local workspace audit

Status: **canonical operator procedure**  
Updated: **2026-08-26**

GitHub contains the versioned implementation, but it cannot see ignored/untracked/private files on the operator workstation. Project-integrity reviews therefore use one bounded read-only local inventory instead of guessing from `git diff`.

## What the inventory does

`scripts/inventory_local_workspace.py` enumerates project files without reading their contents. It records private metadata needed for an integrity review:

```text
relative path
size
mtime
tracked/untracked state
known privacy/generated class
file suffix
```

It skips Git internals and disposable tooling caches such as `.git/`, `.venv/`, `__pycache__/`, `.pytest_cache/`, `playwright-report/` and `test-results/`.

It does **not**:

```text
read file bodies
read the API key value
hash private scalar content
delete/rename/modify project files
run git clean/reset/checkout
publish raw/private filenames
```

## Outputs

Private exact manifest:

```text
data/private/local-workspace-inventory.json
```

This may contain private filenames and stays ignored/local. It may be shared privately for analysis when an exact local audit is requested; sharing it does not make it publishable.

Public-safe summary:

```text
data/exchange/out/local-workspace-inventory-summary.json
```

The public-safe summary contains only counts/booleans and no file paths.

## Run

From repository root:

```powershell
uv run --no-sync python scripts/inventory_local_workspace.py
```

For a full documentation/project-integrity audit, provide the private manifest as the single local handoff. Do not manually paste the API key, raw payloads or dozens of directory listings.

## Interpretation

The manifest lets the reviewer distinguish:

```text
tracked Git state
ignored/private authoritative data
local generated artifacts
unknown untracked helper/source files
```

Unknown untracked files are evidence to inspect, not cleanup targets.

A GitHub-only review may be complete for tracked files while the local-workspace audit remains pending. The documentation must state that distinction explicitly rather than claiming all local files were inspected remotely.
