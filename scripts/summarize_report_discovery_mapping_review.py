from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.report_discovery_mapping_summary import (
    summarize_report_discovery_mapping_review,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize report mapping and structural reviews without source scalar values "
            "or optional-property assumptions."
        )
    )
    parser.add_argument(
        "--mapping-review",
        type=Path,
        default=Path("data/exchange/out/report-discovery-mapping-review.json"),
    )
    parser.add_argument(
        "--structural-review",
        type=Path,
        default=Path("data/exchange/out/report-discovery-structural-review.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/report-discovery-mapping-summary.json"),
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    result = summarize_report_discovery_mapping_review(
        args.mapping_review,
        args.structural_review,
    )
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(args.output)
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
