from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.raw_archive import RawArchive
from coa_workbench.collector.source_acquisition import (
    capture_reviewed_get_observation,
    observe_reviewed_har,
)
from coa_workbench.collector.source_observatory import ReviewedGetContract
from coa_workbench.collector.source_registry import load_source_registry


def _pairs(values: list[str], label: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"{label} must use KEY=VALUE: {value!r}")
        key, item = value.split("=", 1)
        if not key or key in result:
            raise ValueError(f"{label} contains an empty or duplicate key: {key!r}")
        result[key] = item
    return result


def _contract(registry_path: Path, endpoint_code: str):
    registry = load_source_registry(registry_path)
    route = registry.route(endpoint_code)
    if not route.observatory_ready:
        raise SystemExit(
            f"source route {route.endpoint_code!r} is not Source Observatory capture-ready"
        )
    contract = ReviewedGetContract(
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
    return route, contract


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Observe one reviewed GET source directly or from a browser HAR."
    )
    parser.add_argument("endpoint_code")
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("config/ascension_logs_sources.yaml"),
    )
    parser.add_argument("--param", action="append", default=[], metavar="KEY=VALUE")
    parser.add_argument("--path-param", action="append", default=[], metavar="KEY=VALUE")
    parser.add_argument("--har", type=Path)
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    parser.add_argument("--database", type=Path, default=Path("data/warehouse/coa.duckdb"))
    parser.add_argument("--migrations", type=Path, default=Path("migrations"))
    parser.add_argument("--timeout-seconds", type=float, default=20.0)
    parser.add_argument("--max-bytes", type=int, default=32 * 1024 * 1024)
    args = parser.parse_args()

    route, contract = _contract(args.registry, args.endpoint_code)
    archive = RawArchive(
        args.raw_root,
        database_path=args.database,
        migrations_dir=args.migrations,
    )

    if args.har is not None:
        if args.param or args.path_param:
            raise SystemExit("--har cannot be combined with --param or --path-param")
        observations = observe_reviewed_har(
            args.har,
            archive=archive,
            database_path=args.database,
            migrations_dir=args.migrations,
            contract=contract,
            dimension_keys=route.dimension_keys,
        )
        result = {
            "source_code": contract.source_code,
            "endpoint_code": contract.endpoint_code,
            "capture_mode": "browser_har",
            "matching_entry_count": len(observations),
            "observations": [item.public_summary() for item in observations],
        }
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if observations else 5

    query_params = _pairs(args.param, "--param")
    path_params = _pairs(args.path_param, "--path-param")
    if not query_params and route.parameter_keys and not route.empty_params_observed:
        raise SystemExit(
            "this reviewed route has no observed empty-parameter branch; "
            "provide reviewed --param values"
        )

    observation = capture_reviewed_get_observation(
        archive=archive,
        database_path=args.database,
        migrations_dir=args.migrations,
        contract=contract,
        path_params=path_params,
        query_params=query_params,
        dimension_keys=route.dimension_keys,
        timeout_seconds=args.timeout_seconds,
        max_bytes=args.max_bytes,
    )
    print(json.dumps(observation.public_summary(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
