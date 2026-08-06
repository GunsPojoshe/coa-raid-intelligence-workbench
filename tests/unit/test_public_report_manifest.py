from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

from coa_workbench.collector import RawArchive, load_source_registry
from coa_workbench.collector.public_report_manifest import capture_public_report_manifest


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
    def __init__(
        self,
        payloads: dict[int, object],
        *,
        fail_page: int | None = None,
        fail_occurrence: int = 1,
    ) -> None:
        self.payloads = payloads
        self.fail_page = fail_page
        self.fail_occurrence = fail_occurrence
        self.requested_pages: list[int] = []
        self.page_counts: dict[int, int] = {}

    def __call__(self, request, **_kwargs):
        page = int(parse_qs(urlsplit(request.full_url).query)["page"][0])
        self.requested_pages.append(page)
        self.page_counts[page] = self.page_counts.get(page, 0) + 1
        if page == self.fail_page and self.page_counts[page] == self.fail_occurrence:
            raise OSError("synthetic interruption")
        payload = self.payloads[page]
        if callable(payload):
            payload = payload(self.page_counts[page])
        return _Response(payload)


def _write(path: Path, payload: object) -> bytes:
    body = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    path.write_bytes(body)
    return body


def _report(report_id: int, *, guild_id: int | None = None, guild_name: str | None = None) -> dict:
    return {
        "created_at": "2026-07-30T00:00:00Z",
        "end_time": "2026-07-30T00:30:00Z",
        "guild_id": guild_id,
        "guild_name": guild_name,
        "highest_difficulty": None,
        "id": report_id,
        "locations": [],
        "start_time": "2026-07-30T00:00:00Z",
        "title": f"Report {report_id}",
        "uploader_username": "tester",
        "visibility": "public",
    }


def _payload(page: int, reports: list[dict], *, terminal_page: int = 4) -> dict:
    return {
        "reports": reports,
        "pagination": {
            "hasMore": page < terminal_page,
            "hasPrevious": page > 1,
            "limit": 5,
            "offset": (page - 1) * 5,
            "page": page,
        },
        "success": True,
    }


def _payloads(*, duplicate: bool = False) -> dict[int, dict]:
    values: dict[int, dict] = {}
    next_id = 1000
    for page in (1, 2, 3):
        reports = []
        for index in range(5):
            report_id = next_id
            next_id += 1
            if duplicate and page == 2 and index == 0:
                report_id = 1000
            if page == 2 and index in (1, 2):
                reports.append(_report(report_id, guild_id=77, guild_name="Argentum"))
            else:
                reports.append(_report(report_id))
        values[page] = _payload(page, reports)
    values[4] = _payload(
        4,
        [
            _report(next_id, guild_id=77, guild_name="Argentum"),
            _report(next_id + 1),
        ],
    )
    values[5] = _payload(5, [])
    return values


