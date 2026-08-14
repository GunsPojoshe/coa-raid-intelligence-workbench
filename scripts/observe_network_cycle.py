from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit

from coa_workbench.collector.har_source_discovery import inventory_network_har
from coa_workbench.collector.raw_archive import RawArchive
from coa_workbench.collector.source_acquisition import observe_reviewed_har
from coa_workbench.collector.source_dimension_index import rebuild_source_dimension_index
from coa_workbench.collector.source_health import build_source_health
from coa_workbench.collector.source_observatory import ReviewedGetContract
from coa_workbench.collector.source_registry import load_source_registry
from coa_workbench.storage.migrations import apply_migrations


def _contract(registry, route):
    return ReviewedGetContract(
        source_code=registry.source_code,
        endpoint_code=route.endpoint_code,
        base_url=registry.base_url,
        route_template=str(route.route_template),
        parameter_keys=route.parameter_keys,
        auth_state=route.auth_mode,
        discovery_source=route.discovery_source,
        review_state=route.review_state,
        logical_name=route.use,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run one Network-first Source Observatory cycle from a browser HAR: "
            "inventory traffic, ingest matching reviewed GET contracts, rebuild approved "
            "derived dimensions, and report health."
        )
    )
    parser.add_argument("har", type=Path)
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("config/ascension_logs_sources.yaml"),
    )
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    parser.add_argument("--database", type=Path, default=Path("data/warehouse/coa.duckdb"))
    parser.add_argument("--migrations", type=Path, default=Path("migrations"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    registry = load_source_registry(args.registry)
    apply_migrations(args.database, args.migrations)
    archive = RawArchive(
        args.raw_root,
        database_path=args.database,
        migrations_dir=args.migrations,
    )

    inventory = inventory_network_har(
        args.har,
        allowed_host=urlsplit(registry.base_url).hostname or "",
        api_prefix="/api/",
    )

    observed_routes: list[dict[str, object]] = []
    for route in registry.routes:
        if not route.observatory_ready:
            continue
        observations = observe_reviewed_har(
            args.har,
            archive=archive,
            database_path=args.database,
            migrations_dir=args.migrations,
            contract=_contract(registry, route),
            dimension_keys=route.dimension_keys,
        )
        if not observations:
            continue
        observed_routes.append(
            {
                "endpoint_code": route.endpoint_code,
                "matching_entry_count": len(observations),
                "observations": [item.public_summary() for item in observations],
            }
        )

    dimension_endpoints = [
        route.endpoint_code
        for route in registry.routes
        if route.observatory_ready and route.dimension_keys
    ]
    dimension_index = rebuild_source_dimension_index(
        args.database,
        args.migrations,
        source_code=registry.source_code,
        endpoint_codes=dimension_endpoints,
    )

    health = build_source_health(args.database)
    result = {
        "cycle_version": "network-source-cycle-v2",
        "capture_mode": "browser_har",
        "network_requests_performed": False,
        "network_inventory": inventory,
        "reviewed_routes_observed": observed_routes,
        "reviewed_route_observation_count": sum(
            int(item["matching_entry_count"]) for item in observed_routes
        ),
        "source_dimension_index": dimension_index,
        "source_health": health,
        "privacy": {
            "har_body_included": False,
            "cookies_included": False,
            "headers_included": False,
            "query_values_included": False,
            "dimension_values_included": False,
        },
    }

    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
