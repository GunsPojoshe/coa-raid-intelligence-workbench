from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.analytics.cross_report_benchmark import (
    build_cross_report_structural_benchmark,
)
from coa_workbench.analytics.cross_report_review import build_public_cross_report_review


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build the local/private structural cross-report benchmark twice and emit only a "
            "public-safe scalar review. No network requests are performed."
        )
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("data/warehouse/coa.duckdb"),
    )
    parser.add_argument("--migrations", type=Path, default=Path("migrations"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    first = build_cross_report_structural_benchmark(args.database, args.migrations)
    second = build_cross_report_structural_benchmark(args.database, args.migrations)
    result = build_public_cross_report_review(
        first,
        deterministic_requery_equal=first == second,
    )
    result["network_requests_performed"] = False

    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
