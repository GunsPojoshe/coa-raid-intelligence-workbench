from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from coa_workbench.collector.discovery_scenarios import (
    build_discovery_scenario_coverage,
    load_discovery_scenario_manifest,
)


def _load_receipts(directory: Path) -> tuple[dict[str, Any], ...]:
    if not directory.exists():
        return ()
    if not directory.is_dir():
        raise ValueError("receipts directory must be a directory")
    receipts: list[dict[str, Any]] = []
    for path in sorted(directory.glob("coa-browser-observatory-*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"browser receipt must contain an object: {path.name}")
        receipts.append(payload)
    return tuple(receipts)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build public-safe Browser Observatory scenario coverage. Coverage states are "
            "evidence states and are not semantic proof or a completion percentage."
        )
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("config/browser_discovery_scenarios.yaml"),
    )
    parser.add_argument(
        "--receipts-dir",
        type=Path,
        default=Path("data/exchange/out"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/coa-browser-discovery-coverage.json"),
    )
    args = parser.parse_args()

    manifest = load_discovery_scenario_manifest(args.manifest)
    receipts = _load_receipts(args.receipts_dir)
    result = build_discovery_scenario_coverage(manifest, receipts)
    result["receipt_count"] = len(receipts)
    result["receipt_paths_included"] = False

    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
