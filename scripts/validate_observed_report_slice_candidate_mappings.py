from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.report_slice_mapping_validation import (
    validate_observed_report_slice_candidate_mappings,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate exact candidate report-slice mappings with in-memory normalization dry runs. "
            "No network requests or mapping promotion are performed."
        )
    )
    parser.add_argument(
        "--selection",
        type=Path,
        default=Path("data/exchange/out/observed-report-slice-field-selection.json"),
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
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "data/exchange/out/observed-report-slice-candidate-mapping-validation.json"
        ),
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
    validation = validate_observed_report_slice_candidate_mappings(
        args.selection,
        mapping_dir=args.mapping_dir,
        capture_path=args.capture,
        route_inventory_path=args.route_inventory,
        raw_root=args.raw_root,
    )
    _write_json(args.output, validation)

    summary = validation["summary"]
    boundary = validation["decision_boundary"]
    counts = summary["aggregate_dry_run_counts"]
    print("OBSERVED_REPORT_SLICE_CANDIDATE_MAPPING_VALIDATION")
    print(f"schema_version={validation['schema_version']}")
    print(f"validation_kind={validation['validation_kind']}")
    print(f"mapping_count={summary['mapping_count']}")
    print(f"exact_raw_archive_count={summary['exact_raw_archive_count']}")
    print(f"field_contract_count={summary['field_contract_count']}")
    print(f"dry_run_reports={counts['reports']}")
    print(f"dry_run_encounters={counts['encounters']}")
    print(f"dry_run_actors={counts['actors']}")
    print(f"dry_run_participants={counts['participants']}")
    print(f"dry_run_aura_events={counts['aura_events']}")
    print(f"dry_run_rejects={counts['rejects']}")
    print(
        "all_candidate_files_match_selection="
        f"{str(summary['all_candidate_files_match_selection']).lower()}"
    )
    print(f"all_raw_archives_verified={str(summary['all_raw_archives_verified']).lower()}")
    print(f"all_dry_run_counts_match={str(summary['all_dry_run_counts_match']).lower()}")
    print(f"cross_payload_consistent={str(summary['cross_payload_consistent']).lower()}")
    print(f"contains_source_scalar_values={str(summary['contains_source_scalar_values']).lower()}")
    print(f"ready_for_manual_promotion={str(boundary['ready_for_manual_promotion']).lower()}")
    print(f"can_promote={str(boundary['can_promote']).lower()}")
    print(f"normalization_allowed={str(boundary['normalization_allowed']).lower()}")
    print()
    print("MAPPING_DRY_RUNS")
    for row in validation["mappings"]:
        row_counts = row["dry_run_counts"]
        print(
            f"mapping_id={row['mapping_id']} | status={row['status']} | "
            f"field_contract_count={row['field_contract_count']} | "
            f"reports={row_counts['reports']} | encounters={row_counts['encounters']} | "
            f"actors={row_counts['actors']} | participants={row_counts['participants']} | "
            f"aura_events={row_counts['aura_events']} | rejects={row_counts['rejects']} | "
            f"dry_run_counts_match={str(row['dry_run_counts_match']).lower()}"
        )
    print()
    print("CROSS_PAYLOAD_CHECKS")
    for name, passed in sorted(validation["cross_payload_checks"].items()):
        print(f"{name}={str(passed).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