def _packet(tmp_path: Path) -> tuple[Path, Path, Path]:
    terminal_private = {
        "schema_version": 1,
        "search_kind": "report_pagination_terminal_private_batch",
        "search_version": "report-pagination-terminal-search-v1",
        "generated_at": "2026-07-30T00:00:00Z",
        "target_guild_label": "Argentum",
        "request": {
            "route_template": "/api/reports/public",
            "initial_lower_bound": 2,
            "initial_upper_bound": 8,
            "limit": 5,
            "sort_by": "created_at",
            "sort_order": "desc",
            "http_profile_version": "coa-fetch-context-v1",
        },
        "pages": [
            {
                "phase": "final_predecessor",
                "page": 3,
                "limit": 5,
                "raw_id": "a" * 64,
                "observation_id": "b" * 64,
                "payload_hash": "c" * 64,
                "schema_fingerprint": "d" * 64,
                "source_report_ids": [1010, 1011, 1012, 1013, 1014],
                "pagination": {
                    "hasMore": True,
                    "hasPrevious": True,
                    "limit": 5,
                    "offset": 10,
                    "page": 3,
                },
                "report_count": 5,
            },
            {
                "phase": "final_terminal",
                "page": 4,
                "limit": 5,
                "raw_id": "e" * 64,
                "observation_id": "f" * 64,
                "payload_hash": "1" * 64,
                "schema_fingerprint": "2" * 64,
                "source_report_ids": [1015, 1016],
                "pagination": {
                    "hasMore": False,
                    "hasPrevious": True,
                    "limit": 5,
                    "offset": 15,
                    "page": 4,
                },
                "report_count": 2,
            },
            {
                "phase": "final_successor",
                "page": 5,
                "limit": 5,
                "raw_id": "3" * 64,
                "observation_id": "4" * 64,
                "payload_hash": "5" * 64,
                "schema_fingerprint": "6" * 64,
                "source_report_ids": [],
                "pagination": {
                    "hasMore": False,
                    "hasPrevious": True,
                    "limit": 5,
                    "offset": 20,
                    "page": 5,
                },
                "report_count": 0,
            },
        ],
        "summary": {
            "captured_page_count": 3,
            "report_occurrence_count": 7,
            "unique_report_id_count": 7,
            "contains_source_scalar_values": True,
        },
    }
    private_path = tmp_path / "terminal.private.json"
    private_body = _write(private_path, terminal_private)

    terminal_receipt = {
        "schema_version": 1,
        "search_kind": "report_pagination_terminal_search",
        "search_version": "report-pagination-terminal-search-v1",
        "generated_at": "2026-07-30T00:00:01Z",
        "source_private_search_name": private_path.name,
        "source_private_search_sha256": hashlib.sha256(private_body).hexdigest(),
        "target": {
            "guild_label": "Argentum",
            "guild_identity_status": "operator_named_target_unresolved",
        },
        "request": {
            "route_template": "/api/reports/public",
            "initial_lower_bound": 2,
            "initial_upper_bound": 8,
            "limit": 5,
            "sort_by": "created_at",
            "sort_order": "desc",
            "http_profile_version": "coa-fetch-context-v1",
            "max_requests": 16,
        },
        "terminal_contract": {
            "status": "verified_adjacent_transition",
            "strategy": "request_pages_1_through_terminal_page_inclusive",
            "deduplication_key": "/reports/*/id",
            "inclusive_terminal_page": True,
            "predecessor_page": 3,
            "terminal_page": 4,
            "successor_page": 5,
            "terminal_page_report_count": 2,
            "automatic_network_collection_allowed": False,
        },
        "decision_boundary": {
            "status": "pagination_terminal_contract_verified",
            "page_semantics_verified": True,
            "page_size_semantics_verified": True,
            "offset_semantics_verified": True,
            "has_previous_semantics_verified": True,
            "has_more_semantics_verified": True,
            "termination_condition_verified": True,
            "terminal_page_verified": True,
            "ready_for_exhaustive_public_report_manifest_capture": True,
            "automatic_full_manifest_collection_allowed": False,
            "ready_for_full_guild_crawl": False,
            "ready_for_guild_identity_review": False,
            "ready_for_guild_filtering": False,
            "ready_for_multi_report_character_graph": False,
            "ready_for_performance_model": False,
            "ready_for_global_benchmark": False,
            "ready_for_bis25_scoring": False,
            "planner_scoring_allowed": False,
            "private_search_contains_source_scalar_values": True,
        },
        "summary": {
            "all_integrity_checks_passed": True,
            "completed_request_count": 6,
            "terminal_page": 4,
            "terminal_page_report_count": 2,
            "private_search_contains_source_scalar_values": True,
            "contains_source_scalar_values": False,
            "ready_for_exhaustive_public_report_manifest_capture": True,
            "ready_for_full_guild_crawl": False,
            "ready_for_bis25_scoring": False,
        },
    }
    receipt_path = tmp_path / "terminal.json"
    _write(receipt_path, terminal_receipt)

    mapping = {
        "mapping_schema_version": 1,
        "mapping_id": "coa-public-report-discovery-v1",
        "status": "verified",
        "route_template": "/api/reports/public",
        "collection": {
            "path": "/reports/*",
            "required_keys": sorted(
                {
                    "created_at",
                    "end_time",
                    "guild_id",
                    "guild_name",
                    "highest_difficulty",
                    "id",
                    "locations",
                    "start_time",
                    "title",
                    "uploader_username",
                    "visibility",
                }
            ),
            "fields": {
                "source_report_id": {},
                "title": {},
                "created_at": {},
                "start_time": {},
                "end_time": {},
                "visibility": {},
                "uploader_username": {},
            },
        },
    }
    mapping_path = tmp_path / "mapping.json"
    _write(mapping_path, mapping)
    return receipt_path, private_path, mapping_path


