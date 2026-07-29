from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.report_slice_mapping_publication import (
    publish_observed_report_slice_mappings,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Publish exactly reviewed report-slice parser mappings into config/mappings and emit "
            "a scalar-free receipt. Gameplay semantics, combatants enrichment and aura semantics "
            "remain unavailable."
        )
    )
    parser.add_argument(
        "--promotion",
        type=Path,
        default=Path("data/exchange/out/observed-report-slice-mapping-promotion.json"),
    )
    parser.add_argument(
        "--staged-mapping-dir",
        type=Path,
        default=Path("data/exchange/out/verified-mappings"),
    )
    parser.add_argument(
        "--target-mapping-dir",
        type=Path,
        default=Path("config/mappings"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/observed-report-slice-mapping-publication.json"),
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
    receipt = publish_observed_report_slice_mappings(
        args.promotion,
        staged_mapping_dir=args.staged_mapping_dir,
        target_mapping_dir=args.target_mapping_dir,
    )
    _write_json(args.output, receipt)

    summary = receipt["summary"]
    boundary = receipt["decision_boundary"]
    print("OBSERVED_REPORT_SLICE_MAPPING_PUBLICATION")
    print(f"schema_version={receipt['schema_version']}")
    print(f"publication_kind={receipt['publication_kind']}")
    print(f"mapping_count={summary['mapping_count']}")
    print(f"field_contract_count={summary['field_contract_count']}")
    print(
        "all_staged_files_match_promotion="
        f"{str(summary['all_staged_files_match_promotion']).lower()}"
    )
    print(f"all_targets_published={str(summary['all_targets_published']).lower()}")
    print(f"contains_source_scalar_values={str(summary['contains_source_scalar_values']).lower()}")
    print(
        "selected_parser_normalization_allowed="
        f"{str(summary['selected_parser_normalization_allowed']).lower()}"
    )
    print(f"mechanic_semantics_verified={str(summary['mechanic_semantics_verified']).lower()}")
    print(f"full_report_slice_complete={str(summary['full_report_slice_complete']).lower()}")
    print()
    print("PUBLISHED_MAPPINGS")
    for row in receipt["published_mappings"]:
        print(
            f"mapping_id={row['mapping_id']} | status={row['status']} | "
            f"field_contract_count={row['field_contract_count']} | "
            f"already_current={str(row['already_current']).lower()} | "
            f"target={row['target_path']}"
        )
    print()
    print("BOUNDARIES")
    print(
        "combatants_info_enrichment_available="
        f"{str(boundary['combatants_info_enrichment_available']).lower()}"
    )
    print(f"aura_normalization_available={str(boundary['aura_normalization_available']).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
