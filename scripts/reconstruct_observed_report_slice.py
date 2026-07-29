from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.report_slice_reconstruction import (
    reconstruct_observed_report_slice,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Deterministically merge the two private normalized report-slice batches into one "
            "local canonical slice and emit a scalar-free receipt. No network requests are "
            "performed."
        )
    )
    parser.add_argument(
        "--normalization",
        type=Path,
        default=Path("data/exchange/out/observed-report-slice-normalization.json"),
    )
    parser.add_argument(
        "--normalized-output-dir",
        type=Path,
        default=Path("data/normalized/report-slice"),
    )
    parser.add_argument(
        "--reconstructed-output",
        type=Path,
        default=Path("data/reconstructed/report-slice/observed-report-slice.reconstructed.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/observed-report-slice-reconstruction.json"),
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
    receipt = reconstruct_observed_report_slice(
        args.normalization,
        normalized_output_dir=args.normalized_output_dir,
        reconstructed_output_path=args.reconstructed_output,
    )
    _write_json(args.output, receipt)

    summary = receipt["summary"]
    input_counts = summary["input_counts"]
    output_counts = summary["output_counts"]
    boundary = receipt["decision_boundary"]
    print("OBSERVED_REPORT_SLICE_DETERMINISTIC_RECONSTRUCTION")
    print(f"schema_version={receipt['schema_version']}")
    print(f"reconstruction_kind={receipt['reconstruction_kind']}")
    print(f"reconstruction_version={receipt['reconstruction_version']}")
    print(f"source_batch_count={summary['source_batch_count']}")
    print(f"input_reports={input_counts['reports']}")
    print(f"output_reports={output_counts['reports']}")
    print(f"input_encounters={input_counts['encounters']}")
    print(f"output_encounters={output_counts['encounters']}")
    print(f"output_actors={output_counts['actors']}")
    print(f"output_participants={output_counts['participants']}")
    print(f"output_aura_events={output_counts['aura_events']}")
    print(f"output_rejects={output_counts['rejects']}")
    print(f"duplicate_report_count={summary['duplicate_report_count']}")
    print(f"duplicate_encounter_count={summary['duplicate_encounter_count']}")
    print(f"field_conflict_count={summary['field_conflict_count']}")
    print(
        f"all_input_batch_hashes_verified={str(summary['all_input_batch_hashes_verified']).lower()}"
    )
    print(f"all_linkage_checks_passed={str(summary['all_linkage_checks_passed']).lower()}")
    print(
        "ready_for_selected_parser_persistence="
        f"{str(summary['ready_for_selected_parser_persistence']).lower()}"
    )
    print(f"mechanic_semantics_verified={str(summary['mechanic_semantics_verified']).lower()}")
    print(f"full_report_slice_complete={str(summary['full_report_slice_complete']).lower()}")
    print(
        "reconstructed_file_contains_source_scalar_values="
        f"{str(boundary['reconstructed_file_contains_source_scalar_values']).lower()}"
    )
    print()
    print("LINKAGE_CHECKS")
    for name, passed in sorted(receipt["linkage_checks"].items()):
        print(f"{name}={str(passed).lower()}")
    print()
    print(f"receipt={args.output.as_posix()}")
    print(f"private_reconstructed_output={args.reconstructed_output.as_posix()}")
    print("Do not share or commit the reconstructed canonical slice file.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
