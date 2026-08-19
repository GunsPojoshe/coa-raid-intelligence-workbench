from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.upstream_lua_evidence import (
    review_lua_source_tree,
    write_upstream_lua_review,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build a scalar-safe structural evidence inventory from a local pinned Lua source tree. "
            "The command performs no network requests and does not infer gameplay semantics."
        )
    )
    parser.add_argument(
        "source_root", type=Path, help="Local root of the pinned upstream source tree"
    )
    parser.add_argument("--source-code", required=True, help="Public-safe source code")
    parser.add_argument("--revision", required=True, help="Pinned hexadecimal upstream revision")
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    review = review_lua_source_tree(
        args.source_root,
        source_code=args.source_code,
        revision=args.revision,
    )
    if args.output:
        write_upstream_lua_review(args.output, review)
        print(args.output)
    else:
        print(json.dumps(review, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
