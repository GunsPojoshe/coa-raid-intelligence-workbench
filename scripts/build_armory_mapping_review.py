from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.armory_mapping_review import build_armory_mapping_review


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a type-only Armory mapping review packet from archived payloads."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="Progressive Armory endpoint capture manifest.",
    )
    parser.add_argument(
        "--raw-root",
        type=Path,
        default=Path("data/raw"),
        help="Immutable raw archive root.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Safe mapping review JSON output path.",
    )
    parser.add_argument(
        "--max-nodes",
        type=int,
        default=100_000,
        help="Maximum JSON node occurrences inspected per endpoint.",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    result = build_armory_mapping_review(
        args.manifest,
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
