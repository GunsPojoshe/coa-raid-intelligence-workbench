from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector import RawArchive, load_source_registry
from coa_workbench.collector.report_slice_capture import (
    ObservedReportSliceCaptureResult,
    capture_observed_report_slice,
    observed_report_slice_capture_to_dict,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Capture report detail, encounter detail, and combatants-info only after their "
            "route shapes were verified in an archived SPA route inventory."
        )
    )
    parser.add_argument("--report-id", required=True, type=int)
    parser.add_argument("--encounter-id", required=True, type=int)
    parser.add_argument(
        "--route-inventory",
        type=Path,
        default=Path("data/exchange/out/spa-api-route-inventory.json"),
    )
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
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    parser.add_argument("--retry-count", type=int, default=1)
    parser.add_argument("--max-json-bytes", type=int, default=32 * 1024 * 1024)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/observed-report-slice-capture.json"),
    )
    return parser.parse_args()


def _write_result(path: Path, result: ObservedReportSliceCaptureResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(observed_report_slice_capture_to_dict(result), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def main() -> int:
    args = _arguments()
    registry = load_source_registry(args.registry)
    archive = RawArchive(
        args.raw_root,
        database_path=args.database,
        migrations_dir=args.migrations,
    )
    result = capture_observed_report_slice(
        registry,
        archive,
        route_inventory_path=args.route_inventory,
        report_id=args.report_id,
        encounter_id=args.encounter_id,
        timeout_seconds=args.timeout_seconds,
        retry_count=args.retry_count,
        max_json_bytes=args.max_json_bytes,
        on_progress=lambda partial: _write_result(args.output, partial),
    )
    _write_result(args.output, result)
    rendered = observed_report_slice_capture_to_dict(result)

    print("OBSERVED_REPORT_SLICE_CAPTURE")
    print(f"schema_version={rendered['schema_version']}")
    print(f"capture_kind={rendered['capture_kind']}")
    print(
        "route_inventory_verified="
        f"{str(rendered['provenance']['route_inventory_verified']).lower()}"
    )
    print(f"route_inventory_hash={rendered['provenance']['route_inventory_hash']}")
    print(f"http_profile_version={rendered['provenance']['http_profile_version']}")
    print(
        "expected_endpoint_count="
        f"{rendered['summary']['expected_endpoint_count']}"
    )
    print(
        "attempted_endpoint_count="
        f"{rendered['summary']['attempted_endpoint_count']}"
    )
    print(
        "complete_endpoint_count="
        f"{rendered['summary']['complete_endpoint_count']}"
    )
    print(f"all_complete={str(rendered['summary']['all_complete']).lower()}")
    print(
        "contains_source_scalar_values="
        f"{str(rendered['summary']['contains_source_scalar_values']).lower()}"
    )
    print(
        "semantic_verification_required="
        f"{str(rendered['summary']['semantic_verification_required']).lower()}"
    )
    print(
        "normalization_allowed="
        f"{str(rendered['summary']['normalization_allowed']).lower()}"
    )
    print()
    print("ENDPOINTS")
    for endpoint in rendered["endpoints"]:
        capture = endpoint["capture"] or {}
        print(
            f"kind={endpoint['endpoint_kind']} | route={endpoint['route_template']} | "
            f"status={endpoint['status']} | content_type={endpoint['content_type']} | "
            f"top_level_kind={endpoint['top_level_kind']} | "
            f"top_level_keys={','.join(endpoint['top_level_keys'])} | "
            f"payload_hash={capture.get('payload_hash')} | "
            f"schema_fingerprint={capture.get('schema_fingerprint')} | "
            f"bytes_uncompressed={capture.get('bytes_uncompressed')} | "
            f"complete={str(endpoint['complete']).lower()} | error={endpoint['error']}"
        )
    return 0 if result.all_complete else 4


if __name__ == "__main__":
    raise SystemExit(main())
