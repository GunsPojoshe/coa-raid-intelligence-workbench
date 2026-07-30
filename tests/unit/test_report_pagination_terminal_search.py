from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

from coa_workbench.collector import RawArchive, load_source_registry
from coa_workbench.collector.report_pagination_terminal_search import (
    capture_report_pagination_terminal_search,
)


class _Headers:
    def get_content_type(self) -> str:
        return "application/json"


class _Response:
    def __init__(self, payload: object) -> None:
        self.status = 200
        self.headers = _Headers()
        self._body = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self, size: int = -1) -> bytes:
        if size is None or size < 0:
            return self._body
        return self._body[:size]


class _PageOpener:
    def __init__(self, payloads: dict[int, object]) -> None:
        self.payloads = payloads
        self.requested_pages: list[int] = []

    def __call__(self, request, **_kwargs):
        page = int(parse_qs(urlsplit(request.full_url).query)["page"][0])
        self.requested_pages.append(page)
        return _Response(self.payloads[page])


def _write(path: Path, payload: object) -> bytes:
    body = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    path.write_bytes(body)
    return body


def _private_page(page: int, *, has_more: bool, count: int = 5) -> dict:
    return {
        "page": page,
        "limit": 5,
        "raw_id": f"{page:064x}",
        "observation_id": f"{page + 100:064x}",
        "payload_hash": f"{page + 200:064x}",
        "schema_fingerprint": f"{page + 300:064x}",
        "source_report_ids": [700000 + page * 10 + index for index in range(count)],
        "pagination": {
            "hasMore": has_more,
            "hasPrevious": page > 1,
            "limit": 5,
            "offset": (page - 1) * 5,
            "page": page,
        },
        "report_count": count,
        "duplicate_with_prior_pages_count": 0,
    }


def _packet(tmp_path: Path) -> tuple[Path, Path]:
    private = {
        "schema_version": 1,
        "probe_kind": "report_pagination_boundary_private_batch",
        "probe_version": "report-pagination-boundary-probe-v1",
        "generated_at": "2026-07-30T00:14:09Z",
        "source_semantic_review_name": "pagination-review.json",
        "source_semantic_review_sha256": "a" * 64,
        "source_baseline_private_name": "pagination.private.json",
        "source_baseline_private_sha256": "b" * 64,
        "target_guild_label": "Argentum",
        "request": {
            "route_template": "/api/reports/public",
            "probe_pages": [4, 8, 16],
            "limit": 5,
            "sort_by": "created_at",
            "sort_order": "desc",
            "http_profile_version": "coa-fetch-context-v1",
        },
        "pages": [
            _private_page(4, has_more=True),
            _private_page(8, has_more=True),
            _private_page(16, has_more=False, count=0),
        ],
        "summary": {
            "captured_page_count": 3,
            "report_occurrence_count": 10,
            "unique_report_id_count": 10,
            "contains_source_scalar_values": True,
        },
    }
    private_path = tmp_path / "boundary.private.json"
    private_body = _write(private_path, private)

    boundary = {
        "schema_version": 1,
        "probe_kind": "report_pagination_boundary_probe",
        "probe_version": "report-pagination-boundary-probe-v1",
        "generated_at": "2026-07-30T00:14:10Z",
        "source_private_probe_name": private_path.name,
        "source_private_probe_sha256": hashlib.sha256(private_body).hexdigest(),
        "target": {
            "guild_label": "Argentum",
            "guild_identity_status": "operator_named_target_unresolved",
        },
        "request": {
            "route_template": "/api/reports/public",
            "probe_pages": [4, 8, 16],
            "limit": 5,
            "sort_by": "created_at",
            "sort_order": "desc",
            "http_profile_version": "coa-fetch-context-v1",
        },
        "boundary_observation": {
            "baseline_lower_bound_page": 3,
            "highest_more_pages_candidate": 8,
            "lowest_terminal_candidate": 16,
            "terminal_bracket_observed": True,
            "monotonic_has_more_candidate": True,
        },
        "decision_boundary": {
            "status": "bounded_pagination_boundary_probe_completed",
            "page_semantics_verified": True,
            "page_size_semantics_verified": True,
            "offset_semantics_verified": True,
            "has_previous_semantics_verified": True,
            "has_more_semantics_verified": False,
            "termination_condition_verified": False,
            "terminal_bracket_observed": True,
            "ready_for_bounded_terminal_search": True,
            "ready_for_larger_bounded_probe": False,
            "automatic_full_manifest_collection_allowed": False,
            "ready_for_exhaustive_public_report_manifest_capture": False,
            "ready_for_full_guild_crawl": False,
            "ready_for_guild_identity_review": False,
            "ready_for_guild_filtering": False,
            "ready_for_multi_report_character_graph": False,
            "ready_for_performance_model": False,
            "ready_for_global_benchmark": False,
            "ready_for_bis25_scoring": False,
            "planner_scoring_allowed": False,
            "private_probe_contains_source_scalar_values": True,
        },
        "summary": {
            "baseline_page_count": 3,
            "probe_page_count": 3,
            "completed_probe_page_count": 3,
            "report_occurrence_count": 10,
            "unique_probe_report_id_count": 10,
            "duplicate_with_baseline_or_prior_count": 0,
            "empty_probe_page_count": 1,
            "has_more_true_probe_page_count": 2,
            "has_more_false_probe_page_count": 1,
            "terminal_bracket_observed": True,
            "integrity_check_count": 13,
            "all_integrity_checks_passed": True,
            "contains_source_scalar_values": False,
            "private_probe_contains_source_scalar_values": True,
            "ready_for_bounded_terminal_search": True,
            "ready_for_larger_bounded_probe": False,
            "ready_for_exhaustive_public_report_manifest_capture": False,
            "ready_for_full_guild_crawl": False,
            "ready_for_bis25_scoring": False,
        },
    }
    boundary_path = tmp_path / "boundary.json"
    _write(boundary_path, boundary)
    return boundary_path, private_path


