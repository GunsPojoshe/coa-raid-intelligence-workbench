from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.public_api_catalog import load_latest_public_api_payload
from coa_workbench.collector.public_api_statistics_review import (
    build_public_api_statistics_shape_review,
)
from coa_workbench.collector.source_registry import load_source_registry


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Review the latest archived official /statistics payload using scalar-safe structural "
            "counts only. Dynamic class/spec keys and metric values are never emitted."
        )
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("config/coa_public_api_sources.yaml"),
    )
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/coa-public-api-statistics-shape-review.json"),
    )
    args = parser.parse_args()

    registry = load_source_registry(args.registry)
    payload = load_latest_public_api_payload(
        args.raw_root,
        source_code=registry.source_code,
        endpoint_code="public_api_statistics",
    )
    review = build_public_api_statistics_shape_review(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(review, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(review, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
