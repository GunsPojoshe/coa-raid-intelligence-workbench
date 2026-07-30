from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from coa_workbench.collector import RawArchive, load_source_registry
from coa_workbench.collector import public_report_manifest_compat as manifest_compat
from coa_workbench.collector.report_discovery import capture_public_report_discovery


class _Headers:
    def get_content_type(self) -> str:
        return "application/json"


class _Response:
    status = 200
    headers = _Headers()

    def __init__(self, body: bytes) -> None:
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self, size: int = -1) -> bytes:
        return self._body if size < 0 else self._body[:size]


def _registry():
    return load_source_registry(Path("config/ascension_logs_sources.yaml"))


def _opener(request, **_kwargs):
    payload = {
        "reports": [{"id": index} for index in range(25)],
        "pagination": {
            "page": 1,
            "limit": 25,
            "offset": 0,
            "hasPrevious": False,
            "hasMore": True,
        },
        "success": True,
    }
    return _Response(json.dumps(payload).encode())


def test_limit_25_requires_explicit_promotion(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="exact promoted limit 25"):
        capture_public_report_discovery(
            _registry(), RawArchive(tmp_path / "raw"), limit=25, opener=_opener
        )


def test_limit_25_capture_records_promoted_contract(tmp_path: Path) -> None:
    result = capture_public_report_discovery(
        _registry(),
        RawArchive(tmp_path / "raw"),
        limit=25,
        allow_promoted_limit=True,
        opener=_opener,
    )
    assert result.complete is True
    assert result.capture is not None
    manifest = json.loads(Path(result.capture.manifest_path).read_text(encoding="utf-8"))
    assert manifest["metadata"]["limit"] == 25
    assert manifest["metadata"]["limit_contract"] == "manually_promoted_terminal_search"


def test_promoted_and_probe_limit_modes_are_mutually_exclusive(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="mutually exclusive"):
        capture_public_report_discovery(
            _registry(),
            RawArchive(tmp_path / "raw"),
            limit=25,
            allow_promoted_limit=True,
            allow_unverified_limit_probe=True,
            opener=_opener,
        )


def test_promoted_terminal_receipt_and_private_contract() -> None:
    terminal_page = 251
    terminal_count = 7
    receipt = {
        "schema_version": 1,
        "search_kind": "report_pagination_terminal_search",
        "search_version": "report-pagination-terminal-search-v2",
        "source_limit_promotion_sha256": "a" * 64,
        "source_limit_probe_sha256": "b" * 64,
        "source_limit_probe_private_sha256": "c" * 64,
        "target": {
            "guild_label": "Argentum",
            "guild_identity_status": "operator_named_target_unresolved",
        },
        "request": {
            "route_template": "/api/reports/public",
            "initial_lower_bound": 2,
            "initial_upper_bound": 8192,
            "limit": 25,
            "sort_by": "created_at",
            "sort_order": "desc",
            "http_profile_version": "coa-fetch-context-v1",
        },
        "summary": {
            "all_integrity_checks_passed": True,
            "contains_source_scalar_values": False,
            "promoted_limit": 25,
            "ready_for_exhaustive_public_report_manifest_capture": True,
            "terminal_page": terminal_page,
            "terminal_page_report_count": terminal_count,
        },
        "decision_boundary": {
            "status": "promoted_limit_pagination_terminal_contract_verified",
            "page_semantics_verified": True,
            "page_size_semantics_verified": True,
            "promoted_limit_verified": True,
            "offset_semantics_verified": True,
            "has_previous_semantics_verified": True,
            "has_more_semantics_verified": True,
            "termination_condition_verified": True,
            "terminal_page_verified": True,
            "ready_for_exhaustive_public_report_manifest_capture": True,
            "ready_for_guild_filtering": False,
            "planner_scoring_allowed": False,
        },
        "terminal_contract": {
            "status": "verified_adjacent_transition",
            "strategy": "request_pages_1_through_terminal_page_inclusive",
            "terminal_page": terminal_page,
            "successor_page": terminal_page + 1,
            "terminal_page_report_count": terminal_count,
            "inclusive_terminal_page": True,
            "deduplication_key": "/reports/*/id",
        },
    }
    assert manifest_compat._validate_promoted_terminal_receipt(receipt, "Argentum") == (
        terminal_page,
        terminal_count,
        25,
    )

    def row(phase: str, page: int, has_more: bool, count: int) -> dict[str, object]:
        return {
            "phase": phase,
            "page": page,
            "pagination": {
                "page": page,
                "limit": 25,
                "offset": (page - 1) * 25,
                "hasPrevious": page > 1,
                "hasMore": has_more,
            },
            "source_report_ids": list(range(count)),
        }

    private = {
        "schema_version": 1,
        "search_kind": "report_pagination_terminal_search_private_batch",
        "search_version": "report-pagination-terminal-search-v2",
        "target_guild_label": "Argentum",
        "source_limit_promotion_sha256": "a" * 64,
        "source_limit_probe_sha256": "b" * 64,
        "source_limit_probe_private_sha256": "c" * 64,
        "request": receipt["request"],
        "pages": [
            row("final_predecessor", terminal_page - 1, True, 25),
            row("final_terminal", terminal_page, False, terminal_count),
            row("final_successor", terminal_page + 1, False, 0),
        ],
    }
    private_body = (json.dumps(private, sort_keys=True) + "\n").encode()
    receipt["source_private_search_sha256"] = hashlib.sha256(private_body).hexdigest()
    manifest_compat._validate_promoted_terminal_private(
        private, private_body, receipt, "Argentum", terminal_page
    )
