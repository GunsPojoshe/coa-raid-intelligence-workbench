from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit

from coa_workbench.collector import RawArchive, inventory_har, load_source_registry

_ARMORY_ROUTES = (
    "/api/armory/",
    "/api/characters/search",
)


def _is_armory_route(path: str | None) -> bool:
    if not path:
        return False
    return path.startswith(_ARMORY_ROUTES[0]) or path == _ARMORY_ROUTES[1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Import browser-captured Armory API responses from a local HAR into the "
            "immutable raw archive without persisting headers, cookies, or query values."
        )
    )
    parser.add_argument("--har", type=Path, required=True)
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("config/ascension_logs_sources.yaml"),
    )
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("data/warehouse/coa.duckdb"),
    )
    parser.add_argument("--migrations", type=Path, default=Path("migrations"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    registry = load_source_registry(args.registry)
    allowed_host = urlsplit(registry.base_url).hostname
    if not allowed_host:
        raise ValueError("source registry base URL has no hostname")

    archive = RawArchive(
        args.raw_root,
        database_path=args.database,
        migrations_dir=args.migrations,
    )
    inventory = inventory_har(
        args.har,
        archive=archive,
        source_code=registry.source_code,
        allowed_host=allowed_host,
    )

    selected = [
        entry for entry in inventory["entries"] if _is_armory_route(entry.get("route_path"))
    ]
    successful_json = [
        entry
        for entry in selected
        if entry.get("http_status") is not None
        and 200 <= int(entry["http_status"]) < 300
        and entry.get("candidate_label") in {"json_object", "json_array"}
        and entry.get("raw_id")
    ]
    routes = sorted({str(entry["route_path"]) for entry in selected if entry.get("route_path")})
    fingerprints = sorted(
        {
            str(entry["schema_fingerprint"])
            for entry in successful_json
            if entry.get("schema_fingerprint")
        }
    )
    payload = {
        "schema_version": 1,
        "source_code": registry.source_code,
        "har_file_name": args.har.name,
        "matched_entries": len(selected),
        "successful_json_entries": len(successful_json),
        "routes": routes,
        "schema_fingerprints": fingerprints,
        "entries": selected,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if successful_json else 4


if __name__ == "__main__":
    raise SystemExit(main())
