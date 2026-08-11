# Windows development environment

## Purpose

This document defines the supported Windows shell/tooling baseline for local development and automation in this repository.

## VS Code PowerShell extension

Observed user setup at the 2026-08-12 handoff:

```text
Identifier: ms-vscode.powershell
Version: 2025.4.0
```

Keep this extension. The extension is the VS Code integration layer; project scripts still execute in a concrete PowerShell runtime.

## Project shell standard

For new Windows automation use **PowerShell 7+** and invoke it as:

```text
pwsh
```

Windows PowerShell 5.1 may remain installed side-by-side for legacy system tasks, but new project automation should not depend on it.

Why this project standard exists: recent bounded E3 helper scripts exposed multiple Windows PowerShell 5.1 / .NET Framework compatibility problems:

```text
System.IO.Path.GetRelativePath unavailable
multiline external python -c quoting failure
gh --jq quoting corruption
ConvertFrom-Json root-array/member-enumeration ambiguity
```

These failures were orchestration/runtime issues, not evidence-stage failures.

## Verify the active shell

Inside the PowerShell session used for project work:

```powershell
$PSVersionTable.PSVersion
(Get-Process -Id $PID).Path
Get-Command pwsh -ErrorAction SilentlyContinue
```

Target:

```text
PSVersion Major >= 7
process path ends in pwsh.exe
pwsh command is discoverable
```

## VS Code session

Use the installed `ms-vscode.powershell` extension and select a PowerShell 7 session through the extension's PowerShell session menu.

The integrated terminal can also use PowerShell 7 as its default profile. Do not assume that installing the VS Code extension automatically changes the terminal/runtime from Windows PowerShell 5.1 to PowerShell 7.

No repository `.vscode/settings.json` is required merely to enforce a machine-specific executable path. Prefer a user-level VS Code selection unless the project later adopts a portable team-wide setting.

## Running project automation

Large scripts containing loops, conditionals, here-strings, JSON parsing or multiple external tools must be saved as `.ps1` and run as a file.

Preferred invocation:

```powershell
pwsh -NoProfile -File .\script.ps1
```

Do not paste large compound programs statement-by-statement into the interactive prompt.

For user-facing one-off orchestration generated during development, keep the file untracked unless it becomes a reusable project operation. Delete obsolete root helpers after their task is closed and after `git status` confirms they are untracked.

## External JSON / GitHub CLI rules

For robust automation:

- prefer one exact run/object over parsing a large run list when the ID is already known;
- parse raw JSON deliberately;
- normalize arrays explicitly before filtering;
- do not rely on PowerShell member-enumeration side effects;
- avoid shell-sensitive `--jq` expressions inside legacy PowerShell;
- verify external command exit codes;
- bind workflow checks to exact commit SHA and exact run ID where possible.

## Python / uv / Ruff

Do not install Visual Studio Build Tools merely to work around Ruff packaging.

The repository has already corrected Ruff lock metadata and CI uses a no-source-build boundary. Current local dependency preparation is expected to use:

```powershell
uv sync --frozen --extra dev --no-build-package ruff
```

Then use the existing environment without re-resolving dependencies where possible:

```powershell
uv run --no-sync python -m ruff check .
uv run --no-sync python -m ruff format --check .
uv run --no-sync python -m pytest
uv run --no-sync python scripts/verify_repo.py
```

Always compare with the current `docs/CI_OPERATIONS.md` before changing dependency commands.

## Line endings

Git may print warnings that LF will be replaced by CRLF in the Windows working copy. A warning alone is not a reason to rewrite files or change repository-wide line-ending policy.

Before commit use:

```powershell
git diff --check
git --no-pager diff
git --no-pager diff --cached
```

Review semantic content and whitespace errors explicitly.

## Security and evidence boundary

Shell convenience must never weaken the repository privacy model. Do not print or commit:

```text
cookies
tokens
Authorization values
browser profiles
unsanitized HAR
private guild/report IDs
private queries
raw JavaScript
raw owner chains
raw private contexts
```

Do not use shell cleanup commands that recursively remove protected data trees.

## Current recommended setup action

At the next local session:

1. confirm whether `pwsh` is installed;
2. if absent, install the current supported PowerShell 7 release using official Microsoft instructions;
3. select that runtime in the VS Code PowerShell extension session menu;
4. optionally set PowerShell 7 as the VS Code integrated-terminal default profile;
5. verify the active runtime with `$PSVersionTable` and process path;
6. use `pwsh -NoProfile -File` for future project automation.
