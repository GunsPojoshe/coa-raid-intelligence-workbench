from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.current_combatants_roster import parse_current_combatants_roster
from coa_workbench.collector.current_report_analytics import parse_current_report_analytics
from coa_workbench.collector.current_report_analytics_dependencies import (
    register_current_report_analytics_scoped_dependencies,
)
from coa_workbench.collector.current_report_har import extract_current_report_har_slice
from coa_workbench.collector.source_registry import load_source_registry
from coa_workbench.storage.current_report_analytics import (
    persist_current_report_analytics_observations,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Persist one already-observed current CoA report HAR as deterministic throughput, "
            "healing, and damage-taken read-model observations. The operation is local-only, "
            "requires previously persisted Source Observatory captures, and registers report-scoped "
            "dependencies for every source family used by the read model."
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
        "--registry",
        type=Path,
        default=Path("config/ascension_logs_sources.yaml"),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    har_slice = extract_current_report_har_slice(args.har)
    roster = parse_current_combatants_roster(har_slice.combatants_roster.payload)
    analytics = parse_current_report_analytics(har_slice, roster=roster)
    result = persist_current_report_analytics_observations(
        database_path=args.database,
        migrations_path=args.migrations,
        har_slice=har_slice,
        analytics=analytics,
    )
    registry = load_source_registry(args.registry)
    dependencies = register_current_report_analytics_scoped_dependencies(
        args.database,
        args.migrations,
        registry=registry,
        artifact_key=str(result["input_fingerprint"]),
    )

    public_result = {
        key: value
        for key, value in result.items()
        if key not in {"input_fingerprint", "output_fingerprint"}
    }
    public_result["analytics"] = analytics.public_summary()
    public_result["scoped_reanalysis_dependencies"] = dependencies.public_summary()
    public_result["reanalysis_dependencies_registered"] = dependencies.dependency_count > 0
    public_result["har_slice"] = har_slice.public_summary()
    public_result["network_requests_performed"] = False
    public_result["privacy"] = {
        "har_included": False,
        "raw_response_bodies_included": False,
        "report_ids_included": False,
        "encounter_ids_included": False,
        "character_ids_included": False,
        "character_names_included": False,
        "query_values_included": False,
        "dynamic_group_keys_included": False,
        "source_capture_ids_included": False,
        "source_scope_values_included": False,
        "source_scope_fingerprints_included": False,
        "input_output_fingerprints_included": False,
    }

    rendered = json.dumps(public_result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
