from __future__ import annotations

from pathlib import Path
from typing import Any

from coa_workbench.collector.public_api_archive import ArchivedPublicApiCapture
from coa_workbench.collector.source_acquisition import (
    SourceAcquisitionObservation,
    classify_acquisition,
    record_source_acquisition,
)
from coa_workbench.collector.source_health import build_source_health
from coa_workbench.collector.source_observatory import (
    ReviewedGetContract,
    build_get_url,
    observe_raw_capture,
)
from coa_workbench.collector.source_registry import SourceRegistry

PUBLIC_API_STATISTICS_ENDPOINT_CODE = "public_api_statistics"
_PUBLIC_API_STATISTICS_RESPONSE_DIMENSIONS = (
    "phase",
    "difficulty",
    "metric",
    "bracket",
    "location",
    "boss_id",
    "damage_mode",
    "week_number",
    "day_number",
)


def reviewed_public_api_contract(
    registry: SourceRegistry,
    *,
    endpoint_code: str = PUBLIC_API_STATISTICS_ENDPOINT_CODE,
) -> ReviewedGetContract:
    route = registry.route(endpoint_code, require_production=True)
    if not route.observatory_ready:
        raise ValueError(f"public API route {endpoint_code!r} is not Source Observatory ready")
    if route.method != "GET":
        raise ValueError("public API Source Observatory integration requires GET")
    if not route.route_template:
        raise ValueError("public API route template is unavailable")
    return ReviewedGetContract(
        source_code=registry.source_code,
        endpoint_code=route.endpoint_code,
        base_url=registry.base_url,
        route_template=route.route_template,
        parameter_keys=route.parameter_keys,
        schema_profile_keys=route.schema_profile_keys,
        auth_state=route.auth_mode,
        discovery_source=route.discovery_source,
        review_state=route.review_state,
        logical_name=route.use,
    )


def observe_archived_public_api_statistics(
    *,
    database_path: Path,
    migrations_path: Path,
    raw_root: Path,
    registry: SourceRegistry,
    capture: ArchivedPublicApiCapture,
) -> SourceAcquisitionObservation:
    """Register an archived statistics response in Source Observatory without network I/O."""
    if capture.endpoint_code != PUBLIC_API_STATISTICS_ENDPOINT_CODE:
        raise ValueError("archived capture is not public_api_statistics")
    if capture.source_code != registry.source_code:
        raise ValueError("archived public API capture source does not match registry")

    query_values = capture.query_value_mapping()
    missing_query_values = sorted(set(capture.query_keys) - set(query_values))
    if missing_query_values:
        raise ValueError(
            "archived public API observation lacks private values for request keys: "
            + ", ".join(missing_query_values)
        )

    contract = reviewed_public_api_contract(registry)
    request_url = build_get_url(contract, query_params=query_values)
    raw_capture = capture.as_raw_capture(raw_root)
    classification = classify_acquisition(
        status=capture.http_status,
        content_type=capture.content_type,
        body=capture.payload_bytes,
    )
    if classification.outcome != "schema_candidate":
        raise ValueError(
            "archived public API statistics capture is not a reviewed JSON schema candidate"
        )

    metadata = {
        "capture_mode": "official_public_api_stats",
        "access_scope": "stats:read",
        "archive_replay": True,
    }
    source_observation = observe_raw_capture(
        database_path,
        migrations_path,
        contract=contract,
        capture=raw_capture,
        payload=capture.payload_bytes,
        request_url=request_url,
        dimension_keys=_PUBLIC_API_STATISTICS_RESPONSE_DIMENSIONS,
        metadata=metadata,
    )
    return record_source_acquisition(
        database_path,
        migrations_path,
        contract=contract,
        request_url=request_url,
        capture_mode="official_public_api_stats",
        classification=classification,
        capture=raw_capture,
        source_observation=source_observation,
        metadata=metadata,
    )


