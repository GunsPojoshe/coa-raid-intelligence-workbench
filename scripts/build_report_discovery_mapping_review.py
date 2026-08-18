from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.report_discovery_mapping_review import (
    build_report_discovery_mapping_review,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build a full-root type-only mapping review packet for one exact bounded "
            "report-discovery archive."
        )
    )
    parser.add_argument(
        "--capture",
        type=Path,
        default=Path("data/exchange/out/report-discovery-page.json"),
    )
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/report-discovery-mapping-review.json"),
    )
    parser.add_argument("--max-nodes", type=int, default=100_000)
    return parser


def main() -> int:
    args = _parser().parse_args()
    result = build_report_discovery_mapping_review(
        args.capture,
        raw_root=args.raw_root,
        max_nodes=args.max_nodes,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
