from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.public_api_catalog import (
    build_public_api_catalog_review,
    load_latest_public_api_payload,
)
from coa_workbench.collector.source_registry import load_source_registry


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Review the latest archived official /phases and /bosses payloads. "
            "The receipt contains only counts and booleans."
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
        default=Path("data/exchange/out/coa-public-api-catalog-review.json"),
    )
    args = parser.parse_args()

    registry = load_source_registry(args.registry)
    phases = load_latest_public_api_payload(
        args.raw_root,
        source_code=registry.source_code,
        endpoint_code="public_api_phases",
    )
    bosses = load_latest_public_api_payload(
        args.raw_root,
        source_code=registry.source_code,
        endpoint_code="public_api_bosses",
    )
    result = build_public_api_catalog_review(phases, bosses)
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["selection"]["current_phase_selectable"] else 4


if __name__ == "__main__":
    raise SystemExit(main())
