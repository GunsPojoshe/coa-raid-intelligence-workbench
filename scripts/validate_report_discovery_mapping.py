from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

from coa_workbench.collector.report_discovery_review import review_report_discovery_capture
from coa_workbench.normalizer.report_discovery_mapping import (
    ReportDiscoveryMappingContract,
)
from coa_workbench.normalizer.schema_inspector import structure_fingerprint


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate one candidate public-report mapping against its scalar-free summary "
            "and exact immutable raw archive."
        )
    )
    parser.add_argument(
        "--mapping",
        type=Path,
        default=Path("config/mappings/coa_public_report_discovery_v1.json"),
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=Path("data/exchange/out/report-discovery-mapping-summary.json"),
    )
    parser.add_argument(
        "--capture",
        type=Path,
        default=Path("data/exchange/out/report-discovery-page.json"),
    )
    parser.add_argument(
        "--raw-root",
        type=Path,
        default=Path("data/raw"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/report-discovery-mapping-validation.json"),
    )
    return parser.parse_args()


def _load_object(path: Path, description: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{description} must contain a JSON object")
    return payload


def _load_archived_payload(
    structural: dict[str, Any],
    *,
    raw_root: Path,
) -> tuple[Any, str, str]:
    root = raw_root.resolve()
    response = structural["response"]
    archive_path = (root / str(response["payload_path"])).resolve()
    if (
        not archive_path.is_relative_to(root)
        or not archive_path.is_file()
        or not archive_path.name.endswith(".json.gz")
    ):
        raise ValueError("report discovery payload must be a gzip JSON archive below raw-root")
    body = gzip.decompress(archive_path.read_bytes())
    payload_hash = hashlib.sha256(body).hexdigest()
    payload = json.loads(body)
    fingerprint = structure_fingerprint(payload)
    return payload, payload_hash, fingerprint


def main() -> int:
    args = _arguments()
    contract = ReportDiscoveryMappingContract.from_path(args.mapping)
    summary = _load_object(args.summary, "report discovery mapping summary")
    summary_result = contract.validate_against_summary(summary)

    structural = review_report_discovery_capture(args.capture, raw_root=args.raw_root)
    payload, payload_hash, fingerprint = _load_archived_payload(
        structural,
        raw_root=args.raw_root,
    )
    archive_result = contract.validate_against_payload(
        payload,
        payload_hash=payload_hash,
        schema_fingerprint=fingerprint,
        route=structural["request"]["route_template"],
    )

    output = {
        "schema_version": 1,
        "validation_kind": "report_discovery_mapping_validation",
        "mapping_file": args.mapping.as_posix(),
        "summary_file": args.summary.name,
        "capture_file": args.capture.name,
        "mapping_id": contract.mapping_id,
        "status": contract.status,
        "all_structurally_consistent": True,
        "all_raw_archive_selectors_consistent": True,
        "production_ready": contract.production_ready,
        "can_promote": False,
        "contains_source_scalar_values": False,
        "summary_validation": summary_result,
        "raw_archive_validation": archive_result,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(args.output)
    print(
        json.dumps(
            {
                "output": args.output.as_posix(),
                "mapping_id": contract.mapping_id,
                "status": contract.status,
                "report_item_count": archive_result["report_item_count"],
                "field_contract_count": archive_result["field_contract_count"],
                "extracted_value_count": archive_result["extracted_value_count"],
                "all_structurally_consistent": True,
                "all_raw_archive_selectors_consistent": True,
                "production_ready": contract.production_ready,
                "can_promote": False,
                "contains_source_scalar_values": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
