from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.report_slice_review import (
    review_observed_report_slice_capture,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Verify exact observed report-slice archives and emit scalar-free structural facts."
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
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/observed-report-slice-structural-review.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    review = review_observed_report_slice_capture(
        args.capture,
        route_inventory_path=args.route_inventory,
        raw_root=args.raw_root,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(
        json.dumps(review, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(args.output)

    summary = review["summary"]
    print("OBSERVED_REPORT_SLICE_STRUCTURAL_REVIEW")
    print(f"schema_version={review['schema_version']}")
    print(f"review_kind={review['review_kind']}")
    print(f"route_inventory_hash={review['provenance']['route_inventory_hash']}")
    print(f"raw_archive_count={summary['raw_archive_count']}")
    print(f"candidate_collection_count={summary['candidate_collection_count']}")
    print(f"all_archives_consistent={str(summary['all_archives_consistent']).lower()}")
    print(
        "contains_source_scalar_values="
        f"{str(summary['contains_source_scalar_values']).lower()}"
    )
    print(
        "semantic_verification_required="
        f"{str(summary['semantic_verification_required']).lower()}"
    )
    print(f"normalization_allowed={str(summary['normalization_allowed']).lower()}")
    print()
    print("ENDPOINT_STRUCTURES")
    for endpoint in review["endpoints"]:
        print(
            f"kind={endpoint['endpoint_kind']} | route={endpoint['route_template']} | "
            f"status={endpoint['http_status']} | content_type={endpoint['content_type']} | "
            f"top_level_kind={endpoint['top_level_kind']} | "
            f"top_level_keys={','.join(endpoint['top_level_keys'])} | "
            f"payload_hash={endpoint['payload_hash']} | "
            f"schema_fingerprint={endpoint['schema_fingerprint']} | "
            f"bytes_uncompressed={endpoint['bytes_uncompressed']} | "
            f"candidate_collection_count={len(endpoint['candidate_collections'])} | "
            "archive_verified=true"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
