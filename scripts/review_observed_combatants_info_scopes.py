from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.combatants_scope_review import (
    build_observed_combatants_info_deep_scope_review,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a scalar-free deep structural review packet for the exact observed "
            "combatants-info archive. No network requests are performed."
        )
    )
    parser.add_argument(
        "--mapping-review",
        type=Path,
        default=Path("data/exchange/out/observed-report-slice-mapping-review.json"),
    )
    parser.add_argument(
        "--persistence",
        type=Path,
        default=Path("data/exchange/out/observed-report-slice-persistence.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/observed-combatants-info-deep-scope-review.json"),
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
    review = build_observed_combatants_info_deep_scope_review(
        args.mapping_review,
        args.persistence,
    )
    _write_json(args.output, review)

    summary = review["summary"]
    boundary = review["decision_boundary"]
    print("OBSERVED_COMBATANTS_INFO_DEEP_SCOPE_REVIEW")
    print(f"schema_version={review['schema_version']}")
    print(f"review_kind={review['review_kind']}")
    print(f"scope_candidate_count={summary['scope_candidate_count']}")
    print(f"present_scope_count={summary['present_scope_count']}")
    print(f"required_scope_count={summary['required_scope_count']}")
    print(f"required_scope_present_count={summary['required_scope_present_count']}")
    print(f"optional_scope_present_count={summary['optional_scope_present_count']}")
    print(f"optional_scope_missing_count={summary['optional_scope_missing_count']}")
    print(f"direct_field_count={summary['direct_field_count']}")
    print(
        "selected_parser_persistence_verified="
        f"{str(summary['selected_parser_persistence_verified']).lower()}"
    )
    print(
        "ready_for_manual_combatants_field_selection="
        f"{str(summary['ready_for_manual_combatants_field_selection']).lower()}"
    )
    print(
        "combatants_info_enrichment_available="
        f"{str(boundary['combatants_info_enrichment_available']).lower()}"
    )
    print(f"can_promote={str(boundary['can_promote']).lower()}")
    print(f"normalization_allowed={str(boundary['normalization_allowed']).lower()}")
    print(f"planner_scoring_allowed={str(boundary['planner_scoring_allowed']).lower()}")
    print()
    print("PRESENT_SCOPES")
    for scope in review["scopes"]:
        scope_summary = scope["summary"]
        print(
            " | ".join(
                [
                    f"scope={scope['scope']}",
                    f"required={str(scope['required_scope']).lower()}",
                    f"occurrences={scope_summary['scope_occurrence_count']}",
                    f"direct_fields={scope_summary['direct_field_count']}",
                    f"all_occurrence_fields={scope_summary['fields_observed_on_all_scope_occurrences']}",
                ]
            )
        )
    print()
    print("MISSING_OPTIONAL_SCOPES")
    for row in review["missing_optional_scopes"]:
        print(f"scope={row['scope']} | reason={row['reason']}")
    print()
    print(f"receipt={args.output.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
