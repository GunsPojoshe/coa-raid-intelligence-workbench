from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.har_source_discovery import inventory_network_har


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inventory same-origin API traffic from a browser HAR "
            "without retaining scalar values."
        )
    )
    parser.add_argument("path", type=Path)
    parser.add_argument("--host", default="coa.ascensionlogs.gg")
    parser.add_argument("--api-prefix", default="/api/")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = inventory_network_har(
        args.path,
        allowed_host=args.host,
        api_prefix=args.api_prefix,
    )
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
