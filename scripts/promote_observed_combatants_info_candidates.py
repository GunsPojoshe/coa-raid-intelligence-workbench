from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.combatants_candidate_promotion import (
    promote_observed_combatants_info_candidates,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Manually validate and promote the exact private combatants-info candidate extraction "
            "into a scalar-free parser-observation promotion receipt. No network requests, "
            "DuckDB writes, core actor mutations or gameplay-semantic promotion are performed."
        )
    )
    parser.add_argument(
        "--extraction-receipt",
        type=Path,
        default=Path("data/exchange/out/observed-combatants-info-candidate-extraction.json"),
    )
    parser.add_argument(
        "--private-extraction",
        type=Path,
        default=Path(
            "data/extracted/combatants-info/observed-combatants-info.candidate-extraction.json"
        ),
    )
    parser.add_argument("--reviewed-by", required=True)
    parser.add_argument("--reviewed-at", required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/observed-combatants-info-candidate-promotion.json"),
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
    promotion = promote_observed_combatants_info_candidates(
        args.extraction_receipt,
        args.private_extraction,
        reviewed_by=args.reviewed_by,
        reviewed_at=args.reviewed_at,
    )
    _write_json(args.output, promotion)

    summary = promotion["summary"]
    boundary = promotion["decision_boundary"]
    print("OBSERVED_COMBATANTS_INFO_CANDIDATE_PROMOTION")
    print(f"schema_version={promotion['schema_version']}")
    print(f"promotion_kind={promotion['promotion_kind']}")
    print(f"promotion_version={promotion['promotion_version']}")
    print(f"design_count={summary['design_count']}")
    print(f"selected_field_contract_count={summary['selected_field_contract_count']}")
    print(f"source_match_count={summary['source_match_count']}")
    print(f"output_observation_count={summary['output_observation_count']}")
    print(f"deduplicated_source_match_count={summary['deduplicated_source_match_count']}")
    print(f"linked_actor_count={summary['linked_actor_count']}")
    print(f"integrity_check_count={summary['integrity_check_count']}")
    print(f"all_integrity_checks_passed={str(summary['all_integrity_checks_passed']).lower()}")
    print(f"contains_source_scalar_values={str(summary['contains_source_scalar_values']).lower()}")
    print(
        "ready_for_immutable_observation_persistence="
        f"{str(summary['ready_for_immutable_observation_persistence']).lower()}"
    )
    print(f"core_entity_mutation_allowed={str(summary['core_entity_mutation_allowed']).lower()}")
    print(
        "companion_addon_provenance_verified="
        f"{str(boundary['companion_addon_provenance_verified']).lower()}"
    )
    print(
        "nested_collection_semantics_verified="
        f"{str(boundary['nested_collection_semantics_verified']).lower()}"
    )
    print(f"mechanic_semantics_verified={str(boundary['mechanic_semantics_verified']).lower()}")
    print(f"planner_scoring_allowed={str(boundary['planner_scoring_allowed']).lower()}")
    print(f"output={args.output.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
