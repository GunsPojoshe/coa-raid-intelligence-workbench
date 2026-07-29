from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.report_slice_mapping_promotion import (
    promote_observed_report_slice_candidate_mappings,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Recompute and manually promote exact report-slice candidate mappings into a "
            "scalar-free verified mapping packet. No network requests or repository publication "
            "are performed."
        )
    )
    parser.add_argument(
        "--selection",
        type=Path,
        default=Path("data/exchange/out/observed-report-slice-field-selection.json"),
    )
    parser.add_argument(
        "--validation",
        type=Path,
        default=Path(
            "data/exchange/out/observed-report-slice-candidate-mapping-validation.json"
        ),
    )
    parser.add_argument(
        "--mapping-dir",
        type=Path,
        default=Path("data/exchange/out/candidate-mappings"),
    )
    parser.add_argument(
        "--capture",
        type=Path,
        default=Path("data/exchange/out/observed-report-slice-capture.json"),
    )
    parser.add_argument(
        "--route-inventory",
        type=Path,
        default=Path("data/exchange/out/spa-api-route-inventory.json"),
    )
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    parser.add_argument("--reviewed-by", required=True)
    parser.add_argument("--reviewed-at", required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/observed-report-slice-mapping-promotion.json"),
    )
    parser.add_argument(
        "--verified-output-dir",
        type=Path,
        default=Path("data/exchange/out/verified-mappings"),
    )
    return parser.parse_args()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def main() -> int:
    args = _arguments()
    promotion = promote_observed_report_slice_candidate_mappings(
        args.selection,
        args.validation,
        mapping_dir=args.mapping_dir,
        capture_path=args.capture,
        route_inventory_path=args.route_inventory,
        raw_root=args.raw_root,
        reviewed_by=args.reviewed_by,
        reviewed_at=args.reviewed_at,
    )
    _write_json(args.output, promotion)

    written: list[Path] = []
    for row in promotion["verified_mappings"]:
        path = args.verified_output_dir / row["mapping_file"]
        _write_json(path, row["mapping"])
        written.append(path)

    summary = promotion["summary"]
    boundary = promotion["decision_boundary"]
    print("OBSERVED_REPORT_SLICE_MAPPING_PROMOTION")
    print(f"schema_version={promotion['schema_version']}")
    print(f"promotion_kind={promotion['promotion_kind']}")
    print(f"mapping_count={summary['mapping_count']}")
    print(f"field_contract_count={summary['field_contract_count']}")
    print(f"exact_raw_archive_count={summary['exact_raw_archive_count']}")
    print(f"deferred_scope_count={summary['deferred_scope_count']}")
    print(
        "all_candidate_files_match_selection="
        f"{str(summary['all_candidate_files_match_selection']).lower()}"
    )
    print(f"all_raw_archives_verified={str(summary['all_raw_archives_verified']).lower()}")
    print(f"all_dry_run_counts_match={str(summary['all_dry_run_counts_match']).lower()}")
    print(f"cross_payload_consistent={str(summary['cross_payload_consistent']).lower()}")
    print(f"contains_source_scalar_values={str(summary['contains_source_scalar_values']).lower()}")
    print(
        "ready_to_publish_verified_mappings="
        f"{str(summary['ready_to_publish_verified_mappings']).lower()}"
    )
    print(f"mechanic_semantics_verified={str(boundary['mechanic_semantics_verified']).lower()}")
    print(f"normalization_allowed={str(boundary['normalization_allowed']).lower()}")
    print()
    print("VERIFIED_MAPPING_OUTPUTS")
    for row, path in zip(promotion["verified_mappings"], written, strict=True):
        print(
            f"mapping_id={row['mapping_id']} | status={row['mapping']['status']} | "
            f"field_contract_count={row['field_contract_count']} | output={path.as_posix()}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
