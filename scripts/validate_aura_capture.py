from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.normalizer import AuraTimelineContract, validate_archived_aura_capture


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate one single-encounter aura timeline against archived source intervals."
    )
    parser.add_argument("--timeline", required=True, help="Archived timeline payload hash or path")
    parser.add_argument(
        "--reference",
        required=True,
        help="Archived debuff_sources payload hash or path",
    )
    parser.add_argument("--encounter-id", required=True, help="Source encounter ID")
    parser.add_argument(
        "--mapping",
        type=Path,
        default=Path("config/mappings/coa_aura_timeline_single_encounter_v1.json"),
    )
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    contract = AuraTimelineContract.from_path(args.mapping)
    result = validate_archived_aura_capture(
        args.timeline,
        args.reference,
        raw_root=args.raw_root,
        source_encounter_id=args.encounter_id,
        contract=contract,
    )
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["status"] == "matched" else 2


if __name__ == "__main__":
    raise SystemExit(main())
