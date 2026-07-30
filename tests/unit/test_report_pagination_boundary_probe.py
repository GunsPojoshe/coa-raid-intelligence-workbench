from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

from coa_workbench.collector import RawArchive, load_source_registry
from coa_workbench.collector.report_pagination_boundary_probe import (
    capture_report_pagination_boundary_probe,
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


def _packet(tmp_path: Path) -> tuple[Path, Path]:
    baseline_pages = []
    for page in (1, 2, 3):
        baseline_pages.append(
            {
                "page": page,
                "limit": 5,
                "raw_id": f"{page:064x}",
                "observation_id": f"{page + 10:064x}",
                "payload_hash": f"{page + 20:064x}",
                "schema_fingerprint": f"{page + 30:064x}",
                "source_report_ids": [100000 + page * 10 + offset for offset in range(5)],
                "pagination": {
                    "hasMore": True,
                    "hasPrevious": page > 1,
                    "limit": 5,
                    "offset": (page - 1) * 5,
                    "page": page,
                },
                "pagination_shape": {},
                "top_level_keys": ["pagination", "reports", "success"],
                "report_count": 5,
                "duplicate_within_page_count": 0,
                "duplicate_with_prior_pages_count": 0,
            }
        )

    baseline = {
        "schema_version": 1,
        "evidence_kind": "bounded_report_pagination_private_batch",
        "evidence_version": "report-pagination-evidence-v1",
        "generated_at": "2026-07-30T00:00:00Z",
        "source_contract_name": "argentum-guild-report-collection-contract.json",
        "source_contract_sha256": "a" * 64,
        "target_guild_label": "Argentum",
        "request": {
            "route_template": "/api/reports/public",
            "start_page": 1,
            "page_count": 3,
            "limit": 5,
            "sort_by": "created_at",
            "sort_order": "desc",
            "http_profile_version": "coa-fetch-context-v1",
        },
        "pages": baseline_pages,
        "summary": {
            "captured_page_count": 3,
            "report_occurrence_count": 15,
            "unique_report_id_count": 15,
            "duplicate_report_occurrence_count": 0,
            "empty_page_count": 0,
            "contains_source_scalar_values": True,
        },
    }
    baseline_path = tmp_path / "pagination.private.json"
    baseline_body = _write(baseline_path, baseline)

    field_contracts = [
        {
            "field_name": "hasMore",
            "semantic_assignment": "unassigned",
            "semantic_status": "unresolved",
        },
        {
            "field_name": "hasPrevious",
            "semantic_assignment": "unassigned",
            "semantic_status": "unresolved",
        },
        {
            "field_name": "limit",
            "semantic_assignment": "page_size",
            "semantic_status": "relationship_verified",
        },
        {
            "field_name": "offset",
            "semantic_assignment": "unassigned",
            "semantic_status": "unresolved",
        },
        {
            "field_name": "page",
            "semantic_assignment": "current_page",
            "semantic_status": "relationship_verified",
        },
    ]
    review = {
        "schema_version": 1,
        "review_kind": "report_pagination_semantic_review",
        "review_version": "report-pagination-semantic-review-v1",
        "generated_at": "2026-07-30T00:00:01Z",
        "source_private_evidence_name": baseline_path.name,
        "source_private_evidence_sha256": hashlib.sha256(baseline_body).hexdigest(),
        "target": {
            "guild_label": "Argentum",
            "guild_identity_status": "operator_named_target_unresolved",
        },
        "request": {
            "route_template": "/api/reports/public",
            "reviewed_pages": [1, 2, 3],
            "limit": 5,
            "sort_by": "created_at",
            "sort_order": "desc",
        },
        "field_contracts": field_contracts,
        "semantic_assignments": {
            "current_page_candidate_count": 1,
            "current_page_field": "page",
            "has_next_page_candidate_count": 0,
            "has_next_page_field": None,
            "page_size_candidate_count": 1,
            "page_size_field": "limit",
            "total_page_count_field": None,
            "total_record_count_field": None,
            "total_record_page_pair_candidate_count": 0,
        },
        "decision_boundary": {
            "status": "pagination_semantics_reviewed",
            "pagination_field_semantics_verified": False,
            "termination_condition_verified": False,
            "ready_for_exhaustive_public_report_manifest_capture": False,
            "ready_for_full_guild_crawl": False,
            "ready_for_guild_identity_review": False,
            "ready_for_guild_filtering": False,
            "ready_for_multi_report_character_graph": False,
            "ready_for_performance_model": False,
            "ready_for_global_benchmark": False,
            "ready_for_bis25_scoring": False,
            "planner_scoring_allowed": False,
        },
        "summary": {
            "reviewed_page_count": 3,
            "pagination_direct_field_count": 5,
            "relationship_verified_field_count": 2,
            "unresolved_field_count": 3,
            "pagination_field_semantics_verified": False,
            "termination_condition_verified": False,
            "ready_for_exhaustive_public_report_manifest_capture": False,
            "ready_for_full_guild_crawl": False,
            "ready_for_bis25_scoring": False,
            "all_integrity_checks_passed": True,
            "contains_source_scalar_values": False,
            "private_evidence_contains_source_scalar_values": True,
        },
    }
    review_path = tmp_path / "pagination-review.json"
    _write(review_path, review)
    return review_path, baseline_path


def _payload(page: int, *, has_more: bool, count: int = 5, offset: int | None = None) -> dict:
    return {
        "reports": [{"id": 500000 + page * 10 + index} for index in range(count)],
        "pagination": {
            "hasMore": has_more,
            "hasPrevious": page > 1,
            "limit": 5,
            "offset": (page - 1) * 5 if offset is None else offset,
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


def test_observes_terminal_bracket_without_opening_manifest_capture(tmp_path: Path) -> None:
    review_path, baseline_path = _packet(tmp_path)
    pages = (4, 8, 16)
    opener = _PageOpener(
        {
            4: _payload(4, has_more=True),
            8: _payload(8, has_more=True),
            16: _payload(16, has_more=False, count=2),
        }
    )
    private_output = tmp_path / "probe.private.json"
    receipt_output = tmp_path / "probe.json"

    receipt = capture_report_pagination_boundary_probe(
        _registry(),
        RawArchive(tmp_path / "raw"),
        semantic_review_path=review_path,
        baseline_private_path=baseline_path,
        private_output_path=private_output,
        receipt_output_path=receipt_output,
        probe_pages=pages,
        opener=opener,
    )

    assert opener.requested_pages == [4, 8, 16]
    assert receipt["boundary_observation"]["highest_more_pages_candidate"] == 8
    assert receipt["boundary_observation"]["lowest_terminal_candidate"] == 16
    assert receipt["summary"]["terminal_bracket_observed"] is True
    assert receipt["decision_boundary"]["ready_for_bounded_terminal_search"] is True
    assert receipt["decision_boundary"]["has_more_semantics_verified"] is False
    assert receipt["decision_boundary"]["ready_for_exhaustive_public_report_manifest_capture"] is False
    assert receipt["decision_boundary"]["ready_for_bis25_scoring"] is False

    source_ids = {
        500000 + page * 10 + index
        for page, count in ((4, 5), (8, 5), (16, 2))
        for index in range(count)
    }
    assert source_ids.isdisjoint(_integer_values(receipt))


def test_requests_larger_bounded_probe_when_no_false_candidate_is_observed(
    tmp_path: Path,
) -> None:
    review_path, baseline_path = _packet(tmp_path)
    opener = _PageOpener(
        {
            4: _payload(4, has_more=True),
            8: _payload(8, has_more=True),
        }
    )

    receipt = capture_report_pagination_boundary_probe(
        _registry(),
        RawArchive(tmp_path / "raw"),
        semantic_review_path=review_path,
        baseline_private_path=baseline_path,
        private_output_path=tmp_path / "probe.private.json",
        receipt_output_path=tmp_path / "probe.json",
        probe_pages=(4, 8),
        opener=opener,
    )

    assert receipt["summary"]["has_more_false_probe_page_count"] == 0
    assert receipt["summary"]["ready_for_larger_bounded_probe"] is True
    assert receipt["summary"]["ready_for_bounded_terminal_search"] is False


def test_rejects_baseline_private_changed_after_semantic_review(tmp_path: Path) -> None:
    review_path, baseline_path = _packet(tmp_path)
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    baseline["pages"][0]["pagination"]["hasMore"] = False
    _write(baseline_path, baseline)

    with pytest.raises(ValueError, match="hash changed"):
        capture_report_pagination_boundary_probe(
            _registry(),
            RawArchive(tmp_path / "raw"),
            semantic_review_path=review_path,
            baseline_private_path=baseline_path,
            private_output_path=tmp_path / "probe.private.json",
            receipt_output_path=tmp_path / "probe.json",
            probe_pages=(4, 8),
            opener=_PageOpener({}),
        )


def test_rejects_offset_relation_mismatch(tmp_path: Path) -> None:
    review_path, baseline_path = _packet(tmp_path)
    opener = _PageOpener(
        {
            4: _payload(4, has_more=True, offset=999),
            8: _payload(8, has_more=False),
        }
    )

    with pytest.raises(ValueError, match="offset relation failed"):
        capture_report_pagination_boundary_probe(
            _registry(),
            RawArchive(tmp_path / "raw"),
            semantic_review_path=review_path,
            baseline_private_path=baseline_path,
            private_output_path=tmp_path / "probe.private.json",
            receipt_output_path=tmp_path / "probe.json",
            probe_pages=(4, 8),
            opener=opener,
        )
