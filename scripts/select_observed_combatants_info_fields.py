from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector import select_observed_combatants_info_fields


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Select bounded scalar-free combatants-info parser fields from exact review packets. "
            "No mapping is created and no network request is performed."
        )
    )
    parser.add_argument(
        "--deep-review",
        type=Path,
        default=Path("data/exchange/out/observed-combatants-info-deep-scope-review.json"),
    )
    parser.add_argument(
        "--scope-review",
        type=Path,
        default=Path("data/exchange/out/observed-report-slice-scope-review.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/observed-combatants-info-field-selection.json"),
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
    selection = select_observed_combatants_info_fields(
        args.deep_review,
        args.scope_review,
    )
    _write_json(args.output, selection)

    summary = selection["summary"]
    boundary = selection["decision_boundary"]
    print("OBSERVED_COMBATANTS_INFO_FIELD_SELECTION")
    print(f"schema_version={selection['schema_version']}")
    print(f"selection_kind={selection['selection_kind']}")
    print(f"selection_group_count={summary['selection_group_count']}")
    print(f"selected_scope_count={summary['selected_scope_count']}")
    print(f"selected_field_contract_count={summary['selected_field_contract_count']}")
    print(f"linkage_contract_count={summary['linkage_contract_count']}")
    print(f"deferred_field_count={summary['deferred_field_count']}")
    print(f"missing_optional_scope_count={summary['missing_optional_scope_count']}")
    print(f"candidate_mapping_files_ready={str(summary['candidate_mapping_files_ready']).lower()}")
    print(
        f"ready_for_manual_mapping_design={str(summary['ready_for_manual_mapping_design']).lower()}"
    )
    print(
        "combatants_info_enrichment_available="
        f"{str(summary['combatants_info_enrichment_available']).lower()}"
    )
    print(f"normalization_allowed={str(summary['normalization_allowed']).lower()}")
    print(f"planner_scoring_allowed={str(summary['planner_scoring_allowed']).lower()}")
    print(f"can_promote={str(boundary['can_promote']).lower()}")
    print()
    print("SELECTION_GROUPS")
    for group in selection["selection_groups"]:
        print(
            " | ".join(
                [
                    f"group_id={group['group_id']}",
                    f"scope={group['scope']}",
                    f"mapping_strategy={group['mapping_strategy']}",
                    f"selected_field_count={group['selected_field_count']}",
                    f"mapping_status={group['mapping_status']}",
                ]
            )
        )
    print()
    print(f"receipt={args.output.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
