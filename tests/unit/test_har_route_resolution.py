from __future__ import annotations

from coa_workbench.collector.har_route_resolution import (
    generic_har_ingest_ready,
    route_requires_explicit_dynamic_resolution,
)


def test_generic_har_ingestion_accepts_only_exact_static_paths() -> None:
    assert generic_har_ingest_ready("/api/reports/public/filter-options") is True
    assert generic_har_ingest_ready("/api/reports/queue-status") is True
    assert generic_har_ingest_ready("/api/reports/{reportId}") is False
    assert generic_har_ingest_ready(
        "/api/reports/{reportId}/encounters/{encounterId}/combatants-info"
    ) is False


def test_dynamic_route_detection_is_explicit_and_null_safe() -> None:
    assert route_requires_explicit_dynamic_resolution(None) is False
    assert route_requires_explicit_dynamic_resolution("/api/phases") is False
    assert route_requires_explicit_dynamic_resolution("/api/reports/{reportId}") is True
