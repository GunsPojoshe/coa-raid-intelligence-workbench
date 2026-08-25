# CI operations and development verification

Updated: **2026-08-26**.

## Required jobs

```text
public-release-audit
ubuntu
windows
```

GitHub CI is the final cross-platform gate for the **exact pushed HEAD**.

## Responsibility split

The agent inspects PR/CI/branch state through GitHub tooling. Do not ask the operator to run `gh` merely to report remote status.

The operator is involved only for unavailable local/private runtime work.

## Development cadence

```text
focused tests during iteration
-> one coherent change
-> uv run --no-sync python scripts/verify_repo.py
-> one push
-> inspect exact-head workflow run/jobs
```

Do not repeatedly run the entire suite after every small edit unless a subsequent change invalidated the result.

## Dependency preparation

```powershell
uv sync --frozen --extra dev --no-build-package ruff
```

Do not hand-edit `uv.lock` and do not install Visual Studio Build Tools solely for Ruff.

## Exact-head rule

After a push:

1. resolve the current branch HEAD;
2. query workflow runs for that SHA;
3. inspect concrete jobs;
4. verify `public-release-audit`, `ubuntu`, `windows`;
5. report actual conclusions.

An older green run does not validate a newer commit.

The last fully verified **pre-documentation-overhaul** E4 implementation checkpoint was `41162ddd...` with CI #883 green after a targeted rerun of an infrastructure DNS failure. The 2026-08-26 documentation overhaul requires its own exact-head validation before being called green.

## Evidence-sensitive work

Add focused deterministic/privacy checks for source contracts, public receipts and trust gates. A coherent code+tests+scalar-safe evidence commit is preferred over process-driven micro-commits.

## Git/branch integration

Current staged chain:

```text
main <- e2 (#3) <- e3 (#7) <- e4 (#9)
```

A merge-conflict warning in a lower staged PR is integration debt, not a reason to merge Draft branches prematurely. Resolve conflicts deliberately and preserve the newest canonical docs/evidence semantics.

At the 2026-08-26 audit, #9 and #7 were mergeable; #3 reported lower-chain conflict debt.

## Local handoff

When exact Windows state is needed, ask for one bounded handoff. `git diff HEAD` does not include untracked files.

Preferred inventory:

```powershell
uv run --no-sync python scripts/inventory_local_workspace.py
```

Never use broad cleanup/staging over private data trees.

## Never repeat

```text
no empty commits only to trigger CI
no CI-success claim without exact-head check
no broad private-tree cleanup
no raw private evidence in public CI artifacts
no repeated obsolete Browser/HAR probes when official/API/source evidence already answers the question
```
