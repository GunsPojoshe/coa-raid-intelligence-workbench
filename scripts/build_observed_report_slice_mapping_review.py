from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.report_slice_mapping_review import (
    build_observed_report_slice_mapping_review,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build scalar-free full-root mapping-review packets for the exact observed "
            "report slice. No network requests are performed."
        )
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
    parser.add_argument("--max-nodes-per-endpoint", type=int, default=500_000)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/observed-report-slice-mapping-review.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    review = build_observed_report_slice_mapping_review(
        args.capture,
        route_inventory_path=args.route_inventory,
        raw_root=args.raw_root,
        max_nodes_per_endpoint=args.max_nodes_per_endpoint,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(
        json.dumps(review, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(args.output)

    summary = review["summary"]
    print("OBSERVED_REPORT_SLICE_MAPPING_REVIEW")
    print(f"schema_version={review['schema_version']}")
    print(f"review_kind={review['review_kind']}")
    print(f"endpoint_count={summary['endpoint_count']}")
    print(f"raw_archive_count={summary['raw_archive_count']}")
    print(f"field_path_count={summary['field_path_count']}")
    print(f"node_occurrence_count={summary['node_occurrence_count']}")
    print(f"numeric_map_path_count={summary['numeric_map_path_count']}")
    print(f"nullable_path_count={summary['nullable_path_count']}")
    print(f"array_path_count={summary['array_path_count']}")
    print(f"object_path_count={summary['object_path_count']}")
    print(f"candidate_collection_count={summary['candidate_collection_count']}")
    print(
        "all_archives_consistent="
        f"{str(summary['all_archives_consistent']).lower()}"
    )
    print(
        "contains_source_scalar_values="
        f"{str(summary['contains_source_scalar_values']).lower()}"
    )
    print(
        "semantic_verification_required="
        f"{str(summary['semantic_verification_required']).lower()}"
    )
    print(f"normalization_allowed={str(summary['normalization_allowed']).lower()}")
    print(
        "ready_for_manual_mapping_review="
        f"{str(summary['ready_for_manual_mapping_review']).lower()}"
    )
    print()
    print("ENDPOINT_MAPPING_SUMMARIES")
    for endpoint in review["endpoints"]:
        endpoint_summary = endpoint["summary"]
        print(
            f"kind={endpoint['endpoint_kind']} | route={endpoint['route_template']} | "
            f"scope={endpoint['scope']} | field_path_count="
            f"{endpoint_summary['field_path_count']} | node_occurrence_count="
            f"{endpoint_summary['node_occurrence_count']} | numeric_map_path_count="
            f"{endpoint_summary['numeric_map_path_count']} | nullable_path_count="
            f"{endpoint_summary['nullable_path_count']} | array_path_count="
            f"{endpoint_summary['array_path_count']} | object_path_count="
            f"{endpoint_summary['object_path_count']} | candidate_collection_count="
            f"{endpoint_summary['candidate_collection_count']} | "
            f"review_status={endpoint['review_status']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
