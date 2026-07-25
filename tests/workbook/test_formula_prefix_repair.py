from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile

from scripts.repair_workbook_formula_prefixes import repair_workbook, sha256_file


EXPECTED_SOURCE_SHA256 = "d2f719c2875ad5aa1b1413daee54aaa36e4d52068bfe2a898df8fcb8b296eb83"
EXPECTED_TEXTJOIN_COUNT = 72
EXPECTED_RANK_EQ_COUNT = 70
EXPECTED_CHANGED_MEMBERS = {
    "xl/workbook.xml",
    "xl/worksheets/sheet2.xml",
    "xl/worksheets/sheet9.xml",
}


def test_formula_prefix_repair_is_deterministic_and_package_safe(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    source = root / "workbook" / "archive" / "CoA_Raid_Comp_Конструктор_v9.xlsx"
    output_a = tmp_path / "candidate-a.xlsx"
    output_b = tmp_path / "candidate-b.xlsx"

    result_a = repair_workbook(source, output_a)
    result_b = repair_workbook(source, output_b)

    assert result_a.source_sha256 == EXPECTED_SOURCE_SHA256
    assert result_a.output_sha256 == result_b.output_sha256
    assert sha256_file(output_a) == sha256_file(output_b)
    assert result_a.replacements == {
        "_xludf.TEXTJOIN": EXPECTED_TEXTJOIN_COUNT,
        "_xludf.RANK.EQ": EXPECTED_RANK_EQ_COUNT,
    }
    assert set(result_a.changed_members) == EXPECTED_CHANGED_MEMBERS
    assert result_a.remaining_xludf_occurrences == 0
    assert result_a.xlfn_textjoin_occurrences == EXPECTED_TEXTJOIN_COUNT
    assert result_a.xlfn_rank_eq_occurrences == EXPECTED_RANK_EQ_COUNT
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


def test_checked_in_candidate_matches_report() -> None:
    root = Path(__file__).resolve().parents[2]
    candidate = (
        root
        / "workbook"
        / "candidates"
        / "CoA_Raid_Comp_Конструктор_v9_formula_repair.xlsx"
    )
    report = json.loads(
        (root / "workbook" / "candidates" / "FORMULA_REPAIR_REPORT.json").read_text(
            encoding="utf-8"
        )
    )

    assert candidate.is_file()
    assert sha256_file(candidate) == report["output_sha256"]
    assert report["source_sha256"] == EXPECTED_SOURCE_SHA256
    assert report["replacements"] == {
        "_xludf.TEXTJOIN": EXPECTED_TEXTJOIN_COUNT,
        "_xludf.RANK.EQ": EXPECTED_RANK_EQ_COUNT,
    }
    assert report["remaining_xludf_occurrences"] == 0
    assert report["cached_values_recalculated"] is False
