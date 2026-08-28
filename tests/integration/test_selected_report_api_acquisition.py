from __future__ import annotations

from pathlib import Path

import pytest

from coa_workbench.analytics.public_api_encounter_context import EncounterReference
from coa_workbench.collector.selected_report_api_acquisition import (
    acquire_selected_report_core_sources,
)
from coa_workbench.storage.migrations import apply_migrations


duckdb = pytest.importorskip("duckdb")


class _Headers:
    def get_content_type(self) -> str:
        return "application/json"


class _Response:
    status = 200
    headers = _Headers()

    def __init__(self, body: bytes) -> None:
        self._body = body
        self._read = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read1(self, _size: int) -> bytes:
        if self._read:
            return b""
        self._read = True
        return self._body


def test_selected_report_core_sources_use_direct_api_then_become_idempotent(
    tmp_path: Path,
) -> None:
    root = Path(__file__).resolve().parents[2]
    database = tmp_path / "coa.duckdb"
    raw_root = tmp_path / "raw"
    apply_migrations(database, root / "migrations")
    reference = EncounterReference(report_id=31135, encounter_id=703971)
    requested_urls: list[str] = []

    def opener(request, **_kwargs):
        requested_urls.append(request.full_url)
        return _Response(b'{"ok":true,"rows":[]}')

    first = acquire_selected_report_core_sources(
        database_path=database,
        migrations_path=root / "migrations",
        raw_root=raw_root,
        registry_path=root / "config" / "ascension_logs_sources.yaml",
        reference=reference,
        opener=opener,
    )

    assert first.network_request_count == 3
    assert first.already_observatory_ready_count == 0
    assert first.complete is True
    assert first.availability_after.archived_required_source_family_count == 3
    assert first.availability_after.observatory_ready_required_source_family_count == 3
    assert len(requested_urls) == 3
    assert all(result.source_mode == "direct_api" for result in first.results)
    assert all(result.schema_candidate for result in first.results)
    assert all("/api/reports/31135" in url for url in requested_urls)
    assert any("includeTrash=false" in url for url in requested_urls)
    assert any("encounterIds=703971" in url for url in requested_urls)

    def unexpected_opener(*_args, **_kwargs):
        raise AssertionError("second pass must not perform API requests")

    second = acquire_selected_report_core_sources(
        database_path=database,
        migrations_path=root / "migrations",
        raw_root=raw_root,
        registry_path=root / "config" / "ascension_logs_sources.yaml",
        reference=reference,
        opener=unexpected_opener,
    )

    assert second.network_request_count == 0
    assert second.already_observatory_ready_count == 3
    assert second.complete is True
    assert all(result.source_mode == "already_observatory_ready" for result in second.results)

    summary = second.public_summary()
    assert summary["browser_har_used_this_run"] is False
    assert summary["events_read_used"] is False
    assert summary["raw_payload_bodies_read_from_archive"] is False
    assert summary["selected_reference_same_report_build_binding_proven"] is False
    assert summary["current_build_freshness_verified"] is False
    assert summary["planner_scoring_allowed"] is False
    assert summary["public_release_safe"] is True