def review_public_api_statistics_health(database_path: Path) -> dict[str, Any]:
    """Return a scalar-safe health receipt for the aggregate statistics artifact family."""
    health = build_source_health(database_path)
    endpoint = next(
        (
            item
            for item in health["endpoints"]
            if item["endpoint_code"] == PUBLIC_API_STATISTICS_ENDPOINT_CODE
        ),
        None,
    )

    import duckdb

    with duckdb.connect(str(database_path), read_only=True) as connection:
        source_endpoint_dependency_count = int(
            connection.execute(
                """
                SELECT COUNT(*)
                FROM artifact_dependency
                WHERE artifact_type = 'public_api_population_statistics'
                  AND dependency_type = 'source_endpoint'
                  AND dependency_key = ?
                  AND active = TRUE
                """,
                [PUBLIC_API_STATISTICS_ENDPOINT_CODE],
            ).fetchone()[0]
        )
        raw_dependency_count = int(
            connection.execute(
                """
                SELECT COUNT(*)
                FROM artifact_dependency
                WHERE artifact_type = 'public_api_population_statistics'
                  AND dependency_type = 'raw_object'
                  AND active = TRUE
                """
            ).fetchone()[0]
        )
        completed_analysis_run_count = int(
            connection.execute(
                """
                SELECT COUNT(*)
                FROM analysis_run
                WHERE artifact_type = 'public_api_population_statistics'
                  AND analysis_type = 'official_public_api_population_statistics'
                  AND status = 'completed'
                """
            ).fetchone()[0]
        )
        pending_reanalysis_count = int(
            connection.execute(
                """
                SELECT COUNT(*)
                FROM reanalysis_request
                WHERE artifact_type = 'public_api_population_statistics'
                  AND analysis_type = 'official_public_api_population_statistics'
                  AND status = 'pending'
                """
            ).fetchone()[0]
        )
        actionable_open_change_count = int(
            connection.execute(
                """
                SELECT COUNT(*)
                FROM source_change_event
                WHERE endpoint_code = ?
                  AND status = 'open'
                  AND severity <> 'info'
                """,
                [PUBLIC_API_STATISTICS_ENDPOINT_CODE],
            ).fetchone()[0]
        )

    latest_acquisition = endpoint["latest_acquisition"] if endpoint else None
    acquisition_healthy = bool(
        latest_acquisition
        and latest_acquisition.get("outcome") == "schema_candidate"
        and latest_acquisition.get("body_kind") == "json"
    )
    endpoint_registered = endpoint is not None
    capture_observed = bool(endpoint and int(endpoint["capture_count"]) > 0)
    schema_observed = bool(endpoint and endpoint["latest_schema"] is not None)
    source_endpoint_dependency_registered = source_endpoint_dependency_count > 0
    raw_dependency_registered = raw_dependency_count > 0
    analysis_run_registered = completed_analysis_run_count > 0
    no_pending_reanalysis = pending_reanalysis_count == 0
    no_actionable_open_source_change = actionable_open_change_count == 0
    source_observatory_integrated = all(
        (
            endpoint_registered,
            capture_observed,
            schema_observed,
            acquisition_healthy,
            source_endpoint_dependency_registered,
            raw_dependency_registered,
            analysis_run_registered,
        )
    )
    attention_required = not all(
        (
            source_observatory_integrated,
            no_pending_reanalysis,
            no_actionable_open_source_change,
        )
    )

    return {
        "schema_version": 1,
        "review_kind": "official_public_api_statistics_source_health",
        "source_observatory": {
            "endpoint_registered": endpoint_registered,
            "capture_count": int(endpoint["capture_count"]) if endpoint else 0,
            "schema_snapshot_observed": schema_observed,
            "acquisition_observed": latest_acquisition is not None,
            "latest_acquisition_outcome": (
                latest_acquisition.get("outcome") if latest_acquisition else None
            ),
            "open_change_event_count": int(endpoint["open_change_count"]) if endpoint else 0,
            "actionable_open_change_event_count": actionable_open_change_count,
            "generic_health_state": endpoint.get("health_state") if endpoint else None,
        },
        "analysis": {
            "source_endpoint_dependency_count": source_endpoint_dependency_count,
            "raw_dependency_count": raw_dependency_count,
            "completed_analysis_run_count": completed_analysis_run_count,
            "pending_reanalysis_request_count": pending_reanalysis_count,
        },
        "verification": {
            "source_observatory_integrated": source_observatory_integrated,
            "source_endpoint_dependency_registered": source_endpoint_dependency_registered,
            "raw_dependency_registered": raw_dependency_registered,
            "analysis_run_registered": analysis_run_registered,
            "no_pending_reanalysis": no_pending_reanalysis,
            "no_actionable_open_source_change": no_actionable_open_source_change,
            "attention_required": attention_required,
            "planner_scoring_allowed": False,
        },
        "privacy": {
            "query_values_included": False,
            "dimension_values_included": False,
            "raw_ids_included": False,
            "request_fingerprints_included": False,
            "schema_fingerprints_included": False,
            "artifact_keys_included": False,
            "class_names_included": False,
            "spec_names_included": False,
        },
        "public_release_safe": True,
    }


__all__ = [
    "PUBLIC_API_STATISTICS_ENDPOINT_CODE",
    "observe_archived_public_api_statistics",
    "review_public_api_statistics_health",
    "reviewed_public_api_contract",
]
