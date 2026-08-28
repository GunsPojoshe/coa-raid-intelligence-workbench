from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.analytics.public_api_encounter_comparator import (
    build_public_api_encounter_location_comparator,
    review_public_api_location_comparator,
)
from coa_workbench.analytics.public_api_encounter_context import (
    parse_encounter_reference_url,
    resolve_public_api_boss_id,
    review_public_api_encounter_context,
)
from coa_workbench.analytics.report_encounter_population_binding import (
    build_report_encounter_population_binding,
)
from coa_workbench.analytics.report_encounter_source_correlation import (
    correlate_report_encounter_catalog_payload,
    load_archived_report_encounter_catalog,
    load_persisted_report_encounter_catalog,
)
from coa_workbench.collector.public_api_catalog import (
    load_latest_public_api_payload,
    parse_public_api_phases,
    select_current_phase_number,
)
from coa_workbench.collector.source_registry import load_source_registry


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Bind one machine-correlated report encounter to the already-persisted official "
            "population context and matched location comparator. This command performs no "
            "network requests and publishes only scalar-safe booleans/counts/version markers."
        )
    )
    parser.add_argument("--reference-url", required=True)
    parser.add_argument("--boss-name", required=True)
    parser.add_argument("--location", required=True)
    parser.add_argument(
        "--difficulty",
        required=True,
        choices=("normal", "heroic", "mythic", "ascended"),
    )
    parser.add_argument(
        "--site-registry",
        type=Path,
        default=Path("config/ascension_logs_sources.yaml"),
    )
    parser.add_argument(
        "--public-api-registry",
        type=Path,
        default=Path("config/coa_public_api_sources.yaml"),
    )
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("data/warehouse/coa.duckdb"),
    )
    parser.add_argument("--migrations", type=Path, default=Path("migrations"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/coa-report-encounter-population-binding-review.json"),
    )
    return parser.parse_args()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _privacy() -> dict[str, bool]:
    return {
        "report_ids_included": False,
        "encounter_ids_included": False,
        "boss_names_included": False,
        "boss_ids_included": False,
        "location_values_included": False,
        "difficulty_values_included": False,
        "phase_values_included": False,
        "query_values_included": False,
        "class_names_included": False,
        "spec_names_included": False,
        "metric_scalar_values_included": False,
        "parse_share_values_included": False,
        "raw_ids_included": False,
        "raw_paths_included": False,
        "request_urls_included": False,
        "source_structure_fingerprints_included": False,
    }


def main() -> int:
    args = _arguments()
    reference = parse_encounter_reference_url(args.reference_url)
    site_registry = load_source_registry(args.site_registry)

    source_kind: str
    catalog_observation_count: int
    persisted = load_persisted_report_encounter_catalog(
        args.database,
        reference=reference,
    )
    if persisted is not None:
        catalog = persisted
        source_kind = "persisted_first_party_encounter_catalog"
    else:
        archived = load_archived_report_encounter_catalog(
            args.raw_root,
            args.database,
            reference=reference,
            source_code=site_registry.source_code,
            base_url=site_registry.base_url,
        )
        if archived is None:
            review = {
                "schema_version": 1,
                "review_kind": "report_encounter_population_binding",
                "failure": {"kind": "local_report_catalog_evidence_unavailable"},
                "source": {
                    "network_request_count": 0,
                    "persisted_report_catalog_reused": False,
                    "archived_report_catalog_reused": False,
                    "existing_public_api_persistence_reused": False,
                    "events_read_used": False,
                    "browser_har_used": False,
                },
                "privacy": _privacy(),
                "verification": {
                    "machine_correlated_encounter_population_binding_complete": False,
                    "player_identity_verified": False,
                    "mechanic_semantics_verified": False,
                    "planner_scoring_allowed": False,
                },
                "public_release_safe": True,
            }
            _write_json(args.output, review)
            print(json.dumps(review, indent=2, sort_keys=True))
            return 4
        catalog = archived
        source_kind = "archived_first_party_encounter_catalog"

    catalog_observation_count = catalog.matching_observation_count
    correlation = correlate_report_encounter_catalog_payload(
        catalog.payload,
        reference=reference,
        expected_boss_name=args.boss_name,
        expected_difficulty=args.difficulty,
        source_kind=source_kind,
    )

    public_registry = load_source_registry(args.public_api_registry)
    phases_payload = load_latest_public_api_payload(
        args.raw_root,
        source_code=public_registry.source_code,
        endpoint_code="public_api_phases",
    )
    bosses_payload = load_latest_public_api_payload(
        args.raw_root,
        source_code=public_registry.source_code,
        endpoint_code="public_api_bosses",
    )
    phase_number = select_current_phase_number(parse_public_api_phases(phases_payload))
    boss_id = resolve_public_api_boss_id(
        bosses_payload,
        boss_name=args.boss_name,
        location=args.location,
    )

    encounter_context = review_public_api_encounter_context(
        args.database,
        args.migrations,
        phase=phase_number,
        difficulty=args.difficulty,
        location=args.location,
        boss_id=boss_id,
    )
    location_comparator = review_public_api_location_comparator(
        args.database,
        args.migrations,
        phase=phase_number,
        difficulty=args.difficulty,
        location=args.location,
    )

    differential = None
    if correlation.complete and encounter_context.complete and location_comparator.complete:
        differential = build_public_api_encounter_location_comparator(
            args.database,
            args.migrations,
            phase=phase_number,
            difficulty=args.difficulty,
            location=args.location,
            boss_id=boss_id,
        )

    binding = build_report_encounter_population_binding(
        source_correlation=correlation,
        encounter_context=encounter_context,
        location_comparator=location_comparator,
        differential=differential,
        same_private_scope_inputs_reused=True,
    )
    summary = binding.public_summary()
    review = {
        "schema_version": 1,
        "review_kind": "report_encounter_population_binding",
        "source": {
            "report_catalog_source_kind": source_kind,
            "report_catalog_observation_count": catalog_observation_count,
            "persisted_report_catalog_reused": (
                source_kind == "persisted_first_party_encounter_catalog"
            ),
            "archived_report_catalog_reused": (
                source_kind == "archived_first_party_encounter_catalog"
            ),
            "existing_public_api_persistence_reused": True,
            "network_request_count": 0,
            "events_read_used": False,
            "browser_har_used": False,
        },
        "binding": summary,
        "verification": {
            "source_correlation_complete": correlation.complete,
            "exact_reference_identity_verified": correlation.exact_reference_identity_verified,
            "report_encounter_boss_source_correlated": correlation.boss_source_correlated,
            "report_encounter_difficulty_source_correlated": correlation.difficulty_source_correlated,
            "encounter_context_complete": encounter_context.complete,
            "location_comparator_complete": location_comparator.complete,
            "differential_built": differential is not None,
            "same_private_scope_inputs_reused": True,
            "machine_correlated_encounter_population_binding_complete": binding.complete,
            "no_historical_difficulty_heuristic_used": True,
            "player_identity_verified": False,
            "mechanic_semantics_verified": False,
            "site_tier_list_algorithm_verified": False,
            "planner_scoring_allowed": False,
        },
        "privacy": _privacy(),
        "public_release_safe": True,
    }
    _write_json(args.output, review)
    print(json.dumps(review, indent=2, sort_keys=True))
    return 0 if binding.complete else 4


if __name__ == "__main__":
    raise SystemExit(main())
