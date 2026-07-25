# Workbook migration area

- `archive/CoA_Raid_Comp_Конструктор_v9.xlsx` is a byte-for-byte archived baseline.
- Do not resave the archived file with openpyxl: the package contains extension-based validation/formatting rules that openpyxl reports it would remove.
- The first v10 workbook copy will be created only after an approved 25-player regression fixture is supplied or reconstructed and accepted.

## Formula-prefix repair candidate

`candidates/CoA_Raid_Comp_Конструктор_v9_formula_repair.xlsx` is a generated candidate, not a new baseline and not an approved 25-player fixture.

It is produced by `scripts/repair_workbook_formula_prefixes.py`, which edits the XLSX package directly instead of resaving it through openpyxl. The transformation is intentionally narrow:

- 72 `_xludf.TEXTJOIN` calls become `_xlfn.TEXTJOIN`;
- 70 `_xludf.RANK.EQ` calls become `_xlfn.RANK.EQ`;
- workbook calculation is set to automatic with full recalculation on load.

Only `xl/workbook.xml`, `xl/worksheets/sheet2.xml` and `xl/worksheets/sheet9.xml` differ from the archived package. Cached formula values are not fabricated. Desktop Excel must open and save the candidate before its calculated values can be accepted as fixture evidence.
