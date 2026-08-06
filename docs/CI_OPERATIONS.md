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

## Final verified checkpoint

Implementation checkpoint before the subsequent handoff-document commits:

```text
HEAD: 66fd5ed89520070a7d48392f41fbfb7cb352b0f7
Verify repository run: #598
run ID: 31128752182
event: workflow_dispatch
status: completed
conclusion: success
public-release-audit: success
ubuntu: success
windows: success
```

Local verification for the same implementation checkpoint:

```text
Ruff lint: passed
Ruff format: passed
focused helper-reference tests: passed
full pytest: 387 passed
repository verification: 10/10 passed
working tree after push: clean
```

The documentation commits created after this checkpoint change the live branch
HEAD. Always query current HEAD and exact-head runs live.

## Relevant corrective commits

```text
7180894952f2f54a23e07a0782847669ae51a495
Format helper reference review command

42dfc1de713fa4b20be64ff5ff0119920df6ee3a
Enable E3 verification triggers

c24f6f1c1e6b14ed5e464a2a00fe6d462183ae5b
Repair Ruff lock distributions

7e53d5e2841808d30f127e1917a36d24cf82bcfd
Reject Ruff source builds in CI

66fd5ed89520070a7d48392f41fbfb7cb352b0f7
Document CI operations and diagnostics
```

## Confirmed failures and corrections

### Automatic `push` run remains absent

The workflow was active, repository Actions were enabled, allowed actions were
`all`, PR #7 was clean and mergeable, and `e3/real-log-capture` was already in
`push.branches` before the controlled push from `42dfc1d` to `66fd5ed`.

The controlled normal push created no exact-head `push` run during the bounded
observation window.

Therefore:

```text
workflow availability: proven
job execution: proven
automatic push-event delivery for this branch: not proven / currently absent
```

Do not hide this condition with repeated empty commits.

### Manual dispatch is the proven bounded fallback

Manual dispatch created run #598 for exact HEAD `66fd5ed` and all three jobs
completed successfully.

Known-good command:

```powershell
gh workflow run verify.yml `
  --repo GunsPojoshe/coa-raid-intelligence-workbench `
  --ref e3/real-log-capture
```

Manual dispatch proves workflow availability and exact-head verification. It
does not prove automatic `push` event delivery.

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

The first polling command assumed that every object returned by `gh run list`
had a `headSha` property. Under PowerShell `Set-StrictMode`, this produced
`PropertyNotFoundStrict`.

Use REST queries and check property existence before dereferencing JSON fields.

### Ruff was missing locally

The local `.venv` initially lacked Ruff. `scripts/verify_repo.py` therefore
reported 8/10 although application tests passed.

Synchronize development dependencies before repository verification.

### Ruff lock entry contained only an sdist

The Ruff 0.12.12 entry in `uv.lock` contained only an sdist URL and no wheels.

Consequences:

- clean Windows sync attempted a Rust source build;
- local Windows sync failed because MSVC `link.exe` was not installed;
- clean GitHub runners spent the dependency phase compiling Ruff;
- CI behavior depended on native compiler availability.

The lock entry was regenerated through `uv lock`; it was not hand-edited.

The workflow now uses:

```text
uv sync --frozen --extra dev --no-build-package ruff
```

This forces an explicit failure when Ruff wheels are missing instead of silently
compiling Rust.

### Ruff formatter failure

The helper-reference review command initially failed `ruff format --diff`.
The formatter-only correction was committed independently.

## Current annotations and warnings to audit

GitHub Actions emitted an annotation that the pinned `actions/checkout` target
uses deprecated Node.js 20 metadata and is being forced to run on Node.js 24.
The next repository/dependency audit must determine the correct pinned upgrade.

Pytest currently emits:

```text
StarletteDeprecationWarning:
Using httpx with starlette.testclient is deprecated; install httpx2 instead.
```

This warning is non-blocking at the verified checkpoint but must be classified
before dependency changes.

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

Use the versioned script:

```powershell
pwsh -NoProfile -File scripts/inspect_verify_workflow.ps1 `
  -HeadSha <exact-40-character-sha> `
  -Event push
```

The script uses REST endpoints and checks JSON property existence before
reading values.

Do not infer run creation from:

- successful `git push`;
- branch movement;
- PR head movement;
- an older run shown on the Actions page.

## Trigger policy

Attempt the normal push once as part of a real atomic change and inspect the
exact HEAD through REST.

If no exact-head `push` run appears in a bounded window, use the documented
manual dispatch fallback and record:

```text
trigger mode: workflow_dispatch
automatic push run absent: true
exact verified HEAD: <sha>
```

Do not create additional commits solely to retry event delivery.

## Atomic commit policy

Keep these scopes separate:

1. dependency and lock repair;
2. workflow trigger or guardrail changes;
3. formatter-only corrections;
4. evidence receipts;
5. operational documentation;
6. repository cleanup and branch deletion.

Do not mix evidence conclusions with CI infrastructure changes.

## Never repeat

- Do not create repeated empty commits before proving the trigger contract.
- Do not use long blind polling loops before a run ID exists.
- Do not install Visual Studio Build Tools only to work around a missing Ruff
  wheel.
- Do not edit `uv.lock` manually.
- Do not paste a large multi-branch PowerShell program directly into the
  interactive prompt.
- Do not publish raw private evidence in CI logs, receipts or documentation.
- Do not delete branches before checking linked PRs, merge-base and unique
  commits.
