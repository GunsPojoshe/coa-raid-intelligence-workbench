from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.report_discovery_review import review_report_discovery_capture


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Verify one bounded report-discovery archive and write a scalar-free structural review."
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
        default=Path("data/exchange/out/report-discovery-structural-review.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    result = review_report_discovery_capture(args.capture, raw_root=args.raw_root)
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(args.output)
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
