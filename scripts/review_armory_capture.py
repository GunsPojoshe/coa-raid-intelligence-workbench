from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.armory_structural_review import review_armory_capture_manifest


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify and structurally inspect endpoint-isolated Armory payloads."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/exchange/out/armory-endpoint-capture.json"),
    )
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/armory-structural-review.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    result = review_armory_capture_manifest(args.manifest, raw_root=args.raw_root)
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
