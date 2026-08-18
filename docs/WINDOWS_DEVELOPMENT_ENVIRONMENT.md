# Windows development environment

Дата актуализации: **2026-08-13**.

## Purpose

Supported Windows shell/tooling baseline and the minimal user-interaction contract for this repository.

## Project shell standard

Use **PowerShell 7+** (`pwsh`) for new project automation. Windows PowerShell 5.1 may remain installed for legacy system tasks but is not a target for new project scripts.

The existing VS Code `ms-vscode.powershell` extension is supported. The extension is only the integration layer; ensure the active runtime is PowerShell 7 when running project automation.

Historical PowerShell 5.1 failures included:

```text
System.IO.Path.GetRelativePath unavailable
multiline external-command quoting corruption
gh --jq quoting corruption
ConvertFrom-Json array/member-enumeration ambiguity
```

These were orchestration/runtime problems, not evidence failures.

## Local repository

```text
C:\Users\Simpa\source\repos\coa-raid-intelligence-workbench
```

## Responsibility split

The agent handles GitHub, PR, CI, remote branch comparison and repository-source inspection itself whenever tools permit it.

The user should not be asked to act as a manual GitHub operator.

The user is required only for things the agent cannot access directly, primarily:

- the exact Windows working tree;
- unshared local/private artifacts;
- browser/session state;
- local runtime execution.

When local work is required, provide **one complete action** whenever possible. Prefer one downloadable script or one short command that produces one compact result/handoff.

Do not send long sequences of commands when a single script can perform the same bounded task.

## Private files

Private/raw files are valid analysis inputs. There is no rule requiring the agent to avoid reading them.

The boundary is publication/versioning:

- secrets remain private;
- raw source IDs/report IDs remain private by default;
- raw JavaScript/private contexts/owner chains remain private by default;
- sanitized/public receipts are reviewed separately.

A private file may be shared with the agent for analysis without implying it should be committed.

## Exact local-state handoff

The agent cannot directly enumerate the user's Windows filesystem. A normal GitHub checkout view is not the same as the user's current working tree.

Also:

```text
git diff HEAD
```

does not include untracked files.

When exact local state is needed, use one bounded handoff that captures:

- current branch and HEAD;
- tracked diff;
- relevant untracked-file manifest;
- only the private artifacts actually needed for the decision.

Do not ask the user to manually copy many independent command outputs.

## Running project automation

Large scripts containing loops, conditionals, here-strings, JSON parsing or multiple external tools must run as a file:

```powershell
pwsh -NoProfile -File .\script.ps1
```

One-off user-facing orchestration should stay outside project source unless it becomes a reusable project operation.

## Python / uv / verification

Dependency preparation:

```powershell
uv sync --frozen --extra dev --no-build-package ruff
```

During iteration use focused tests. Before one meaningful push use the repository aggregate verifier:

```powershell
uv run --no-sync python scripts/verify_repo.py
```

The agent verifies exact-head GitHub CI after push.

## Line endings

LF/CRLF warnings alone are not a reason for repository-wide rewrites. Review semantic diff and whitespace errors explicitly.

## Cleanup safety

Do not use recursive wildcard cleanup over project/private data. Do not delete `.gitkeep`. Remove obsolete one-off helpers or branches only after their purpose/history has been classified.
