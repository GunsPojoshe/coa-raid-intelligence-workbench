# Implementation log

## Initial slice — baseline and repository skeleton

Implemented:

1. Archived workbook v9 without modification and recorded SHA-256.
2. Added reproducible workbook inventory and Excel-table export command.
3. Added observed saved-state fixture for v9; explicitly marked it as not being an approved 25-player roster fixture.
4. Added one model for FLEX/10/25/40 target-size resolution and a canonical 40-element `ActiveSlot` mask.
5. Added draft raid-profile configuration, preserving only source-supported target sizes and v9 duplicate limits.
6. Added initial DuckDB migration contract for raw, canonical, evidence, planning, snapshot and job entities.
7. Added CLI commands: `doctor`, `validate-config`, `freeze-baseline`, `init-db`.
8. Added unit tests and an optional DuckDB integration test.

Deferred intentionally:

- Modifying or resaving workbook v9.
- Inventing role limits for 10/25/40 or a FLEX range.
- Declaring browser/API routes verified.
- Correcting cached formula errors before a regression fixture exists.
- Implementing scoring or collector behavior without fixed inputs and expected outputs.
