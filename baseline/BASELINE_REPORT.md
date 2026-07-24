# Workbook v9 — frozen baseline

The source workbook was read without resaving it. All exports are reproducible from the archived binary.

## Summary

| Metric | Value |
|---|---:|
| Workbook SHA-256 | d2f719c2875ad5aa1b1413daee54aaa36e4d52068bfe2a898df8fcb8b296eb83 |
| Sheets | 16 |
| Excel tables | 9 |
| Formula cells | 4355 |
| Cached formula errors | 282 |
| Class/spec combinations | 70 |
| Conceptual effects | 45 |
| Saved counted players | 0 |
| Saved target size | 25 |
| Workbook timeline events | 12148016 |

## Known baseline risks

- `openpyxl_resave_safe`: **False**. The workbook contains extension features that openpyxl warns it would remove on save.
- Cached Excel formula errors: **282**. They are preserved as evidence, not corrected automatically.
- No approved fully populated 25-player roster is stored in the uploaded workbook; the generated fixture is the observed saved state only.
- Timeline count remains unresolved: workbook=12148016, project document=12147472, difference=544.
- Workbook v9 has no defined names; Excel/Python exchange contracts therefore still need named tables/ranges in v10.

## Sheet inventory

| Sheet | State | Used range | Formulas | Tables | Cached errors |
|---|---|---:|---:|---|---:|
| РЕЙД-КОНСТРУКТОР | visible | 64 x 22 | 404 | — | 0 |
| СРАВНЕНИЕ СПЕКОВ | visible | 62 x 8 | 281 | — | 2 |
| КАТАЛОГ СПЕКОВ | visible | 73 x 16 | 210 | CatalogSpecsTable | 70 |
| СПРАВОЧНИК ЭФФЕКТОВ | visible | 48 x 13 | 135 | EffectsReferenceTable | 0 |
| ДАННЫЕ_Комбинации | visible | 72 x 11 | 0 | RawCombinationsTable | 0 |
| ДАННЫЕ_Источники | visible | 561 x 10 | 0 | RawSourcesTable | 0 |
| Справка | visible | 27 x 10 | 0 | HelpTable | 0 |
| ТЕХ_Списки | visible | 71 x 56 | 0 | — | 0 |
| ТЕХ_Расчет | visible | 119 x 48 | 1825 | — | 140 |
| ЛОГИ_Эффекты | visible | 341 x 19 | 0 | LogsEffects | 0 |
| ЛОГИ_Пакеты | visible | 531 x 14 | 0 | LogsPackages | 0 |
| ЛОГИ_Эксклюзивы | visible | 44 x 15 | 0 | LogsExclusive | 0 |
| ЛОГИ_Спеки | visible | 83 x 20 | 0 | LogsSpecs | 0 |
| ЛОГИ_Сводка | visible | 33 x 16 | 0 | — | 0 |
| ТЕХ_Подсказки | visible | 71 x 76 | 1500 | — | 70 |
| ЛОГИ_Быстрые | visible | 18 x 14 | 0 | — | 0 |

## Exported versioned tables

| Sheet | Table | Rows | Columns | SHA-256 |
|---|---|---:|---:|---|
| КАТАЛОГ СПЕКОВ | CatalogSpecsTable | 70 | 16 | `9aca88cea311d15a57f2c612f1c2d91a9bccfef15539ae6e11634fafba0dc045` |
| СПРАВОЧНИК ЭФФЕКТОВ | EffectsReferenceTable | 45 | 11 | `dc5cff3582b8d16742f51f439dc15599c07975ed2cac7fe3eb2696be4896a73f` |
| ДАННЫЕ_Комбинации | RawCombinationsTable | 70 | 11 | `f45ae4bb720cca069faa4f414bdddefba0ff81e383d6d1f455722d4d49f193d3` |
| ДАННЫЕ_Источники | RawSourcesTable | 559 | 10 | `435fb99bca56220a7bfa48d04170be585d2ccf58f25cd8f644adbddf3a509785` |
| Справка | HelpTable | 14 | 4 | `e1d56bfd4c14e322e92dbea7e834d4d6e68bd4746e29755393429023268ae980` |
| ЛОГИ_Эффекты | LogsEffects | 340 | 19 | `06207870164d3d31e1ab103f085f0734d8718303b5436daa678e0ff268293f9c` |
| ЛОГИ_Пакеты | LogsPackages | 530 | 14 | `bb42c6f25c0901ae8d969e4034bff542bdcb04953b45c473e4214351878810a3` |
| ЛОГИ_Эксклюзивы | LogsExclusive | 43 | 15 | `dc29ff21111d1ce418d0f0c52e3cd210cbf71578d50be48768d3fb559d54afbc` |
| ЛОГИ_Спеки | LogsSpecs | 82 | 20 | `35f9bdff88dd0214f36d059f853bbb68c260491e8274a005102386ac98caae35` |
