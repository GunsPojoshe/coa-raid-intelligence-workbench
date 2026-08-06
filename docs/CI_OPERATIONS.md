# CI operations and incident record

## Purpose

This document defines the safe operating procedure for the `Verify repository`
GitHub Actions workflow and records the CI incident investigated on 2026-08-07.

Canonical workflow:

```text
.github/workflows/verify.yml
```

Expected jobs:

```text
public-release-audit
ubuntu
windows
```

## Confirmed incident state

Starting exact HEAD:

```text
42dfc1de713fa4b20be64ff5ff0119920df6ee3a
```

Confirmed local validation before the infrastructure repair:

```text
Ruff lint: passed
Ruff format: passed
focused helper-reference tests: passed
full pytest: 387 passed
repository verification: 10/10 passed
working tree after push: clean
```

Relevant earlier commits:

```text
7180894952f2f54a23e07a0782847669ae51a495
Format helper reference review command

42dfc1de713fa4b20be64ff5ff0119920df6ee3a
Enable E3 verification triggers
```

## Confirmed failures and corrections

### Automatic run was absent

The workflow was active, repository Actions were enabled, PR #7 was clean and
mergeable, and the branch matched the workflow configuration. No exact-head
push or pull-request run was registered for the starting HEAD.

A manual workflow dispatch successfully created run `31128581113`, proving that
the workflow and Actions infrastructure were available.

The next normal push after the branch trigger already exists is the bounded
control test for automatic push delivery.

### Interactive PowerShell paste split compound statements

A long repair block was pasted directly into interactive PowerShell.
PowerShell executed a completed `if {}` statement before receiving the following
`elseif` or `else`, so those tokens were interpreted as commands.

Operational rule:

```text
Run multi-branch or here-string-heavy automation from a .ps1 file.
Do not paste it statement-by-statement into an interactive prompt.
```

### Unsafe run polling

The first polling implementation assumed every object returned by
`gh run list` exposed `headSha`. Under `Set-StrictMode`, that produced
`PropertyNotFoundStrict`.

Use REST queries and verify property existence before dereferencing JSON fields.

### Ruff was missing locally

The local `.venv` initially lacked Ruff. Repository verification therefore
reported 8/10 although application tests passed.

Synchronize development dependencies before repository verification.

### Ruff lock entry contained only an sdist

The Ruff 0.12.12 entry in `uv.lock` contained no wheel records. Clean Windows
installations attempted a Rust source build and failed without MSVC `link.exe`.
GitHub runners also spent the dependency phase compiling Ruff.

The lock entry was regenerated through `uv lock`, not hand-edited.

The workflow now uses:

```text
uv sync --frozen --extra dev --no-build-package ruff
```

This converts a missing-wheel regression into an immediate, explicit failure.

### Ruff formatter failure

The helper-reference review command initially failed `ruff format --diff`.
The formatter-only correction was committed separately.

## Required local verification

```powershell
uv sync --frozen --extra dev --no-build-package ruff
uv run python -m ruff check .
uv run python -m ruff format --check .
uv run python -m pytest
uv run python scripts/verify_repo.py
```

Expected result:

```text
Summary: 10/10 checks passed
```

## Safe exact-head diagnosis

```powershell
pwsh -NoProfile -File scripts/inspect_verify_workflow.ps1 `
  -HeadSha <exact-40-character-sha> `
  -Event push
```

Do not infer run creation from a successful push, branch movement, PR head
movement, or an older entry on the Actions page.

## Trigger policy

Preferred trigger:

```text
normal Git push
```

Bounded fallback:

```powershell
gh workflow run verify.yml `
  --repo GunsPojoshe/coa-raid-intelligence-workbench `
  --ref e3/real-log-capture
```

Manual dispatch proves workflow availability but does not prove automatic push
delivery.

## Atomic commit policy

Keep these scopes separate:

1. dependency and lock repair;
2. workflow trigger or guardrail changes;
3. formatter-only corrections;
4. evidence receipts;
5. operational documentation.

## Never repeat

- Do not create repeated empty commits before proving the trigger contract.
- Do not use long blind polling loops before a run ID exists.
- Do not install Visual Studio Build Tools only to work around a missing Ruff
  wheel.
- Do not edit `uv.lock` manually.
- Do not paste a large multi-branch PowerShell program directly into the
  interactive prompt.
- Do not publish private evidence in CI logs or documentation.