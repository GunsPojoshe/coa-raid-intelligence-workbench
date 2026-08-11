# CI operations and incident record

## Purpose

Safe operating procedure for `.github/workflows/verify.yml` and the local verification path.

Required jobs:

```text
public-release-audit
ubuntu
windows
```

## Last fully verified code/evidence checkpoint

Before the 2026-08-12 docs-only handoff:

```text
HEAD: 13982825295737c029b425a37d210a34a7ea0762
commit: Review guild progression helper references
Verify repository run: #603
run ID: 31533555026
event: pull_request
status: completed
conclusion: success
public-release-audit: success
ubuntu: success
windows: success
```

Always query current HEAD and exact-head runs live after subsequent commits.

## Dependency boundary

Ruff lock metadata was previously repaired so clean Windows/Linux environments use wheels rather than silently compiling Ruff from source.

Dependency preparation:

```powershell
uv sync --frozen --extra dev --no-build-package ruff
```

Do not install Visual Studio Build Tools solely to work around Ruff packaging. Do not hand-edit `uv.lock`.

## Local verification

After dependency preparation, prefer deterministic no-resolve commands:

```powershell
uv run --no-sync python -m ruff check .
uv run --no-sync python -m ruff format --check .
uv run --no-sync python -m pytest
uv run --no-sync python scripts/verify_repo.py
```

Repository verifier must remain the final aggregate check. Do not claim a passing checkpoint when only focused tests ran.

## GitHub Actions exact-head policy

A successful `git push` does not itself prove CI exists for the new commit.

For every pushed implementation/evidence change:

1. read the exact new commit SHA;
2. query workflow runs bound to that SHA;
3. identify one concrete run ID;
4. inspect all required jobs;
5. report trigger mode and conclusions.

Do not use an older Actions-page run as evidence for a newer HEAD.

## Trigger history

During the 2026-08-07 incident, an expected automatic `push` run for E3 did not appear even though the workflow was active and the branch filter existed. The bounded fallback was:

```powershell
gh workflow run verify.yml `
  --repo GunsPojoshe/coa-raid-intelligence-workbench `
  --ref e3/real-log-capture
```

A later exact-head `pull_request` run #603 was delivered normally and passed all jobs. Therefore historical push-delivery trouble must not be generalized into a claim that PR runs are broken.

Policy:

- make one real atomic push;
- query exact-head runs;
- if no suitable run exists, diagnose before dispatch;
- use `workflow_dispatch` as bounded fallback when needed;
- never create empty commits merely to retrigger CI.

## PowerShell runtime standard

New Windows automation uses **PowerShell 7+ (`pwsh`)**. See `docs/WINDOWS_DEVELOPMENT_ENVIRONMENT.md`.

The following failures were encountered when orchestration ran in Windows PowerShell 5.1:

```text
System.IO.Path.GetRelativePath missing
multiline python -c quoting corrupted
gh --jq expression quoting corrupted
ConvertFrom-Json root-array/member-enumeration produced accidental multi-run values
```

These were shell/runtime defects, not evidence-chain failures.

Do not add more compatibility workarounds for Windows PowerShell 5.1 unless a genuine project requirement appears. Prefer migrating one-off orchestration to `pwsh`.

## GitHub CLI JSON rules

For scripts that inspect Actions:

- bind to exact SHA;
- use an exact known run ID when available;
- verify the run's `headSha` before trusting it;
- normalize JSON arrays explicitly;
- verify every external command exit code;
- avoid shell-sensitive jq expressions when robust native JSON parsing is simpler;
- never print tokens, credentials or private evidence.

## Interactive-shell rule

Large PowerShell automation containing `if/elseif/else`, loops or here-strings must run from a `.ps1` file:

```powershell
pwsh -NoProfile -File .\script.ps1
```

Do not paste it statement-by-statement. Prior interactive execution split completed `if {}` blocks from following `else` clauses.

## Temporary root helper scripts

One-off `run-e3-*.ps1` files created to bridge a bounded local operation should stay untracked unless deliberately promoted into reusable project tooling.

Once the bounded operation is closed:

1. inspect `git status`;
2. confirm each file is untracked and obsolete;
3. delete only the explicit filenames;
4. do not use recursive/wildcard cleanup over repository data.

## Atomic commit scopes

Do not mix:

1. implementation code;
2. public evidence receipt;
3. CI/dependency repair;
4. documentation;
5. cleanup.

Before commit:

```powershell
git diff --cached --name-only
git --no-pager diff --cached
git diff --cached --check
```

## Known non-blocking dependency warning

Historical pytest runs emitted a `StarletteDeprecationWarning` involving `httpx`/`starlette.testclient`. Treat it as a dependency-audit item, not evidence to make an unreviewed dependency upgrade during unrelated E3 work.

## Actions runtime annotation

GitHub previously annotated a pinned `actions/checkout` Node.js runtime migration. Audit pinned action versions separately; do not mix that maintenance with evidence semantics.

## Never repeat

- no blind long polling before a concrete run exists;
- no repeated empty trigger commits;
- no manual `uv.lock` editing;
- no Visual Studio Build Tools install only for Ruff;
- no large interactive PowerShell paste;
- no raw private evidence in CI logs;
- no CI success claim without exact-head verification.
