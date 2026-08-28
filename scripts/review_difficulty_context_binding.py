from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.analytics.difficulty_context_binding import (
    build_difficulty_context_binding_review,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Review pull-scoped private difficulty context bindings across persisted current reports. "
            "The command performs no network requests and emits only scalar-safe counts and booleans."
        )
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("data/warehouse/coa.duckdb"),
    )
    parser.add_argument(
        "--raw-root",
        type=Path,
        default=Path("data/raw"),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = build_difficulty_context_binding_review(args.database, args.raw_root)
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
