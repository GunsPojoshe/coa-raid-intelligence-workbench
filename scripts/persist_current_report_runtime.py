from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.compatible_normalization import (
    normalize_verified_compatible_payload,
)
from coa_workbench.collector.current_combatants_roster import (
    parse_current_combatants_roster,
)
from coa_workbench.collector.current_report_har import extract_current_report_har_slice
from coa_workbench.storage.current_report_observations import (
    persist_current_report_derived_observations,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Persist one already-observed current CoA report HAR as deterministic derived "
            "report/encounter/roster/build observations. No network requests are performed and "
            "canonical core entities are not mutated."
        )
    )
    parser.add_argument("har", type=Path)
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("data/warehouse/coa.duckdb"),
    )
    parser.add_argument("--migrations", type=Path, default=Path("migrations"))
    parser.add_argument(
        "--mapping",
        type=Path,
        default=Path("config/mappings/coa_report_detail_v1.json"),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    har_slice = extract_current_report_har_slice(args.har)
    mapping_payload = json.loads(args.mapping.read_text(encoding="utf-8"))
    normalization = normalize_verified_compatible_payload(
        har_slice.report_detail.payload,
        mapping_payload,
    )
    roster = parse_current_combatants_roster(har_slice.combatants_roster.payload)
    result = persist_current_report_derived_observations(
        database_path=args.database,
        migrations_path=args.migrations,
        har_slice=har_slice,
        normalization=normalization,
        roster=roster,
    )
    result["har_slice"] = har_slice.public_summary()
    result["network_requests_performed"] = False
    result["privacy"] = {
        "har_included": False,
        "raw_response_bodies_included": False,
        "report_ids_included": False,
        "encounter_ids_included": False,
        "character_ids_included": False,
        "character_names_included": False,
        "query_values_included": False,
        "source_capture_ids_included": False,
    }

    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
