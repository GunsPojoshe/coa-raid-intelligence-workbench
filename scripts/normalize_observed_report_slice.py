from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.report_slice_normalization import (
    normalize_observed_report_slice_selected_parser_mappings,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Normalize the two published report-slice parser mappings into local canonical batch "
            "files and emit a scalar-free receipt. No network requests are performed."
        )
    )
    parser.add_argument(
        "--publication",
        type=Path,
        default=Path("data/exchange/out/observed-report-slice-mapping-publication.json"),
    )
    parser.add_argument(
        "--mapping-dir",
        type=Path,
        default=Path("config/mappings"),
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
        "--normalized-output-dir",
        type=Path,
        default=Path("data/normalized/report-slice"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/observed-report-slice-normalization.json"),
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
    receipt = normalize_observed_report_slice_selected_parser_mappings(
        args.publication,
        mapping_dir=args.mapping_dir,
        capture_path=args.capture,
        route_inventory_path=args.route_inventory,
        raw_root=args.raw_root,
        normalized_output_dir=args.normalized_output_dir,
    )
    _write_json(args.output, receipt)

    summary = receipt["summary"]
    counts = summary["aggregate_counts"]
    boundary = receipt["decision_boundary"]
    print("OBSERVED_REPORT_SLICE_SELECTED_PARSER_NORMALIZATION")
    print(f"schema_version={receipt['schema_version']}")
    print(f"normalization_kind={receipt['normalization_kind']}")
    print(f"mapping_count={summary['mapping_count']}")
    print(f"field_contract_count={summary['field_contract_count']}")
    print(f"exact_raw_archive_count={summary['exact_raw_archive_count']}")
    print(f"reports={counts['reports']}")
    print(f"encounters={counts['encounters']}")
    print(f"actors={counts['actors']}")
    print(f"participants={counts['participants']}")
    print(f"aura_events={counts['aura_events']}")
    print(f"rejects={counts['rejects']}")
    print(f"cross_payload_consistent={str(summary['cross_payload_consistent']).lower()}")
    print(
        "ready_for_deterministic_reconstruction="
        f"{str(summary['ready_for_deterministic_reconstruction']).lower()}"
    )
    print(f"mechanic_semantics_verified={str(summary['mechanic_semantics_verified']).lower()}")
    print(f"full_report_slice_complete={str(summary['full_report_slice_complete']).lower()}")
    print(
        "normalized_batch_files_contain_source_scalar_values="
        f"{str(boundary['normalized_batch_files_contain_source_scalar_values']).lower()}"
    )
    print()
    print("NORMALIZED_BATCHES")
    for row in receipt["normalized_batches"]:
        row_counts = row["counts"]
        print(
            f"mapping_id={row['mapping_id']} | batch={row['normalized_batch_file']} | "
            f"reports={row_counts['reports']} | encounters={row_counts['encounters']} | "
            f"actors={row_counts['actors']} | participants={row_counts['participants']} | "
            f"aura_events={row_counts['aura_events']} | rejects={row_counts['rejects']}"
        )
    print()
    print("CROSS_PAYLOAD_CHECKS")
    for name, passed in sorted(receipt["cross_payload_checks"].items()):
        print(f"{name}={str(passed).lower()}")
    print()
    print(f"receipt={args.output.as_posix()}")
    print("Do not share or commit files from the normalized output directory.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
