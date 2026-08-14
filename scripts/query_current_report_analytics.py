from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.analytics.current_report_read_model import (
    build_current_report_comparison_read_model,
    list_current_report_comparison_reports,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Query persisted current-report analytics as local private comparison read models. "
            "No network requests are performed and planner scoring remains disabled."
        )
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("data/warehouse/coa.duckdb"),
    )
    parser.add_argument("--migrations", type=Path, default=Path("migrations"))
    parser.add_argument("--report-id")
    parser.add_argument("--list", action="store_true", dest="list_reports")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.list_reports:
        result = list_current_report_comparison_reports(args.database, args.migrations)
    else:
        result = build_current_report_comparison_read_model(
            args.database,
            args.migrations,
            report_id=args.report_id,
        )

    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
