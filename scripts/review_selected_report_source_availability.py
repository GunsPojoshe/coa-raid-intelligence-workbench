from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.analytics.public_api_encounter_context import parse_encounter_reference_url
from coa_workbench.analytics.selected_report_source_availability import (
    review_selected_report_source_availability,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Review whether the three already-reviewed current-report source families for a "
            "selected encounter report already exist in the local raw archive / Source "
            "Observatory. This command performs no network I/O and does not read raw payload "
            "bodies."
        )
    )
    parser.add_argument("--reference-url", required=True)
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("data/warehouse/coa.duckdb"),
    )
    parser.add_argument(
        "--raw-root",
        type=Path,
        default=Path("data/raw"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/coa-selected-report-source-availability-review.json"),
    )
    args = parser.parse_args()

    reference = parse_encounter_reference_url(args.reference_url)
    try:
        review = review_selected_report_source_availability(
            args.database,
            raw_root=args.raw_root,
            reference=reference,
        )
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        raise SystemExit(f"selected-report source availability review failed: {exc}") from exc

    summary = review.public_summary()
    receipt = {
        "schema_version": 1,
        "review_kind": "selected_report_source_availability",
        "source": {
            "existing_local_raw_archive_reused": True,
            "existing_source_observatory_reused": True,
            "network_request_count": 0,
            "raw_payload_bodies_read": False,
            "browser_har_used_this_run": False,
            "events_read_used": False,
        },
        "review": summary,
        "verification": {
            "selected_report_current_runtime_persisted": summary[
                "selected_report_current_runtime_persisted"
            ],
            "offline_source_reuse_candidate": summary["offline_source_reuse_candidate"],
            "offline_source_observatory_reuse_ready": summary[
                "offline_source_observatory_reuse_ready"
            ],
            "offline_current_report_runtime_reconstruction_possible": summary[
                "offline_current_report_runtime_reconstruction_possible"
            ],
            "selected_reference_same_report_build_binding_proven": False,
            "current_build_freshness_verified": False,
            "latest_snapshot_semantics_verified": False,
            "cross_report_identity_verified": False,
            "mechanic_semantics_verified": False,
            "planner_scoring_allowed": False,
        },
        "privacy": {
            "report_ids_included": False,
            "encounter_ids_included": False,
            "request_urls_included": False,
            "query_values_included": False,
            "raw_ids_included": False,
            "raw_paths_included": False,
            "source_capture_ids_included": False,
            "source_fingerprints_included": False,
            "player_ids_included": False,
            "player_names_included": False,
            "build_values_included": False,
        },
        "public_release_safe": True,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    args.output.write_text(text, encoding="utf-8")
    print(text, end="")

    ready = (
        review.selected_report_current_runtime_persisted
        or review.offline_current_report_runtime_reconstruction_possible
    )
    return 0 if ready else 4


if __name__ == "__main__":
    raise SystemExit(main())
