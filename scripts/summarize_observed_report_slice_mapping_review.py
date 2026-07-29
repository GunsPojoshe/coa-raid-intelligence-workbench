from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.report_slice_mapping_summary import (
    summarize_observed_report_slice_mapping_review,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize exact report-slice mapping reviews into scalar-free wildcarded "
            "candidate shortlists. No network requests are performed."
        )
    )
    parser.add_argument(
        "--mapping-review",
        type=Path,
        default=Path("data/exchange/out/observed-report-slice-mapping-review.json"),
    )
    parser.add_argument(
        "--structural-review",
        type=Path,
        default=Path("data/exchange/out/observed-report-slice-structural-review.json"),
    )
    parser.add_argument("--max-candidates-per-entity", type=int, default=8)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/observed-report-slice-mapping-summary.json"),
    )
    return parser.parse_args()


def _join(values: object) -> str:
    if not isinstance(values, list):
        return ""
    return ",".join(str(value) for value in values)


def main() -> int:
    args = _arguments()
    summary = summarize_observed_report_slice_mapping_review(
        args.mapping_review,
        args.structural_review,
        max_candidates_per_entity=args.max_candidates_per_entity,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(args.output)

    totals = summary["summary"]
    boundary = summary["decision_boundary"]
    print("OBSERVED_REPORT_SLICE_MAPPING_SUMMARY")
    print(f"schema_version={summary['schema_version']}")
    print(f"summary_kind={summary['summary_kind']}")
    print(f"endpoint_count={totals['endpoint_count']}")
    print(f"field_path_count={totals['field_path_count']}")
    print(f"node_occurrence_count={totals['node_occurrence_count']}")
    print(
        "source_candidate_collection_count="
        f"{totals['source_candidate_collection_count']}"
    )
    print(f"aggregated_candidate_path_count={totals['aggregated_candidate_path_count']}")
    print(f"shortlist_row_count={totals['shortlist_row_count']}")
    print(f"all_archives_consistent={str(totals['all_archives_consistent']).lower()}")
    print(
        f"contains_source_scalar_values={str(totals['contains_source_scalar_values']).lower()}"
    )
    print(
        "ready_for_manual_scope_selection="
        f"{str(totals['ready_for_manual_scope_selection']).lower()}"
    )
    print(f"automatic_scope_selection={str(boundary['automatic_scope_selection']).lower()}")
    print(f"can_promote={str(boundary['can_promote']).lower()}")
    print(f"normalization_allowed={str(boundary['normalization_allowed']).lower()}")
    print()
    print("ENDPOINT_SCOPE_SUMMARIES")
    for endpoint in summary["endpoints"]:
        endpoint_summary = endpoint["summary"]
        print(
            f"kind={endpoint['endpoint_kind']} | route={endpoint['route_template']} | "
            f"field_path_count={endpoint_summary['field_path_count']} | "
            "source_candidate_collection_count="
            f"{endpoint_summary['source_candidate_collection_count']} | "
            "aggregated_candidate_path_count="
            f"{endpoint_summary['aggregated_candidate_path_count']} | "
            f"shortlist_row_count={endpoint_summary['shortlist_row_count']} | "
            f"review_status={endpoint['review_status']}"
        )

    print()
    print("TOP_LEVEL_FIELDS")
    for endpoint in summary["endpoints"]:
        for field in endpoint["top_level_fields"]:
            print(
                f"kind={endpoint['endpoint_kind']} | name={field['name']} | "
                f"path={field['path']} | types={_join(field['types'])} | "
                f"nullable={str(field['nullable']).lower()} | "
                f"is_array={str(field['is_array']).lower()} | "
                f"is_object={str(field['is_object']).lower()}"
            )

    print()
    print("CANDIDATE_SHORTLISTS")
    for endpoint in summary["endpoints"]:
        for entity, rows in endpoint["candidate_shortlists"].items():
            for row in rows:
                print(
                    f"kind={endpoint['endpoint_kind']} | entity={entity} | "
                    f"rank={row['rank']} | path={row['path']} | score={row['score']} | "
                    f"source_candidate_count={row['source_candidate_count']} | "
                    f"item_count_total={row['item_count_total']} | "
                    f"object_item_count_total={row['object_item_count_total']} | "
                    f"matched_hints={_join(row['matched_hints'])} | "
                    f"observed_keys={_join(row['observed_keys'])} | "
                    f"semantic_status={row['semantic_status']}"
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
