from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile

from scripts.repair_workbook_formula_prefixes import repair_workbook, sha256_file


EXPECTED_SOURCE_SHA256 = "d2f719c2875ad5aa1b1413daee54aaa36e4d52068bfe2a898df8fcb8b296eb83"
EXPECTED_OUTPUT_SHA256 = "a0340855a74b04fd98f9e292e235d7ebec71d4c7ab11d403fbeb01d7c4749b0f"
EXPECTED_TEXTJOIN_COUNT = 72
EXPECTED_RANK_EQ_COUNT = 70
EXPECTED_ROLE_FORMULA_COUNT = 10
EXPECTED_CHANGED_MEMBERS = {
    "xl/workbook.xml",
    "xl/worksheets/sheet1.xml",
    "xl/worksheets/sheet2.xml",
    "xl/worksheets/sheet9.xml",
}


def test_formula_repair_is_deterministic_and_package_safe(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    source = root / "workbook" / "archive" / "CoA_Raid_Comp_Конструктор_v9.xlsx"
    output_a = tmp_path / "candidate-a.xlsx"
    output_b = tmp_path / "candidate-b.xlsx"

    result_a = repair_workbook(source, output_a)
    result_b = repair_workbook(source, output_b)

    assert result_a.source_sha256 == EXPECTED_SOURCE_SHA256
    assert result_a.output_sha256 == EXPECTED_OUTPUT_SHA256
    assert result_a.output_sha256 == result_b.output_sha256
    assert sha256_file(output_a) == sha256_file(output_b)
    assert output_a.read_bytes() == output_b.read_bytes()
    assert result_a.replacements == {
        "_xludf.TEXTJOIN": EXPECTED_TEXTJOIN_COUNT,
        "_xludf.RANK.EQ": EXPECTED_RANK_EQ_COUNT,
    }
    assert set(result_a.changed_members) == EXPECTED_CHANGED_MEMBERS
    assert result_a.remaining_xludf_occurrences == 0
    assert result_a.xlfn_textjoin_occurrences == EXPECTED_TEXTJOIN_COUNT
    assert result_a.xlfn_rank_eq_occurrences == EXPECTED_RANK_EQ_COUNT
    assert result_a.restored_role_formulas == EXPECTED_ROLE_FORMULA_COUNT
    assert result_a.remaining_missing_role_formulas == 0
    assert result_a.cached_values_recalculated is False

    with ZipFile(source) as original, ZipFile(output_a) as candidate:
        assert original.namelist() == candidate.namelist()
        assert candidate.testzip() is None
        for member in original.namelist():
            if member not in EXPECTED_CHANGED_MEMBERS:
                assert original.read(member) == candidate.read(member)

        workbook_xml = candidate.read("xl/workbook.xml")
        assert b'calcMode="auto"' in workbook_xml
        assert b'fullCalcOnLoad="1"' in workbook_xml
        assert b'forceFullCalc="1"' in workbook_xml

        constructor_xml = candidate.read("xl/worksheets/sheet1.xml")
        for row in range(6, 16):
            assert f'<c r="E{row}" s="74"/>'.encode("utf-8") not in constructor_xml
            assert f'C{row}&amp;"§"&amp;D{row}'.encode("utf-8") in constructor_xml


def test_generated_candidate_matches_report(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    source = root / "workbook" / "archive" / "CoA_Raid_Comp_Конструктор_v9.xlsx"
    output = tmp_path / "candidate.xlsx"
    result = repair_workbook(source, output)
    report = json.loads(
        (root / "workbook" / "candidates" / "FORMULA_REPAIR_REPORT.json").read_text(
            encoding="utf-8"
        )
    )

    assert result.output_sha256 == report["output_sha256"] == EXPECTED_OUTPUT_SHA256
    assert report["source_sha256"] == EXPECTED_SOURCE_SHA256
    assert report["replacements"] == {
        "_xludf.TEXTJOIN": EXPECTED_TEXTJOIN_COUNT,
        "_xludf.RANK.EQ": EXPECTED_RANK_EQ_COUNT,
    }
    assert report["restored_role_formulas"] == EXPECTED_ROLE_FORMULA_COUNT
    assert report["remaining_missing_role_formulas"] == 0
    assert report["remaining_xludf_occurrences"] == 0
    assert report["cached_values_recalculated"] is False
