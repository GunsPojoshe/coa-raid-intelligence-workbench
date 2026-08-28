from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.analytics.public_api_population_coverage import (
    PUBLIC_API_POPULATION_COVERAGE_V1,
    review_public_api_population_coverage,
)
from coa_workbench.collector.public_api_archive import load_latest_public_api_capture
from coa_workbench.collector.public_api_catalog import (
    load_latest_public_api_payload,
    parse_public_api_phases,
    select_current_phase_number,
)
from coa_workbench.collector.public_api_credentials import (
    DEFAULT_PUBLIC_API_KEY_ENV,
    DEFAULT_PUBLIC_API_KEY_FILE,
    load_public_api_key,
)
from coa_workbench.collector.public_api_source_health import (
    PUBLIC_API_STATISTICS_ENDPOINT_CODE,
    observe_archived_public_api_statistics,
    private_public_api_statistics_profile_key,
    review_public_api_statistics_health,
)
from coa_workbench.collector.public_api_stats_capture import capture_public_api_stats
from coa_workbench.collector.raw_archive import RawArchive
from coa_workbench.collector.source_profile_reanalysis import (
    resolve_profile_reanalysis_requests,
)
from coa_workbench.collector.source_registry import load_source_registry
from coa_workbench.normalizer.public_api_statistics import parse_public_api_statistics
from coa_workbench.storage.public_api_statistics import persist_public_api_statistics


def _query_text(query: dict[str, object]) -> dict[str, str]:
    return {key: str(value) for key, value in query.items()}


