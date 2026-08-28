from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.analytics.cross_report_source_structure import (
    build_cross_report_source_structure_review,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect scalar-free source structure for persisted cross-report reports after an "
            "insufficient equivalence review. No network requests are performed."
        )
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("data/warehouse/coa.duckdb"),
    )
    parser.add_argument(
        "--migrations",
        type=Path,
        default=Path("migrations"),
    )
    parser.add_argument(
        "--raw-root",
        type=Path,
        default=Path("data/raw"),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = build_cross_report_source_structure_review(
        args.database,
        args.migrations,
        args.raw_root,
    )
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
