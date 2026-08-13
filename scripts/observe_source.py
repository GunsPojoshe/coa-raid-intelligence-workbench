from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.raw_archive import RawArchive
from coa_workbench.collector.source_observatory import ReviewedGetContract, capture_reviewed_get
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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Capture one reviewed GET source through Source Observatory v1."
    )
    parser.add_argument("endpoint_code")
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("config/ascension_logs_sources.yaml"),
    )
    parser.add_argument("--param", action="append", default=[], metavar="KEY=VALUE")
    parser.add_argument("--path-param", action="append", default=[], metavar="KEY=VALUE")
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    parser.add_argument("--database", type=Path, default=Path("data/warehouse/coa.duckdb"))
    parser.add_argument("--migrations", type=Path, default=Path("migrations"))
    parser.add_argument("--timeout-seconds", type=float, default=20.0)
    parser.add_argument("--max-bytes", type=int, default=32 * 1024 * 1024)
    args = parser.parse_args()

    registry = load_source_registry(args.registry)
    route = registry.route(args.endpoint_code)
    if not route.observatory_ready:
        raise SystemExit(
            f"source route {route.endpoint_code!r} is not Source Observatory capture-ready"
        )

    query_params = _pairs(args.param, "--param")
    path_params = _pairs(args.path_param, "--path-param")
    if not query_params and route.parameter_keys and not route.empty_params_observed:
        raise SystemExit(
            "this reviewed route has no observed empty-parameter branch; provide reviewed --param values"
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
    archive = RawArchive(
        args.raw_root,
        database_path=args.database,
        migrations_dir=args.migrations,
    )
    observation = capture_reviewed_get(
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
    result = {
        "source_code": contract.source_code,
        "endpoint_code": contract.endpoint_code,
        "contract_id": observation.contract_id,
        "source_capture_id": observation.source_capture_id,
        "raw_id": observation.capture.raw_id,
        "raw_observation_id": observation.capture.observation_id,
        "payload_hash": observation.capture.payload_hash,
        "schema_fingerprint": observation.capture.schema_fingerprint,
        "http_status": observation.capture.http_status,
        "bytes_uncompressed": observation.capture.bytes_uncompressed,
        "change_event_count": len(observation.change_event_ids),
        "change_event_ids": list(observation.change_event_ids),
        "reanalysis_request_count": len(observation.reanalysis_request_ids),
        "reanalysis_request_ids": list(observation.reanalysis_request_ids),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
