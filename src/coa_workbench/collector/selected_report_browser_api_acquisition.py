from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from urllib.request import Request

from coa_workbench.analytics.public_api_encounter_context import EncounterReference
from coa_workbench.analytics.selected_report_source_availability import (
    SelectedReportSourceAvailabilityReview,
    review_selected_report_source_availability,
)
from coa_workbench.collector.http_read import read_response_resilient
from coa_workbench.collector.raw_archive import RawArchive
from coa_workbench.collector.source_acquisition import _archive_and_record
from coa_workbench.collector.source_observatory import ReviewedGetContract, build_get_url
from coa_workbench.collector.source_registry import SourceRegistry, SourceRoute, load_source_registry

SELECTED_REPORT_BROWSER_API_ACQUISITION_VERSION = (
    "selected-report-browser-context-api-acquisition-v1"
)
_REQUIRED_ENDPOINTS = (
    "report_detail_api",
    "report_encounters_api",
    "report_combatants_roster_api",
)


@dataclass(frozen=True, slots=True)
class SelectedReportBrowserApiSourceResult:
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
class SelectedReportBrowserApiAcquisitionReview:
    results: tuple[SelectedReportBrowserApiSourceResult, ...]
    availability_after: SelectedReportSourceAvailabilityReview
    api_request_count: int
    already_observatory_ready_count: int
    browser_navigation_performed: bool

    @property
    def complete(self) -> bool:
        return self.availability_after.offline_current_report_runtime_reconstruction_possible

    def public_summary(self) -> dict[str, Any]:
        return {
            "acquisition_version": SELECTED_REPORT_BROWSER_API_ACQUISITION_VERSION,
            "required_source_family_count": len(_REQUIRED_ENDPOINTS),
            "network_request_count": self.api_request_count,
            "api_request_count": self.api_request_count,
            "already_observatory_ready_count": self.already_observatory_ready_count,
            "browser_context_api_used_this_run": self.api_request_count > 0,
            "browser_navigation_performed": self.browser_navigation_performed,
            "browser_har_used_this_run": False,
            "browser_trace_used_this_run": False,
            "events_read_used": False,
            "raw_payload_bodies_read_from_archive": False,
            "direct_http_used_this_run": False,
            "same_origin_browser_fetch_only": True,
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
            "browser_profile_values_included": False,
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


def acquire_selected_report_core_sources_in_browser_context(
    *,
    database_path: Path,
    migrations_path: Path,
    raw_root: Path,
    registry_path: Path,
    reference: EncounterReference,
    opener: Callable[..., Any] | None,
    timeout_seconds: float = 20.0,
    max_bytes: int = 32 * 1024 * 1024,
    browser_navigation_performed: bool = False,
) -> SelectedReportBrowserApiAcquisitionReview:
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
    requires_request = any(
        not before_by_endpoint[endpoint_code].source_observatory_ready
        for endpoint_code in _REQUIRED_ENDPOINTS
    )
    if requires_request and opener is None:
        raise ValueError("browser-context API opener is required for not-ready sources")

    archive = RawArchive(
        raw_root,
        database_path=database_path,
        migrations_dir=migrations_path,
    )
    results: list[SelectedReportBrowserApiSourceResult] = []
    api_request_count = 0
    already_ready_count = 0

    for endpoint_code in _REQUIRED_ENDPOINTS:
        previous = before_by_endpoint[endpoint_code]
        if previous.source_observatory_ready:
            already_ready_count += 1
            results.append(
                SelectedReportBrowserApiSourceResult(
                    endpoint_code=endpoint_code,
                    source_mode="already_observatory_ready",
                    outcome="schema_candidate",
                    blocker_class=None,
                    http_status=None,
                )
            )
            continue

        route, contract = _contract(registry, endpoint_code)
        request_url = build_get_url(
            contract,
            path_params={"reportId": reference.report_id},
            query_params=_query(endpoint_code, reference.encounter_id),
        )
        request = Request(request_url, method="GET", headers={"Accept": "application/json"})
        status, content_type, body, error = read_response_resilient(
            request,
            timeout_seconds=timeout_seconds,
            opener=opener,
            max_bytes=max_bytes,
            retry_count=0,
        )
        api_request_count += 1
        observed = _archive_and_record(
            archive=archive,
            database_path=database_path,
            migrations_dir=migrations_path,
            contract=contract,
            request_url=request_url,
            body=body,
            http_status=status,
            content_type=content_type,
            capture_mode="browser_context_api",
            dimension_keys=route.dimension_keys,
            error=error,
        )
        results.append(
            SelectedReportBrowserApiSourceResult(
                endpoint_code=endpoint_code,
                source_mode="browser_context_api",
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
    return SelectedReportBrowserApiAcquisitionReview(
        results=tuple(results),
        availability_after=after,
        api_request_count=api_request_count,
        already_observatory_ready_count=already_ready_count,
        browser_navigation_performed=browser_navigation_performed,
    )


__all__ = [
    "SELECTED_REPORT_BROWSER_API_ACQUISITION_VERSION",
    "SelectedReportBrowserApiAcquisitionReview",
    "SelectedReportBrowserApiSourceResult",
    "acquire_selected_report_core_sources_in_browser_context",
]
