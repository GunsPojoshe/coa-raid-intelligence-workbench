from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.normalizer.armory_mapping import ArmoryMappingContract


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate candidate Armory mapping contracts against a safe review packet."
    )
    parser.add_argument(
        "--review",
        type=Path,
        default=Path("data/exchange/out/armory-mapping-review-v2.json"),
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


def main() -> int:
    args = _arguments()
    mapping_paths = args.mappings or [
        Path("config/mappings/coa_armory_character_v1.json"),
        Path("config/mappings/coa_armory_talent_grid_v1.json"),
    ]
    packet = json.loads(args.review.read_text(encoding="utf-8"))
    if not isinstance(packet, dict):
        raise ValueError("Armory mapping review packet must contain a JSON object")

    results = []
    for mapping_path in mapping_paths:
        contract = ArmoryMappingContract.from_path(mapping_path)
        result = contract.validate_against_review_packet(packet)
        result["mapping_file"] = mapping_path.as_posix()
        results.append(result)

    output = {
        "schema_version": 1,
        "validation_kind": "armory_mapping_validation",
        "review_file": args.review.name,
        "mapping_count": len(results),
        "all_structurally_consistent": True,
        "all_production_ready": all(item["production_ready"] for item in results),
        "mappings": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(args.output)
    print(
        json.dumps(
            {
                "output": args.output.as_posix(),
                "mapping_count": len(results),
                "all_structurally_consistent": True,
                "all_production_ready": output["all_production_ready"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
