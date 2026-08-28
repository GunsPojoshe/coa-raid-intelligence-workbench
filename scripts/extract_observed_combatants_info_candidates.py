from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.combatants_candidate_extraction import (
    extract_observed_combatants_info_candidates,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the exact offline combatants-info candidate extractor. The extraction batch contains "
            "source scalar values and must remain local; the receipt is scalar-free."
        )
    )
    parser.add_argument(
        "--design",
        type=Path,
        default=Path("data/exchange/out/observed-combatants-info-mapping-design.json"),
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
    parser.add_argument("--database", type=Path, default=Path("data/warehouse/coa.duckdb"))
    parser.add_argument(
        "--extraction-output",
        type=Path,
        default=Path(
            "data/extracted/combatants-info/observed-combatants-info.candidate-extraction.json"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/observed-combatants-info-candidate-extraction.json"),
    )
    return parser.parse_args()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def main() -> int:
    args = _arguments()
    receipt = extract_observed_combatants_info_candidates(
        args.design,
        capture_path=args.capture,
        route_inventory_path=args.route_inventory,
        raw_root=args.raw_root,
        database_path=args.database,
        extraction_output_path=args.extraction_output,
    )
    _write_json(args.output, receipt)

    summary = receipt["summary"]
    boundary = receipt["decision_boundary"]
    print("OBSERVED_COMBATANTS_INFO_CANDIDATE_EXTRACTION")
    print(f"schema_version={receipt['schema_version']}")
    print(f"extraction_kind={receipt['extraction_kind']}")
    print(f"extraction_version={receipt['extraction_version']}")
    print(f"design_count={summary['design_count']}")
    print(f"selected_field_contract_count={summary['selected_field_contract_count']}")
    print(f"source_match_count={summary['source_match_count']}")
    print(f"output_observation_count={summary['output_observation_count']}")
    print(f"linked_actor_count={summary['linked_actor_count']}")
    print(f"actor_name_exact_match_count={summary['actor_name_exact_match_count']}")
    print(f"deduplicated_source_match_count={summary['deduplicated_source_match_count']}")
    print(f"integrity_check_count={summary['integrity_check_count']}")
    print(f"all_integrity_checks_passed={str(summary['all_integrity_checks_passed']).lower()}")
    print(f"automatic_persistence={str(summary['automatic_persistence']).lower()}")
    print(f"normalization_allowed={str(summary['normalization_allowed']).lower()}")
    print(f"planner_scoring_allowed={str(summary['planner_scoring_allowed']).lower()}")
    print(f"can_promote={str(boundary['can_promote']).lower()}")
    print()
    print("DESIGN_RESULTS")
    for row in receipt["design_results"]:
        print(
            " | ".join(
                [
                    f"design_id={row['design_id']}",
                    f"source_matches={row['source_match_count']}",
                    f"observations={row['output_observation_count']}",
                    f"deduplicated={row['deduplicated_source_match_count']}",
                ]
            )
        )
    print()
    print(f"private_extraction={args.extraction_output.as_posix()}")
    print(f"receipt={args.output.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
