from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile, ZipInfo

FORMULA_REPLACEMENTS: tuple[tuple[bytes, bytes], ...] = (
    (b"_xludf.TEXTJOIN", b"_xlfn.TEXTJOIN"),
    (b"_xludf.RANK.EQ", b"_xlfn.RANK.EQ"),
)


@dataclass(frozen=True)
class RepairResult:
    source: str
    output: str
    source_sha256: str
    output_sha256: str
    member_count: int
    changed_members: list[str]
    replacements: dict[str, int]
    remaining_xludf_occurrences: int
    xlfn_textjoin_occurrences: int
    xlfn_rank_eq_occurrences: int
    restored_role_formulas: int
    remaining_missing_role_formulas: int
    cached_values_recalculated: bool
    recalculation_policy: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _patch_calc_properties(data: bytes) -> bytes:
    """Force desktop Excel to rebuild formulas without reserializing workbook XML."""
    match = re.search(rb"<calcPr\b[^>]*/>", data)
    if match is None:
        raise ValueError("xl/workbook.xml does not contain a self-closing calcPr element")

    element = match.group(0)
    attributes = {
        key.decode("ascii"): value.decode("ascii")
        for key, value in re.findall(rb"([A-Za-z][A-Za-z0-9]*)=\"([^\"]*)\"", element)
    }
    attributes["calcMode"] = "auto"
    attributes["fullCalcOnLoad"] = "1"
    attributes["forceFullCalc"] = "1"

    ordered_names = ["calcId", "calcMode", "fullCalcOnLoad", "forceFullCalc"]
    remaining_names = sorted(name for name in attributes if name not in ordered_names)
    names = [name for name in ordered_names if name in attributes] + remaining_names
    patched = "<calcPr " + " ".join(f'{name}=\"{attributes[name]}\"' for name in names) + "/>"
    return data[: match.start()] + patched.encode("ascii") + data[match.end() :]


def _repair_missing_role_formulas(data: bytes) -> tuple[bytes, int]:
    """Restore role formulas missing from E6:E15 in the saved v9 package."""
    restored = 0
    for row in range(6, 16):
        empty = f'<c r="E{row}" s="74"/>'.encode("utf-8")
        formula = (
            f'<c r="E{row}" s="74" t="str"><f>'
            f'IF(OR(C{row}="",D{row}=""),"",IFERROR(INDEX(ТЕХ_Списки!$C$2:$C$71,'
            f'MATCH(C{row}&amp;"§"&amp;D{row},ТЕХ_Списки!$D$2:$D$71,0)),""))'
            f'</f><v/></c>'
        ).encode("utf-8")
        count = data.count(empty)
        if count != 1:
            raise ValueError(f"Expected exactly one empty E{row} cell, found {count}")
        data = data.replace(empty, formula, 1)
        restored += 1
    return data, restored


def repair_workbook(source: Path, output: Path) -> RepairResult:
    source = source.resolve()
    output = output.resolve()
    if source == output:
        raise ValueError("Output must be a new file; the archived baseline is read-only")
    if not source.is_file():
        raise FileNotFoundError(source)

    output.parent.mkdir(parents=True, exist_ok=True)
    temp_output = output.with_suffix(output.suffix + ".tmp")
    if temp_output.exists():
        temp_output.unlink()

    changed_members: list[str] = []
    replacement_counts = {old.decode("ascii"): 0 for old, _ in FORMULA_REPLACEMENTS}
    restored_role_formulas = 0

    try:
        with ZipFile(source, "r") as src, ZipFile(temp_output, "w") as dst:
            for info in src.infolist():
                data = src.read(info.filename)
                patched = data

                if info.filename.startswith("xl/") and info.filename.endswith(".xml"):
                    for old, new in FORMULA_REPLACEMENTS:
                        count = patched.count(old)
                        if count:
                            replacement_counts[old.decode("ascii")] += count
                            patched = patched.replace(old, new)

                if info.filename == "xl/worksheets/sheet1.xml":
                    patched, restored_role_formulas = _repair_missing_role_formulas(patched)

                if info.filename == "xl/workbook.xml":
                    patched = _patch_calc_properties(patched)

                if patched != data:
                    changed_members.append(info.filename)

                copied_info = ZipInfo(filename=info.filename, date_time=info.date_time)
                copied_info.compress_type = info.compress_type or ZIP_DEFLATED
                copied_info.comment = info.comment
                copied_info.extra = info.extra
                copied_info.internal_attr = info.internal_attr
                copied_info.external_attr = info.external_attr
                copied_info.create_system = info.create_system
                copied_info.create_version = info.create_version
                copied_info.extract_version = info.extract_version
                copied_info.flag_bits = info.flag_bits
                copied_info.volume = info.volume
                dst.writestr(copied_info, patched)

        with ZipFile(temp_output, "r") as check:
            bad_member = check.testzip()
            if bad_member is not None:
                raise BadZipFile(f"CRC failure in {bad_member}")
            xml_bytes = b"".join(
                check.read(name)
                for name in check.namelist()
                if name.startswith("xl/") and name.endswith(".xml")
            )
            member_count = len(check.namelist())
            sheet1_xml = check.read("xl/worksheets/sheet1.xml")

        remaining_xludf = xml_bytes.count(b"_xludf.")
        textjoin_count = xml_bytes.count(b"_xlfn.TEXTJOIN")
        rank_eq_count = xml_bytes.count(b"_xlfn.RANK.EQ")
        remaining_missing_role_formulas = sum(
            sheet1_xml.count(f'<c r="E{row}" s="74"/>'.encode("utf-8"))
            for row in range(6, 16)
        )
        if remaining_xludf:
            raise ValueError(f"Repair incomplete: {remaining_xludf} _xludf occurrences remain")
        if textjoin_count != replacement_counts["_xludf.TEXTJOIN"]:
            raise ValueError("TEXTJOIN replacement count mismatch")
        if rank_eq_count != replacement_counts["_xludf.RANK.EQ"]:
            raise ValueError("RANK.EQ replacement count mismatch")
        if restored_role_formulas != 10 or remaining_missing_role_formulas != 0:
            raise ValueError("Role formula restoration is incomplete")

        temp_output.replace(output)
    except Exception:
        temp_output.unlink(missing_ok=True)
        raise

    return RepairResult(
        source=str(source),
        output=str(output),
        source_sha256=sha256_file(source),
        output_sha256=sha256_file(output),
        member_count=member_count,
        changed_members=changed_members,
        replacements=replacement_counts,
        remaining_xludf_occurrences=remaining_xludf,
        xlfn_textjoin_occurrences=textjoin_count,
        xlfn_rank_eq_occurrences=rank_eq_count,
        restored_role_formulas=restored_role_formulas,
        remaining_missing_role_formulas=remaining_missing_role_formulas,
        cached_values_recalculated=False,
        recalculation_policy=(
            "Workbook calcMode=auto, fullCalcOnLoad=1 and forceFullCalc=1. "
            "Desktop Excel must open and save the candidate before it can become a golden fixture."
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Repair invalid _xludf formula prefixes without resaving the XLSX through openpyxl."
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    result = repair_workbook(args.source, args.output)
    payload = asdict(result)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
