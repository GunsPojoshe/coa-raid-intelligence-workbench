from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit

from coa_workbench.collector.har_route_resolution import (
    generic_har_ingest_ready,
    route_requires_explicit_dynamic_resolution,
)
from coa_workbench.collector.har_source_discovery import (
    inventory_network_har,
    select_latest_relevant_har,
)
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
            "inventory traffic, ingest matching reviewed static GET contracts, rebuild approved "
            "derived dimensions, and report health. Dynamic path templates are inventoried but "
            "deferred to explicit route resolution. If HAR is omitted, use the newest relevant "
            ".har from --har-dir."
        )
    )
    parser.add_argument("har", nargs="?", type=Path)
    parser.add_argument(
        "--har-dir",
        type=Path,
        default=Path.home() / "Downloads",
        help=(
            "Directory searched for the newest relevant .har when the positional HAR path "
            "is omitted. Default: ~/Downloads"
        ),
    )
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
    allowed_host = urlsplit(registry.base_url).hostname or ""
    selection_mode = "explicit"
    if args.har is not None:
        har_path = args.har
        if not har_path.is_file():
            parser.error(f"HAR file does not exist: {har_path}")
    else:
        selection_mode = "latest_relevant_in_directory"
        try:
            har_path = select_latest_relevant_har(
                args.har_dir,
                allowed_host=allowed_host,
                api_prefix="/api/",
            )
        except FileNotFoundError as exc:
            parser.error(str(exc))

    apply_migrations(args.database, args.migrations)
    archive = RawArchive(
        args.raw_root,
        database_path=args.database,
        migrations_dir=args.migrations,
    )

    inventory = inventory_network_har(
        har_path,
        allowed_host=allowed_host,
        api_prefix="/api/",
    )

    deferred_dynamic_routes = sorted(
        route.endpoint_code
        for route in registry.routes
        if route.observatory_ready
        and route_requires_explicit_dynamic_resolution(route.route_template)
    )

    observed_routes: list[dict[str, object]] = []
    for route in registry.routes:
        if not route.observatory_ready or not generic_har_ingest_ready(route.route_template):
            continue
        observations = observe_reviewed_har(
            har_path,
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
        if route.observatory_ready
        and route.dimension_keys
        and generic_har_ingest_ready(route.route_template)
    ]
    dimension_index = rebuild_source_dimension_index(
        args.database,
        args.migrations,
        source_code=registry.source_code,
        endpoint_codes=dimension_endpoints,
    )

    health = build_source_health(args.database)
    result = {
        "cycle_version": "network-source-cycle-v4",
        "capture_mode": "browser_har",
        "network_requests_performed": False,
        "har_selection": {
            "mode": selection_mode,
            "selected_path_included": False,
        },
        "network_inventory": inventory,
        "reviewed_routes_observed": observed_routes,
        "reviewed_route_observation_count": sum(
            int(item["matching_entry_count"]) for item in observed_routes
        ),
        "dynamic_route_resolution": {
            "generic_dynamic_ingestion_allowed": False,
            "deferred_endpoint_codes": deferred_dynamic_routes,
            "deferred_route_count": len(deferred_dynamic_routes),
        },
        "source_dimension_index": dimension_index,
        "source_health": health,
        "privacy": {
            "har_body_included": False,
            "har_path_included": False,
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
