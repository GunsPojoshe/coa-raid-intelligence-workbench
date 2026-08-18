# Local workspace and private-data boundary

Status date: **2026-08-19**.

This document records the **known classes of local state** that are intentionally absent from Git and must be preserved by development automation. It is a safety map, not an assertion that every listed optional artifact exists on every checkout.

## Principle

Git is the versioned implementation/public-evidence layer.

The operator workstation additionally contains private, generated, transient and historical state. That state is valid project input and must not be deleted merely because Git cannot see it.

Automation rules:

```text
never git clean unknown state
never reset/checkout to destroy untracked files
never recursively delete ignored directories as cleanup
never publish private/raw artifacts by default
prefer additive writes and content-addressed storage
```

## Versioned repository state

Canonical source of versioned truth:

```text
GitHub repository: GunsPojoshe/coa-raid-intelligence-workbench
canonical E3 branch: e3/real-log-capture
isolated discovery branch: e4/interactive-har-discovery
```

Versioned families include:

```text
src/                project Python
scripts/            durable project commands/reviewers
migrations/         forward-only published database migrations
config/             reviewed source/mapping configuration
docs/               architecture, project state and handoffs
tests/              deterministic unit/integration coverage
evidence/real-data/ public-safe real receipts only
```

## Known ignored project-data roots

The repository `.gitignore` intentionally excludes generated/private data under:

```text
data/raw/
data/parquet/
data/warehouse/
data/normalized/
data/reconstructed/
data/extracted/
data/exchange/in/
data/exchange/out/
data/backups/
data/logs/
exports/
artifacts/
workbook/working/
```

These paths can contain authoritative private observations and are not disposable build clutter.

Examples already used in the project include:

```text
local DuckDB warehouse
immutable raw response archive
private extraction/review JSON
HAR-derived private observations
exchange input/output receipts
local verification reports
```

## Known operator-side artifacts outside the repository

Project history has used files outside the checkout, especially under Downloads/Desktop. Examples include:

```text
browser HAR exports
scalar-safe JSON handoff files
private diagnostic JSON files
one-off PowerShell helpers
one-off Python apply/diagnostic helpers
handoff ZIP archives
```

These are outside Git's control. Repository automation must not assume that absence from Git means absence from the project context.

Historical examples referenced by handoff/conversation state include:

```text
e3-current-local.patch
review-cross-report-source-structure.ps1
captured coa.ascensionlogs.gg HAR files
source-observation / source-observatory handoff ZIPs
current-report / cross-report proof JSON files
```

Names and timestamps can vary; this is a class-of-state inventory, not a cleanup allowlist.

## Historical untracked implementation/helper state

Earlier E3 checkpoints explicitly allowed untracked implementation or helper files while an evidence slice was being developed. Some were later versioned or superseded.

Therefore:

```text
unknown untracked .py/.ps1/.patch files must be inspected, not deleted
historical e3-current-local.patch must be preserved if present
obsolete helpers may be removed only by exact path after confirming they are obsolete
wildcard/recurse cleanup remains prohibited
```

## Browser Observatory private state

The accelerated E4 architecture introduces a new local-only family:

```text
data/private/browser-observatory/
```

Intended contents can include:

```text
browser-profile/        dedicated automation browser state
sessions/               private action/network session manifests
har/                    optional forensic HAR copies
traces/                 browser/CDP/Playwright traces
screenshots/            private discovery screenshots when explicitly captured
receipts-private/       scalar-bearing internal analysis results
```

This entire family is private/ignored and must never be staged automatically.

Do **not** point automation at the operator's normal Chrome/Firefox profile. Browser automation must use a dedicated project-private profile.

## Browser profile safety

Persistent browser state can contain authentication/session material.

Rules:

```text
separate dedicated profile only
never include browser profile in a handoff ZIP by default
never hash low-entropy private values into public receipts as a substitute for redaction
never print cookies, Authorization values or local-storage secrets
never publish HAR/raw response bodies automatically
```

## Stable operator exchange boundary

The target workflow reduces manual file shuttling to stable paths:

```text
data/exchange/in/       explicit local/private inputs
data/exchange/out/      generated local handoff/review output
```

Durable project logic belongs in `src/` or `scripts/`, not in a succession of Downloads-only helper scripts.

## What a new chat/agent can safely assume

It may assume that:

```text
GitHub does not contain the complete operational corpus
private local files are legitimate analysis inputs
ignored DuckDB/raw/extracted/exchange state may be essential
operator-side Downloads/Desktop artifacts may exist
unknown local state must be preserved
```

It may **not** assume that any specific private file is still present until the operator/local runner verifies it.

## What GitHub-only automation can and cannot do

GitHub-only automation can safely:

```text
inspect/update versioned files
create isolated commits/branches
update documentation/tests/code
run GitHub CI after commits
```

It cannot see or mutate the operator's ignored/untracked localhost state. Changes produced through GitHub APIs therefore must remain additive and compatible with the documented local boundary until the operator fast-forwards/pulls them locally.

## Future workspace manifest

A later Browser Observatory/operator-runner slice should generate a **private local workspace manifest** containing only local paths/classes/status needed for orchestration. A separate public-safe summary may expose booleans/counts, never private path values or scalar identities.
