from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.analytics.current_roster_build_provenance_catalog import (
    review_current_roster_build_provenance_catalog,
)
from coa_workbench.analytics.public_api_encounter_context import parse_encounter_reference_url


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Review report-scoped player identity and observed build provenance across already "
            "persisted current-report roster observations. The selected reference is checked "
            "separately. This command performs no network I/O."
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
        review = review_current_roster_build_provenance_catalog(
            args.database,
            reference=reference,
        )
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        raise SystemExit(f"current roster build provenance review failed: {exc}") from exc

    summary = review.public_summary()
    receipt = {
        "schema_version": 2,
        "review_kind": "current_roster_build_provenance_catalog",
        "source": {
            "existing_current_report_persistence_reused": True,
            "canonical_entity_observation_reused": True,
            "network_request_count": 0,
            "browser_har_used_this_run": False,
            "events_read_used": False,
        },
        "review": summary,
        "verification": {
            "all_persisted_report_scopes_reviewed": summary["all_persisted_report_scopes_reviewed"],
            "all_persisted_report_build_provenance_complete": summary[
                "all_persisted_report_build_provenance_complete"
            ],
            "selected_reference_present": summary["selected_reference_present"],
            "selected_reference_report_scoped_player_identity_complete": summary[
                "selected_reference_report_scoped_player_identity_complete"
            ],
            "selected_reference_observed_build_provenance_complete": summary[
                "selected_reference_observed_build_provenance_complete"
            ],
            "selected_reference_same_report_build_binding_proven": summary[
                "selected_reference_same_report_build_binding_proven"
            ],
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

    if review.selected_reference_same_report_build_binding_proven:
        return 0
    if review.all_persisted_report_build_provenance_complete:
        return 4
    return 5


if __name__ == "__main__":
    raise SystemExit(main())
