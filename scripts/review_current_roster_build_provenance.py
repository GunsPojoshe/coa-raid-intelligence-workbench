from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.analytics.current_roster_build_provenance import (
    review_current_roster_build_provenance,
)
from coa_workbench.analytics.public_api_encounter_context import parse_encounter_reference_url


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Review report-scoped player identity and observed build provenance from already "
            "persisted current-report roster observations. This command performs no network I/O."
        )
    )
    parser.add_argument("--reference-url", required=True)
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("data/warehouse/coa.duckdb"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/coa-current-roster-build-provenance-review.json"),
    )
    args = parser.parse_args()

    reference = parse_encounter_reference_url(args.reference_url)
    try:
        review = review_current_roster_build_provenance(
            args.database,
            reference=reference,
        )
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        raise SystemExit(f"current roster build provenance review failed: {exc}") from exc

    summary = review.public_summary()
    receipt = {
        "schema_version": 1,
        "review_kind": "current_roster_build_provenance",
        "source": {
            "existing_current_report_persistence_reused": True,
            "canonical_entity_observation_reused": True,
            "network_request_count": 0,
            "browser_har_used_this_run": False,
            "events_read_used": False,
        },
        "review": summary,
        "verification": {
            "report_scoped_player_identity_complete": summary[
                "report_scoped_player_identity_complete"
            ],
            "observed_build_linkage_complete": summary["observed_build_linkage_complete"],
            "source_provenance_complete": summary["source_provenance_complete"],
            "observed_build_provenance_complete": summary["observed_build_provenance_complete"],
            "observed_timestamp_coverage_complete": summary["observed_timestamp_coverage_complete"],
            "current_build_freshness_verified": False,
            "latest_snapshot_semantics_verified": False,
            "cross_report_identity_verified": False,
            "mechanic_semantics_verified": False,
            "planner_scoring_allowed": False,
        },
        "privacy": {
            "report_ids_included": False,
            "encounter_ids_included": False,
            "player_ids_included": False,
            "player_names_included": False,
            "player_guids_included": False,
            "realm_values_included": False,
            "build_values_included": False,
            "talent_values_included": False,
            "gear_values_included": False,
            "snapshot_hashes_included": False,
            "source_capture_ids_included": False,
            "raw_ids_included": False,
            "raw_paths_included": False,
            "source_fingerprints_included": False,
        },
        "public_release_safe": True,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    args.output.write_text(text, encoding="utf-8")
    print(text, end="")

    return 0 if review.observed_build_provenance_complete else 4


if __name__ == "__main__":
    raise SystemExit(main())
