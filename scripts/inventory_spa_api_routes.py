from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.spa_route_inventory import build_spa_route_inventory


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Verify already archived SPA assets and emit privacy-safe API route shapes. "
            "No network requests are performed."
        )
    )
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    parser.add_argument("--endpoint-code", default="build_page_asset")
    parser.add_argument("--max-archives", type=int, default=64)
    parser.add_argument("--max-uncompressed-bytes", type=int, default=16 * 1024 * 1024)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/spa-api-route-inventory.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    inventory = build_spa_route_inventory(
        args.raw_root,
        endpoint_code=args.endpoint_code,
        max_archives=args.max_archives,
        max_uncompressed_bytes=args.max_uncompressed_bytes,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(
        json.dumps(inventory, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(args.output)

    relevant = [row for row in inventory["routes"] if row["lexical_hints"]]
    print("SPA_ROUTE_INVENTORY")
    print(f"schema_version={inventory['schema_version']}")
    print(f"inventory_kind={inventory['inventory_kind']}")
    print(f"archive_count={inventory['summary']['archive_count']}")
    print(f"route_candidate_count={inventory['summary']['route_candidate_count']}")
    print(
        "lexically_relevant_candidate_count="
        f"{inventory['summary']['lexically_relevant_candidate_count']}"
    )
    print(f"all_archives_verified={str(inventory['summary']['all_archives_verified']).lower()}")
    print(
        "contains_source_record_scalar_values="
        f"{str(inventory['summary']['contains_source_record_scalar_values']).lower()}"
    )
    print(
        "semantic_verification_required="
        f"{str(inventory['summary']['semantic_verification_required']).lower()}"
    )
    print(
        "network_requests_performed="
        f"{str(inventory['summary']['network_requests_performed']).lower()}"
    )
    print()
    print("LEXICALLY_RELEVANT_ROUTES")
    if not relevant:
        print("none")
    for row in relevant:
        print(
            f"route={row['route_shape']} | hints={','.join(row['lexical_hints'])} | "
            f"archive_count={row['archive_count']} | semantic_status={row['semantic_status']}"
        )
    print()
    print("ALL_ROUTE_SHAPES")
    for row in inventory["routes"]:
        print(
            f"route={row['route_shape']} | archive_count={row['archive_count']} | "
            f"semantic_status={row['semantic_status']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
