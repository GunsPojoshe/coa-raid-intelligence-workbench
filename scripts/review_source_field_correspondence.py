from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.source_field_correspondence import (
    DEFAULT_FOCUS_TOKENS,
    DEFAULT_SERVER_ENDPOINT_CODES,
    build_source_field_correspondence_review,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Compare public upstream Lua field lineage with persisted scalar-free server schema paths. "
            "The review produces structural correspondence candidates only and performs no network requests."
        )
    )
    parser.add_argument(
        "upstream_lineage",
        type=Path,
        help="Scalar-safe upstream Lua lineage JSON",
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
        "--endpoint-code",
        action="append",
        dest="endpoint_codes",
        help="Server endpoint code to inspect; repeatable",
    )
    parser.add_argument(
        "--focus-token",
        action="append",
        dest="focus_tokens",
        help="Public-safe field token used to narrow the structural review; repeatable",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = build_source_field_correspondence_review(
        args.database,
        args.migrations,
        args.upstream_lineage,
        endpoint_codes=args.endpoint_codes or DEFAULT_SERVER_ENDPOINT_CODES,
        focus_tokens=args.focus_tokens or DEFAULT_FOCUS_TOKENS,
    )
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
