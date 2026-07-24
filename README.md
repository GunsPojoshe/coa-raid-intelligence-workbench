# CoA Raid Intelligence Workbench

Initial implementation slice for the local Excel + Python + DuckDB product described by project baseline v0.5.

## What is implemented

- byte-for-byte archive and SHA-256 freeze of Excel v9;
- reproducible workbook inventory, table exports and observed saved-state fixture;
- Python package and CLI skeleton;
- unified format/target-size logic for FLEX, 10, 25 and 40;
- canonical 40-slot `ActiveSlot` mask;
- source-grounded draft raid profiles;
- initial DuckDB migration contract;
- unit tests plus an optional DuckDB migration test.

## Run from the repository root

```powershell
uv sync --extra dev
uv run coa-workbench doctor --project-root .
uv run coa-workbench validate-config --path config/raid_profiles.yaml
uv run pytest
```

Rebuild the baseline artifacts without changing the source workbook:

```powershell
uv run coa-workbench freeze-baseline `
  workbook/archive/CoA_Raid_Comp_Конструктор_v9.xlsx `
  --output-dir baseline `
  --project-document docs/PROJECT_BASELINE_v0.5.md
```

Initialize DuckDB after dependencies are installed:

```powershell
uv run coa-workbench init-db --database data/warehouse/coa.duckdb --migrations migrations
```

## Baseline facts and constraints

- The archived workbook checksum is recorded in `baseline/source_manifest.json`.
- The workbook has 25 physical roster rows in the saved v9 interface, 70 class/spec combinations and 45 conceptual effects.
- The uploaded workbook does **not** contain an approved fully populated 25-player composition. The generated JSON fixture captures only the saved state and is marked accordingly.
- The workbook contains extension-based Excel rules that openpyxl warns it would strip when saving. The archived v9 file is therefore read-only for the Python baseline tool.
- Cached formula errors from v9 are retained in the inventory as evidence; they are not silently corrected.
- FLEX allowed size, role limits and effect requirements remain unapproved and are not guessed in configuration.
- Endpoint Registry is intentionally empty until prior browser scripts, URLs and sample payloads are supplied and verified.

## Immediate next implementation issue

Create and approve a fully populated 25-player regression fixture, including expected roles, coverage, top recommendation and comparison outputs. Only then create the first workbook v10 copy with 40 physical rows and `ActiveSlot` filtering.