def _safe_failure_kind(error: str | None) -> str | None:
    if error is None:
        return None
    folded = error.casefold()
    if "timeout" in folded:
        return "read_timeout"
    if "429" in folded or "rate" in folded:
        return "rate_limited"
    return "capture_incomplete"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Fill the bounded current-phase public population coverage plan. Existing persisted "
            "profiles are reused, so reruns perform network I/O only for still-missing slices."
        )
    )
    parser.add_argument(
        "--api-key-file",
        type=Path,
        default=DEFAULT_PUBLIC_API_KEY_FILE,
    )
    parser.add_argument("--api-key-env", default=DEFAULT_PUBLIC_API_KEY_ENV)
    parser.add_argument(
        "--registry",
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
        default=Path("data/exchange/out/coa-public-api-population-coverage-review.json"),
    )
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--retry-count", type=int, choices=(0, 1), default=1)
    args = parser.parse_args()

    registry = load_source_registry(args.registry)
    phases_payload = load_latest_public_api_payload(
        args.raw_root,
        source_code=registry.source_code,
        endpoint_code="public_api_phases",
    )
    phase_number = select_current_phase_number(parse_public_api_phases(phases_payload))
    before = review_public_api_population_coverage(
        args.database,
        args.migrations,
        phase=phase_number,
    )

    network_request_count = 0
    successful_capture_count = 0
    persisted_profile_count = 0
    inserted_batch_count = 0
    matched_batch_count = 0
    deterministic_replay_count = 0
    observed_change_event_count = 0
    failure_kind: str | None = None

    if before.missing_slice_indexes:
        try:
            api_key = load_public_api_key(key_file=args.api_key_file, env_name=args.api_key_env)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc

        archive = RawArchive(
            args.raw_root,
            database_path=args.database,
            migrations_dir=args.migrations,
        )
        for index in before.missing_slice_indexes:
            coverage_slice = PUBLIC_API_POPULATION_COVERAGE_V1[index]
            query = coverage_slice.query(phase=phase_number)
            result = capture_public_api_stats(
                registry,
                archive,
                endpoint_code=PUBLIC_API_STATISTICS_ENDPOINT_CODE,
                api_key=api_key,
                query=query,
                timeout_seconds=args.timeout_seconds,
                retry_count=args.retry_count,
            )
            network_request_count += 1
            if not result.complete:
                failure_kind = _safe_failure_kind(result.error)
                break

            successful_capture_count += 1
            capture = load_latest_public_api_capture(
                args.raw_root,
                source_code=registry.source_code,
                endpoint_code=PUBLIC_API_STATISTICS_ENDPOINT_CODE,
            )
            if capture.query_value_mapping() != _query_text(query):
                raise SystemExit(
                    "Latest archived /statistics capture does not match the intended private "
                    "coverage profile; refusing to persist it."
                )

            acquisition = observe_archived_public_api_statistics(
                database_path=args.database,
                migrations_path=args.migrations,
                raw_root=args.raw_root,
                registry=registry,
                capture=capture,
            )
            observed_change_event_count += len(
                acquisition.source_observation.change_event_ids
                if acquisition.source_observation is not None
                else ()
            )
            profile_key = private_public_api_statistics_profile_key(registry, capture)
            batch = parse_public_api_statistics(
                capture.payload,
                query_keys=capture.query_keys,
                query_values=capture.query_value_mapping(),
            )
            first = persist_public_api_statistics(
                database_path=args.database,
                migrations_path=args.migrations,
                source_raw_id=capture.raw_id,
                source_code=registry.source_code,
                source_profile_key=profile_key,
                batch=batch,
            )
            second = persist_public_api_statistics(
                database_path=args.database,
                migrations_path=args.migrations,
                source_raw_id=capture.raw_id,
                source_code=registry.source_code,
                source_profile_key=profile_key,
                batch=batch,
            )
            persisted_profile_count += 1
            inserted_batch_count += int(first["batch_inserted"] is True)
            matched_batch_count += int(first["batch_matched"] is True)
            deterministic_replay_count += int(
                second["batch_matched"] is True
                and second["class_rows_inserted"] == 0
                and second["class_rows_matched"] == len(batch.class_summaries)
                and second["spec_rows_inserted"] == 0
                and second["spec_rows_matched"] == len(batch.records)
            )

    profile_reanalysis = resolve_profile_reanalysis_requests(
        args.database,
        args.migrations,
        endpoint_codes=(PUBLIC_API_STATISTICS_ENDPOINT_CODE,),
    )
    after = review_public_api_population_coverage(
        args.database,
        args.migrations,
        phase=phase_number,
    )
    health = review_public_api_statistics_health(args.database)

    receipt = {
        "schema_version": 1,
        "review_kind": "official_public_api_population_coverage",
        "coverage_before": before.public_summary(),
        "execution": {
            "network_request_count": network_request_count,
            "successful_capture_count": successful_capture_count,
            "persisted_profile_count": persisted_profile_count,
            "inserted_batch_count": inserted_batch_count,
            "matched_existing_batch_count": matched_batch_count,
            "deterministic_second_replay_count": deterministic_replay_count,
            "observed_change_event_count": observed_change_event_count,
            "stopped_on_failure": failure_kind is not None,
            "failure_kind": failure_kind,
            "events_read_used": False,
            "bulk_dataset_mode": False,
        },
        "coverage_after": after.public_summary(),
        "profile_reanalysis": profile_reanalysis.public_summary(),
        "source_health": {
            "source_observatory_integrated": health["verification"][
                "source_observatory_integrated"
            ],
            "source_endpoint_profile_dependency_count": health["analysis"][
                "source_endpoint_profile_dependency_count"
            ],
            "legacy_unscoped_source_endpoint_dependency_count": health["analysis"][
                "legacy_unscoped_source_endpoint_dependency_count"
            ],
            "pending_reanalysis_request_count": health["analysis"][
                "pending_reanalysis_request_count"
            ],
            "actionable_open_source_change_event_count": health["source_observatory"][
                "actionable_open_change_event_count"
            ],
            "attention_required": health["verification"]["attention_required"],
        },
        "privacy": {
            "phase_values_included": False,
            "difficulty_values_included": False,
            "metric_values_included": False,
            "role_values_included": False,
            "query_values_included": False,
            "raw_ids_included": False,
            "raw_paths_included": False,
            "profile_fingerprints_included": False,
            "class_names_included": False,
            "spec_names_included": False,
            "metric_scalar_values_included": False,
        },
        "verification": {
            "bounded_population_coverage_complete": after.complete,
            "no_pending_reanalysis": health["analysis"]["pending_reanalysis_request_count"] == 0,
            "no_actionable_open_source_change": health["source_observatory"][
                "actionable_open_change_event_count"
            ]
            == 0,
            "source_health_attention_required": health["verification"]["attention_required"],
            "site_tier_list_algorithm_verified": False,
            "planner_scoring_allowed": False,
        },
        "public_release_safe": True,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    args.output.write_text(text, encoding="utf-8")
    print(text, end="")

    healthy = health["verification"]["attention_required"] is False
    return 0 if after.complete and healthy and failure_kind is None else 4


if __name__ == "__main__":
    raise SystemExit(main())
