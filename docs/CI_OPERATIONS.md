# CI operations and development verification

Дата актуализации: **2026-08-13**.

## Purpose

Keep verification strong without turning every development step into repeated ceremony.

Required GitHub jobs:

```text
public-release-audit
ubuntu
windows
```

## Last verified remote checkpoint

```text
HEAD: be899cc5f66c7bd82a1006116dbe57d91ecaed84
commit: Review guild progression helper owner binding
Verify repository: #613
run ID: 31651028612
status: completed
conclusion: success
public-release-audit: success
ubuntu: success
windows: success
```

Always verify newer pushed HEADs live.

## Responsibility split

The agent performs GitHub/CI inspection itself through the connector. Do not ask the user to run `gh` commands just to report workflow or PR state when the connector can answer it.

The user is involved only for local Windows/private runtime operations the agent cannot access directly.

## Dependency boundary

Prepare the locked environment with:

```powershell
uv sync --frozen --extra dev --no-build-package ruff
```

Do not install Visual Studio Build Tools solely for Ruff. Do not hand-edit `uv.lock`.

## Verification strategy

### During iteration

Run the smallest focused tests that cover the changed behavior. Ruff may be limited to changed files while iterating.

Do not run the entire test suite after every small edit without a reason.

### Before one meaningful push

Run one aggregate local verification:

```powershell
uv run --no-sync python scripts/verify_repo.py
```

If the change is evidence-sensitive, also run its deterministic/public-private/privacy validation before the push.

`verify_repo.py` is the final local aggregate gate. Do not duplicate the same full suite repeatedly unless a subsequent change invalidated the result.

### After push

GitHub CI is the final cross-platform gate. For the exact new commit:

1. resolve the new HEAD SHA;
2. query workflow runs for that SHA;
3. inspect the concrete run ID;
4. verify `public-release-audit`, `ubuntu`, `windows`;
5. report actual conclusions.

A successful push does not imply successful CI. An older green run does not validate a newer commit.

## Development modes

### Normal development

```text
focused iteration tests
-> one verify_repo.py
-> one coherent commit/push
-> exact-head CI
```

### Evidence-sensitive stage

Add deterministic binding and privacy validation. A coherent code+tests+approved scalar-free receipt commit is acceptable when the files represent one meaningful evidence stage.

### High-risk gate

Do not enable first/unknown network probes, destructive changes or trusted scoring without an explicit reviewed contract.

## Commit scope

Prefer one coherent commit per meaningful change. Avoid micro-commits created only to satisfy process ceremony.

Separate an unrelated dependency repair, migration or repository cleanup when it is genuinely independent.

Never use broad cleanup/staging commands over private data trees.

## Diagnostics

A diagnostic is justified when its answer decides which implementation is required. Keep it narrow and offline where possible.

Do not repeatedly add inventory/review/relationship stages when direct provenance tracing of the concrete invocation can answer the product question more directly.

## GitHub Actions trigger policy

Historical push-trigger delivery was once inconsistent. Current rule:

- make one real atomic push;
- query exact-head runs;
- if no suitable run exists, diagnose first;
- use `workflow_dispatch` only as a bounded fallback;
- never create empty commits solely to trigger CI.

## PowerShell runtime

New Windows automation uses PowerShell 7+ (`pwsh`). Large compound automation runs as a `.ps1` file, not statement-by-statement in an interactive terminal.

## Local handoff rule

When the agent needs the exact local state, ask for one bundled handoff rather than a long list of commands.

Remember:

```text
git diff HEAD != complete working tree when untracked files exist
```

The handoff must account for tracked changes and relevant untracked files. Private files may be included/read for analysis when needed; publication restrictions are separate.

## Never repeat

- no manual user GitHub status collection when the connector can do it;
- no blind long polling before a concrete run exists;
- no repeated empty trigger commits;
- no full-suite reruns after every small edit;
- no process-driven micro-commits;
- no manual `uv.lock` editing;
- no Visual Studio Build Tools install only for Ruff;
- no large interactive PowerShell paste;
- no raw private evidence in CI/public receipts;
- no CI success claim without exact-head verification.
