from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from coa_workbench.analytics.public_api_encounter_context import EncounterReference
from coa_workbench.analytics.selected_report_source_availability import (
    SelectedReportSourceAvailabilityReview,
    review_selected_report_source_availability,
)
from coa_workbench.collector.raw_archive import RawArchive
from coa_workbench.collector.source_acquisition import capture_reviewed_get_observation
from coa_workbench.collector.source_observatory import ReviewedGetContract
from coa_workbench.collector.source_registry import SourceRegistry, SourceRoute, load_source_registry

SELECTED_REPORT_API_ACQUISITION_VERSION = "selected-report-api-acquisition-v1"
_REQUIRED_ENDPOINTS = (
    "report_detail_api",
    "report_encounters_api",
    "report_combatants_roster_api",
)


@dataclass(frozen=True, slots=True)
class SelectedReportApiSourceResult:
    endpoint_code: str
    source_mode: str
    outcome: str
    blocker_class: str | None
    http_status: int | None

    @property
    def schema_candidate(self) -> bool:
        return self.outcome == "schema_candidate"

    def public_summary(self) -> dict[str, Any]:
        return {
            "endpoint_code": self.endpoint_code,
            "source_mode": self.source_mode,
            "outcome": self.outcome,
            "schema_candidate": self.schema_candidate,
            "blocker_class": self.blocker_class,
            "http_status": self.http_status,
            "report_ids_included": False,
            "encounter_ids_included": False,
            "query_values_included": False,
            "request_urls_included": False,
            "raw_ids_included": False,
            "source_capture_ids_included": False,
        }


@dataclass(frozen=True, slots=True)
class SelectedReportApiAcquisitionReview:
    results: tuple[SelectedReportApiSourceResult, ...]
    availability_after: SelectedReportSourceAvailabilityReview
    network_request_count: int
    already_observatory_ready_count: int

    @property
    def complete(self) -> bool:
        return self.availability_after.offline_current_report_runtime_reconstruction_possible

    def public_summary(self) -> dict[str, Any]:
        return {
            "acquisition_version": SELECTED_REPORT_API_ACQUISITION_VERSION,
            "required_source_family_count": len(_REQUIRED_ENDPOINTS),
            "network_request_count": self.network_request_count,
            "already_observatory_ready_count": self.already_observatory_ready_count,
            "browser_har_used_this_run": False,
            "events_read_used": False,
            "raw_payload_bodies_read_from_archive": False,
            "direct_api_only_for_not_ready_sources": True,
            "source_families": [result.public_summary() for result in self.results],
            "all_required_sources_schema_candidate": self.complete,
            "availability_after": self.availability_after.public_summary(),
            "selected_report_current_runtime_persisted": (
                self.availability_after.selected_report_current_runtime_persisted
            ),
            "selected_reference_same_report_build_binding_proven": False,
            "current_build_freshness_verified": False,
            "latest_snapshot_semantics_verified": False,
            "cross_report_identity_verified": False,
            "mechanic_semantics_verified": False,
            "planner_scoring_allowed": False,
            "report_ids_included": False,
            "encounter_ids_included": False,
            "query_values_included": False,
            "request_urls_included": False,
            "player_ids_included": False,
            "player_names_included": False,
            "build_values_included": False,
            "raw_ids_included": False,
            "raw_paths_included": False,
            "source_capture_ids_included": False,
            "source_fingerprints_included": False,
            "public_release_safe": True,
        }


def _contract(
    registry: SourceRegistry,
    endpoint_code: str,
) -> tuple[SourceRoute, ReviewedGetContract]:
    route = registry.route(endpoint_code)
    if not route.observatory_ready:
        raise ValueError(f"source route {endpoint_code!r} is not observatory-ready")
    return route, ReviewedGetContract(
        source_code=registry.source_code,
        endpoint_code=route.endpoint_code,
        base_url=registry.base_url,
        route_template=str(route.route_template),
        parameter_keys=route.parameter_keys,
        schema_profile_keys=route.schema_profile_keys,
        auth_state=route.auth_mode,
        discovery_source=route.discovery_source,
        review_state=route.review_state,
        logical_name=route.use,
    )


def _query(endpoint_code: str, encounter_id: int) -> dict[str, object]:
    if endpoint_code == "report_detail_api":
        return {}
    if endpoint_code == "report_encounters_api":
        return {"includeTrash": "false"}
    if endpoint_code == "report_combatants_roster_api":
        return {"encounterIds": encounter_id}
    raise ValueError(f"unsupported selected-report core endpoint: {endpoint_code}")


def acquire_selected_report_core_sources(
    *,
    database_path: Path,
    migrations_path: Path,
    raw_root: Path,
    registry_path: Path,
    reference: EncounterReference,
    timeout_seconds: float = 20.0,
    max_bytes: int = 32 * 1024 * 1024,
    opener: Callable[..., Any] | None = None,
) -> SelectedReportApiAcquisitionReview:
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than zero")
    if max_bytes < 1:
        raise ValueError("max_bytes must be positive")

    registry = load_source_registry(registry_path)
    before = review_selected_report_source_availability(
        database_path,
        raw_root=raw_root,
        reference=reference,
    )
    before_by_endpoint = {family.endpoint_code: family for family in before.families}
    archive = RawArchive(
        raw_root,
        database_path=database_path,
        migrations_dir=migrations_path,
    )

    results: list[SelectedReportApiSourceResult] = []
    network_request_count = 0
    already_ready_count = 0

    for endpoint_code in _REQUIRED_ENDPOINTS:
        previous = before_by_endpoint[endpoint_code]
        if previous.source_observatory_ready:
            already_ready_count += 1
            results.append(
                SelectedReportApiSourceResult(
                    endpoint_code=endpoint_code,
                    source_mode="already_observatory_ready",
                    outcome="schema_candidate",
                    blocker_class=None,
                    http_status=None,
                )
            )
            continue

        route, contract = _contract(registry, endpoint_code)
        kwargs: dict[str, Any] = {}
        if opener is not None:
            kwargs["opener"] = opener
        observed = capture_reviewed_get_observation(
            archive=archive,
            database_path=database_path,
            migrations_dir=migrations_path,
            contract=contract,
            path_params={"reportId": reference.report_id},
            query_params=_query(endpoint_code, reference.encounter_id),
            dimension_keys=route.dimension_keys,
            timeout_seconds=timeout_seconds,
            max_bytes=max_bytes,
            **kwargs,
        )
        network_request_count += 1
        results.append(
            SelectedReportApiSourceResult(
                endpoint_code=endpoint_code,
                source_mode="direct_api",
                outcome=observed.outcome,
                blocker_class=observed.blocker_class,
                http_status=observed.http_status,
            )
        )

    after = review_selected_report_source_availability(
        database_path,
        raw_root=raw_root,
        reference=reference,
    )
    return SelectedReportApiAcquisitionReview(
        results=tuple(results),
        availability_after=after,
        network_request_count=network_request_count,
        already_observatory_ready_count=already_ready_count,
    )


__all__ = [
    "SELECTED_REPORT_API_ACQUISITION_VERSION",
    "SelectedReportApiAcquisitionReview",
    "SelectedReportApiSourceResult",
    "acquire_selected_report_core_sources",
]