def _registry():
    return load_source_registry(Path("config/ascension_logs_sources.yaml"))


def _capture(
    tmp_path: Path,
    opener: _PageOpener,
    *,
    resume: bool = True,
) -> dict:
    receipt_path, private_path, mapping_path = _packet(tmp_path)
    return capture_public_report_manifest(
        _registry(),
        RawArchive(tmp_path / "raw"),
        terminal_receipt_path=receipt_path,
        terminal_private_path=private_path,
        mapping_path=mapping_path,
        checkpoint_path=tmp_path / "manifest.checkpoint.json",
        private_output_path=tmp_path / "manifest.private.json",
        receipt_output_path=tmp_path / "manifest.json",
        request_delay_seconds=0,
        resume=resume,
        opener=opener,
    )


def test_captures_complete_unique_manifest_and_opens_guild_identity_review(tmp_path: Path) -> None:
    receipt = _capture(tmp_path, _PageOpener(_payloads()))

    assert receipt["summary"]["completed_page_count"] == 4
    assert receipt["summary"]["report_occurrence_count"] == 17
    assert receipt["summary"]["unique_report_id_count"] == 17
    assert receipt["summary"]["duplicate_report_occurrence_count"] == 0
    assert receipt["guild_field_summary"]["target_label_exact_match_report_count"] == 3
    assert receipt["guild_field_summary"]["target_label_distinct_non_null_guild_id_count"] == 1
    assert receipt["decision_boundary"]["ready_for_guild_identity_review"] is True
    assert receipt["decision_boundary"]["ready_for_guild_filtering"] is False
    assert receipt["decision_boundary"]["ready_for_bis25_scoring"] is False
    assert receipt["sentinel_summary"]["all_start_end_payload_hashes_equal"] is True


def test_rejects_cross_page_duplicate_report_ids(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="cross-page duplicate"):
        _capture(tmp_path, _PageOpener(_payloads(duplicate=True)))


def test_rejects_sentinel_payload_drift(tmp_path: Path) -> None:
    payloads = _payloads()
    stable_page_one = payloads[1]
    drifted_page_one = _payload(
        1,
        [
            _report(9000),
            _report(9001),
            _report(9002),
            _report(9003),
            _report(9004),
        ],
    )
    payloads[1] = lambda occurrence: drifted_page_one if occurrence >= 3 else stable_page_one

    with pytest.raises(ValueError, match="sentinel payload changed"):
        _capture(tmp_path, _PageOpener(payloads))


def test_resumes_from_checkpoint_after_interruption(tmp_path: Path) -> None:
    receipt_path, private_path, mapping_path = _packet(tmp_path)
    checkpoint_path = tmp_path / "manifest.checkpoint.json"
    first_opener = _PageOpener(_payloads(), fail_page=3, fail_occurrence=2)

    with pytest.raises(ValueError, match="capture was incomplete"):
        capture_public_report_manifest(
            _registry(),
            RawArchive(tmp_path / "raw"),
            terminal_receipt_path=receipt_path,
            terminal_private_path=private_path,
            mapping_path=mapping_path,
            checkpoint_path=checkpoint_path,
            private_output_path=tmp_path / "manifest.private.json",
            receipt_output_path=tmp_path / "manifest.json",
            request_delay_seconds=0,
            retry_count=0,
            opener=first_opener,
        )

    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    assert sorted(checkpoint["pages"]) == ["1", "2"]

    second_opener = _PageOpener(_payloads())
    receipt = capture_public_report_manifest(
        _registry(),
        RawArchive(tmp_path / "raw"),
        terminal_receipt_path=receipt_path,
        terminal_private_path=private_path,
        mapping_path=mapping_path,
        checkpoint_path=checkpoint_path,
        private_output_path=tmp_path / "manifest.private.json",
        receipt_output_path=tmp_path / "manifest.json",
        request_delay_seconds=0,
        opener=second_opener,
    )

    assert receipt["summary"]["report_occurrence_count"] == 17
    assert receipt["summary"]["resume_checkpoint_used"] is True
    assert second_opener.requested_pages[:2] == [3, 4]
