import json
from collections import Counter
from pathlib import Path


EXPECTED_WORKBOOK_SHA256 = "d2f719c2875ad5aa1b1413daee54aaa36e4d52068bfe2a898df8fcb8b296eb83"


def _load(root: Path, name: str) -> dict:
    return json.loads((root / "baseline" / name).read_text(encoding="utf-8"))


def test_frozen_workbook_contract() -> None:
    root = Path(__file__).resolve().parents[2]
    inventory = _load(root, "workbook_inventory.json")
    manifest = _load(root, "source_manifest.json")
    fixture = _load(root, "workbook_v9_observed_default_state.json")

    assert inventory["source"]["sha256"] == EXPECTED_WORKBOOK_SHA256
    assert inventory["workbook"]["sheet_count"] == 16
    assert inventory["workbook"]["defined_name_count"] == 0
    assert inventory["workbook"]["openpyxl_resave_safe"] is False
    assert inventory["workbook"]["total_formula_count"] == 4355
    assert inventory["workbook"]["total_cached_formula_errors"] == 282

    errors_by_sheet = Counter(
        item["sheet"] for item in inventory["workbook"]["cached_formula_error_cells"]
    )
    assert errors_by_sheet == {
        "ТЕХ_Расчет": 140,
        "КАТАЛОГ СПЕКОВ": 70,
        "ТЕХ_Подсказки": 70,
        "СРАВНЕНИЕ СПЕКОВ": 2,
    }

    tables = {item["table"]: item for item in manifest["table_exports"]}
    assert tables["RawCombinationsTable"]["data_rows"] == 70
    assert tables["EffectsReferenceTable"]["data_rows"] == 45
    assert tables["RawSourcesTable"]["data_rows"] == 559
    for item in tables.values():
        assert (root / "baseline" / item["path"]).exists()

    assert fixture["fixture_status"] == "observed_not_approved_25_roster"
    assert fixture["context"]["target_size"] == 25
    assert len(fixture["slots"]) == 25
    assert fixture["summary"]["counted_players"] == 0
    assert fixture["log_summary"]["workbook_timeline_events"] == 12_148_016
    assert fixture["log_summary"]["project_document_alternate_timeline_events"] == 12_147_472
    assert fixture["log_summary"]["difference"] == 544
