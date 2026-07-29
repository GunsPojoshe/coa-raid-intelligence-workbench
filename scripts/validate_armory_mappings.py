from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

from coa_workbench.collector.armory_structural_review import review_armory_capture_manifest
from coa_workbench.normalizer.armory_mapping import ArmoryMappingContract
from coa_workbench.normalizer.schema_inspector import structure_fingerprint


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate candidate Armory mapping contracts against a safe review packet "
            "and the exact immutable raw archives."
        ),
    )
    parser.add_argument(
        "--review",
        type=Path,
        default=Path("data/exchange/out/armory-mapping-review-v2.json"),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/exchange/out/armory-endpoint-capture.json"),
    )
    parser.add_argument(
        "--raw-root",
        type=Path,
        default=Path("data/raw"),
    )
    parser.add_argument(
        "--mapping",
        type=Path,
        action="append",
        dest="mappings",
        default=None,
        help="Mapping JSON path. Repeat for multiple mappings.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/armory-mapping-validation.json"),
    )
    return parser.parse_args()


def _load_object(path: Path, description: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{description} must contain a JSON object")
    return payload


def _load_archived_payload(
    endpoint: dict[str, Any],
    *,
    raw_root: Path,
) -> tuple[Any, str, str]:
    root = raw_root.resolve()
    path = (root / str(endpoint["payload_path"])).resolve()
    if (
        not path.is_relative_to(root)
        or not path.is_file()
        or not path.name.endswith(".json.gz")
    ):
        raise ValueError("Armory payload must be a gzip JSON archive below raw-root")
    body = gzip.decompress(path.read_bytes())
    payload_hash = hashlib.sha256(body).hexdigest()
    payload = json.loads(body)
    fingerprint = structure_fingerprint(payload)
    return payload, payload_hash, fingerprint


def main() -> int:
    args = _arguments()
    mapping_paths = args.mappings or [
        Path("config/mappings/coa_armory_character_v1.json"),
        Path("config/mappings/coa_armory_talent_grid_v1.json"),
    ]
    packet = _load_object(args.review, "Armory mapping review packet")
    structural = review_armory_capture_manifest(args.manifest, raw_root=args.raw_root)
    endpoints = {
        str(endpoint["endpoint_kind"]): endpoint
        for endpoint in structural["endpoints"]
    }

    results = []
    for mapping_path in mapping_paths:
        contract = ArmoryMappingContract.from_path(mapping_path)
        review_result = contract.validate_against_review_packet(packet)
        endpoint = endpoints.get(contract.endpoint_kind)
        if endpoint is None:
            raise ValueError(
                f"Armory capture manifest has no endpoint {contract.endpoint_kind!r}"
            )
        payload, payload_hash, fingerprint = _load_archived_payload(
            endpoint,
            raw_root=args.raw_root,
        )
        archive_result = contract.validate_against_payload(
            payload,
            payload_hash=payload_hash,
            schema_fingerprint=fingerprint,
            route=endpoint.get("route"),
        )
        review_result["mapping_file"] = mapping_path.as_posix()
        review_result["raw_archive_validation"] = archive_result
        results.append(review_result)

    output = {
        "schema_version": 2,
        "validation_kind": "armory_mapping_validation",
        "review_file": args.review.name,
        "manifest_file": args.manifest.name,
        "mapping_count": len(results),
        "raw_archive_count": len(results),
        "all_structurally_consistent": True,
        "all_raw_archives_consistent": True,
        "all_production_ready": all(item["production_ready"] for item in results),
        "mappings": results,
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
                "mapping_count": len(results),
                "all_structurally_consistent": True,
                "all_raw_archives_consistent": True,
                "all_production_ready": output["all_production_ready"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
