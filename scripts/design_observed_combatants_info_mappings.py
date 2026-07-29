from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.combatants_mapping_design import (
    design_observed_combatants_info_mappings,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a scalar-free storage-aware mapping design packet for the exact "
            "observed combatants-info field selection. No mapping files are created."
        )
    )
    parser.add_argument(
        "--selection",
        type=Path,
        default=Path("data/exchange/out/observed-combatants-info-field-selection.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/observed-combatants-info-mapping-design.json"),
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
    design = design_observed_combatants_info_mappings(args.selection)
    _write_json(args.output, design)

    summary = design["summary"]
    boundary = design["decision_boundary"]
    print("OBSERVED_COMBATANTS_INFO_MAPPING_DESIGN")
    print(f"schema_version={design['schema_version']}")
    print(f"design_kind={design['design_kind']}")
    print(f"mapping_design_count={summary['mapping_design_count']}")
    print(f"source_group_count={summary['source_group_count']}")
    print(f"selected_field_contract_count={summary['selected_field_contract_count']}")
    print(f"actor_enrichment_design_count={summary['actor_enrichment_design_count']}")
    print(f"context_observation_design_count={summary['context_observation_design_count']}")
    print(f"nested_observation_design_count={summary['nested_observation_design_count']}")
    print(f"dedicated_extractor_design_count={summary['dedicated_extractor_design_count']}")
    print(
        "generic_normalizer_compatible_design_count="
        f"{summary['generic_normalizer_compatible_design_count']}"
    )
    print(f"expected_outer_actor_link_count={summary['expected_outer_actor_link_count']}")
    print(f"deferred_field_count={summary['deferred_field_count']}")
    print(f"missing_optional_scope_count={summary['missing_optional_scope_count']}")
    print(f"candidate_mapping_files_ready={str(summary['candidate_mapping_files_ready']).lower()}")
    print(
        "ready_for_candidate_extractor_implementation="
        f"{str(summary['ready_for_candidate_extractor_implementation']).lower()}"
    )
    print(
        "combatants_info_enrichment_available="
        f"{str(summary['combatants_info_enrichment_available']).lower()}"
    )
    print(f"normalization_allowed={str(summary['normalization_allowed']).lower()}")
    print(f"planner_scoring_allowed={str(summary['planner_scoring_allowed']).lower()}")
    print(f"can_promote={str(boundary['can_promote']).lower()}")
    print()
    print("MAPPING_DESIGNS")
    for row in design["mapping_designs"]:
        print(
            " | ".join(
                [
                    f"design_id={row['design_id']}",
                    f"design_type={row['design_type']}",
                    f"selected_fields={row['selected_field_count']}",
                    f"expected_matches={row['expected_source_match_count']}",
                    f"target_entity={row['target']['entity_type']}",
                    f"implementation_status={row['implementation_status']}",
                ]
            )
        )
    print()
    print(f"receipt={args.output.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
