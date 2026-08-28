from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.source_health import build_source_health
from coa_workbench.storage.migrations import apply_migrations


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Show Source Observatory endpoint/change/reanalysis health."
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
    parser.add_argument("--recent-change-limit", type=int, default=25)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    apply_migrations(args.database, args.migrations)
    result = build_source_health(
        args.database,
        recent_change_limit=args.recent_change_limit,
    )
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
