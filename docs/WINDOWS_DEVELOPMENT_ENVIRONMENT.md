# Windows development environment

Updated: **2026-08-26**.

## Supported shell

Use **PowerShell 7+ (`pwsh`)** for new project automation. Windows PowerShell 5.1 may exist for legacy system tasks but is not the project target.

Repository:

```text
C:\Users\Simpa\source\repos\coa-raid-intelligence-workbench
```

## Responsibility split

GitHub/PR/CI/repository-source work is handled remotely when tooling permits. The operator is needed for:

```text
exact local working tree
ignored/untracked files
private RawArchive/DuckDB/API key
local browser/session state
local runtime execution
```

Prefer one complete action over long interactive command sequences.

## Private API credential

Default:

```text
data/private/coa-logs-api-key.txt
```

Do not paste the key into PowerShell history, CLI arguments, screenshots or chat unless a specific unavailable local operation truly requires it. Current API capture scripts read the file themselves.

## Exact local-state inventory

Remote GitHub state is not the same as the Windows working tree. `git diff HEAD` misses untracked files.

Run:

```powershell
uv run --no-sync python scripts/inventory_local_workspace.py
```

This writes:

```text
data/private/local-workspace-inventory.json
data/exchange/out/local-workspace-inventory-summary.json
```

The inventory reads metadata only and performs no cleanup.

When a full project-integrity audit needs local state, provide the **private manifest** as one handoff rather than many directory listings. It may contain private filenames and must not be committed.

## Python / uv

```powershell
uv sync --frozen --extra dev --no-build-package ruff
uv run --no-sync python scripts/verify_repo.py
```

Use focused tests while iterating; run the aggregate verifier once before a meaningful push.

## Complex automation

Loops, conditionals, JSON parsing and multi-tool orchestration should run as a `.ps1`/project script rather than being pasted statement-by-statement into an interactive shell.

## Cleanup safety

Do not use recursive wildcard cleanup over project/private data. Do not delete unknown untracked helpers, historical patches or `.gitkeep` files until their role is classified.

LF/CRLF warnings alone are not a reason for repository-wide rewrites.