def _payload(page: int, *, has_more: bool, count: int = 5) -> dict:
    return {
        "reports": [{"id": 900000 + page * 10 + index} for index in range(count)],
        "pagination": {
            "hasMore": has_more,
            "hasPrevious": page > 1,
            "limit": 5,
            "offset": (page - 1) * 5,
            "page": page,
        },
        "success": True,
    }


def _integer_values(value: object) -> set[int]:
    if isinstance(value, bool):
        return set()
    if isinstance(value, int):
        return {value}
    if isinstance(value, dict):
        result: set[int] = set()
        for child in value.values():
            result.update(_integer_values(child))
        return result
    if isinstance(value, list):
        result = set()
        for child in value:
            result.update(_integer_values(child))
        return result
    return set()


def _registry():
    return load_source_registry(Path("config/ascension_logs_sources.yaml"))


def _valid_payloads() -> dict[int, object]:
    return {
        10: _payload(10, has_more=True),
        11: _payload(11, has_more=False, count=2),
        12: _payload(12, has_more=False, count=0),
    }


def test_verifies_adjacent_terminal_transition_without_crawling_manifest(tmp_path: Path) -> None:
    boundary_path, private_path = _packet(tmp_path)
    opener = _PageOpener(_valid_payloads())

    receipt = capture_report_pagination_terminal_search(
        _registry(),
        RawArchive(tmp_path / "raw"),
        boundary_receipt_path=boundary_path,
        boundary_private_path=private_path,
        private_output_path=tmp_path / "search.private.json",
        receipt_output_path=tmp_path / "search.json",
        max_requests=6,
        opener=opener,
    )

    assert opener.requested_pages == [12, 10, 11, 10, 11, 12]
    assert receipt["terminal_contract"]["predecessor_page"] == 10
    assert receipt["terminal_contract"]["terminal_page"] == 11
    assert receipt["terminal_contract"]["successor_page"] == 12
    assert receipt["summary"]["terminal_page_report_count"] == 2
    assert receipt["summary"]["completed_request_count"] == 6
    assert receipt["decision_boundary"]["has_more_semantics_verified"] is True
    assert receipt["decision_boundary"]["termination_condition_verified"] is True
    assert receipt["decision_boundary"]["ready_for_exhaustive_public_report_manifest_capture"] is True
    assert receipt["decision_boundary"]["ready_for_full_guild_crawl"] is False
    assert receipt["decision_boundary"]["ready_for_bis25_scoring"] is False

    source_ids = {
        900000 + page * 10 + index
        for page, count in ((10, 5), (11, 2))
        for index in range(count)
    }
    assert source_ids.isdisjoint(_integer_values(receipt))


def test_rejects_empty_terminal_page(tmp_path: Path) -> None:
    boundary_path, private_path = _packet(tmp_path)
    payloads = _valid_payloads()
    payloads[11] = _payload(11, has_more=False, count=0)

    with pytest.raises(ValueError, match="terminal page must contain"):
        capture_report_pagination_terminal_search(
            _registry(),
            RawArchive(tmp_path / "raw"),
            boundary_receipt_path=boundary_path,
            boundary_private_path=private_path,
            private_output_path=tmp_path / "search.private.json",
            receipt_output_path=tmp_path / "search.json",
            max_requests=6,
            opener=_PageOpener(payloads),
        )


def test_rejects_boundary_private_changed_after_probe(tmp_path: Path) -> None:
    boundary_path, private_path = _packet(tmp_path)
    private = json.loads(private_path.read_text(encoding="utf-8"))
    private["pages"][1]["pagination"]["hasMore"] = False
    _write(private_path, private)

    with pytest.raises(ValueError, match="hash changed"):
        capture_report_pagination_terminal_search(
            _registry(),
            RawArchive(tmp_path / "raw"),
            boundary_receipt_path=boundary_path,
            boundary_private_path=private_path,
            private_output_path=tmp_path / "search.private.json",
            receipt_output_path=tmp_path / "search.json",
            max_requests=6,
            opener=_PageOpener({}),
        )


def test_rejects_has_more_true_on_successor_page(tmp_path: Path) -> None:
    boundary_path, private_path = _packet(tmp_path)
    payloads = _valid_payloads()
    payloads[12] = _payload(12, has_more=True, count=0)

    with pytest.raises(ValueError, match="successor page does not have hasMore=false"):
        capture_report_pagination_terminal_search(
            _registry(),
            RawArchive(tmp_path / "raw"),
            boundary_receipt_path=boundary_path,
            boundary_private_path=private_path,
            private_output_path=tmp_path / "search.private.json",
            receipt_output_path=tmp_path / "search.json",
            max_requests=6,
            opener=_PageOpener(payloads),
        )
