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

## E0 formula-prefix repair candidate

Implemented:

1. Added a direct OOXML package patcher that preserves unsupported Excel extensions and never overwrites the archived v9 workbook.
2. Reclassified 72 `TEXTJOIN` and 70 `RANK.EQ` formulas from invalid `_xludf` calls to standard future-function `_xlfn` calls.
3. Set `calcMode=auto`, `fullCalcOnLoad=1` and `forceFullCalc=1` so desktop Excel performs a complete recalculation when the candidate is opened.
4. Added a deterministic generated workbook candidate and machine-readable repair report.
5. Added a workbook regression test that verifies package membership, deterministic output, exact replacement counts and absence of remaining `_xludf` formulas.

Still deferred:

- Declaring formula caches corrected before desktop Excel has recalculated and saved the candidate.
- Calling the workbook an approved 25-player fixture; no approved 25-player roster has been supplied.
