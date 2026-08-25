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
.venv-capture/
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

These may contain authoritative observations and are not disposable build clutter merely because they are ignored.

`data/exchange/out/` is local exchange/staging, **not** a blanket publication-safe directory. Historical generated outputs may still contain raw/private material. Publication requires an individually reviewed scalar-safe artifact, normally promoted to `evidence/real-data/`.

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

The private manifest contains exact local paths/metadata and stays local. The public summary contains counts/booleans only. Schema v3 skips disposable `.venv-capture`/`*.egg-info` directories and separately flags raw-transport candidates placed under `data/exchange/out/`.

The inventory does not read file bodies or secret values and performs no destructive Git operations.

See `docs/LOCAL_WORKSPACE_AUDIT.md`.

## 2026-08-26 workstation checkpoint

The first real local manifest matched the expected E4 branch/HEAD and showed no modified or missing tracked files. One Git-visible untracked `.patch` savepoint remains the only local implementation/documentation candidate requiring content review.

The private local corpus also contains the expected API-key file, DuckDB/RawArchive state, Browser Observatory state and historical HAR inputs. A historical HAR was detected under ignored `data/exchange/out/`; it is preserved but is not publication-safe merely because it sits in an `out` directory.

## Remote-tool boundary

GitHub tooling can inspect/update versioned state and CI. It cannot enumerate the operator's ignored/untracked filesystem. Therefore a full integrity statement must distinguish:

```text
tracked repository audit
local metadata/workspace audit
private evidence-content review
```

As of the 2026-08-26 review, the tracked audit and local metadata inventory are complete. Full workstation integrity remains pending only the content review of the identified Git-visible untracked `.patch`; raw private evidence bodies are intentionally outside bulk repository-integrity inspection.
