# Local workspace and private-data boundary

Status date: **2026-08-26**.

Git is the versioned implementation/public-evidence layer. The operator workstation also contains valid private, generated, transient and historical project state that GitHub cannot see.

## Non-destructive rule

```text
never git clean unknown state
never reset/checkout to destroy untracked files
never recursively delete ignored data trees
never publish private/raw artifacts by default
inspect unknown local files before classifying them obsolete
```

## Versioned families

```text
src/                project Python
scripts/            durable commands/reviewers
migrations/         forward-only migrations
config/             reviewed source/mapping config
docs/               canonical + historical documentation
tests/              deterministic coverage
evidence/real-data/ public-safe real receipts only
```

## Ignored/private families

The current `.gitignore` excludes project-local state under:

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
data/private/
exports/
artifacts/
workbook/working/
```

These may contain authoritative observations and are not disposable build clutter.

## Official API credential

Default key file:

```text
data/private/coa-logs-api-key.txt
```

The key must never be printed, hashed into public evidence, copied into Git, passed as a CLI value, embedded in a query string, or persisted in RawArchive metadata.

## Browser/private state

Browser Observatory private state may live under:

```text
data/private/browser-observatory/
```

This can include dedicated browser profile/session/HAR/trace/private action data. Never use the operator's normal browser profile for automation and never publish browser-profile material.

Browser/HAR is now a fallback acquisition lane, not the primary Ascension Logs source-discovery path.

## Operator-side artifacts outside checkout

Historical work may also exist in Downloads/Desktop or other user-controlled paths:

```text
HAR exports
private diagnostic JSON
scalar-safe handoff JSON
one-off PowerShell/Python helpers
patch files
handoff ZIPs
```

Absence from Git does not prove absence from the project context.

## Exact local inventory

A GitHub-only audit cannot honestly claim to have enumerated ignored/untracked workstation files.

Use the read-only metadata inventory:

```powershell
uv run --no-sync python scripts/inventory_local_workspace.py
```

Outputs:

```text
data/private/local-workspace-inventory.json
data/exchange/out/local-workspace-inventory-summary.json
```

The private manifest contains exact local paths/metadata and stays local. The public summary contains counts/booleans only.

The inventory does not read file bodies or secret values and performs no destructive Git operations.

See `docs/LOCAL_WORKSPACE_AUDIT.md`.

## Remote-tool boundary

GitHub tooling can inspect/update versioned state and CI. It cannot enumerate the operator's ignored/untracked filesystem. Therefore a full integrity statement must distinguish:

```text
tracked repository audit
local-only workspace audit
```

As of the 2026-08-26 documentation overhaul, the tracked audit is complete and the exact local-only audit is pending the generated private manifest.
