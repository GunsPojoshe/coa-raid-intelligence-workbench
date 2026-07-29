from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

from coa_workbench.collector import RawArchive, load_source_registry
from coa_workbench.collector.report_pagination_evidence import (
    capture_bounded_report_pagination_evidence,
)


class _Headers:
    def get_content_type(self) -> str:
        return "application/json"


class _Response:
    def __init__(self, body: bytes) -> None:
        self.status = 200
        self.headers = _Headers()
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self, size: int = -1) -> bytes:
        if size is None or size < 0:
            return self._body
        return self._body[:size]


class _PageOpener:
    def __init__(self, pages: dict[int, object]) -> None:
        self.pages = pages
        self.requested_pages: list[int] = []

    def __call__(self, request, **_kwargs):
        query = parse_qs(urlsplit(request.full_url).query)
        page = int(query["page"][0])
        self.requested_pages.append(page)
        payload = self.pages[page]
        return _Response(json.dumps(payload).encode("utf-8"))


def _registry():
    return load_source_registry(Path("config/ascension_logs_sources.yaml"))


def _contract_path() -> Path:
    return Path("evidence/real-data/argentum-guild-report-collection-contract.json")


def _report(source_report_id: int) -> dict[str, object]:
    return {
        "id": source_report_id,
        "title": f"Private report {source_report_id}",
        "created_at": "2026-07-29T00:00:00Z",
        "start_time": "2026-07-29T00:00:00Z",
        "end_time": "2026-07-29T01:00:00Z",
        "visibility": "public",
        "uploader_username": "Private uploader",
        "guild_id": None,
        "guild_name": None,
        "highest_difficulty": None,
        "locations": [],
    }


def _page(page: int, report_ids: list[int], *, pages: int = 3) -> dict[str, object]:
    return {
        "pagination": {
            "page": page,
            "pages": pages,
            "has_next": page < pages,
        },
        "reports": [_report(source_report_id) for source_report_id in report_ids],
        "success": True,
    }


def _capture(tmp_path: Path, opener: _PageOpener) -> tuple[dict[str, object], Path, Path]:
    private_path = tmp_path / "pagination.private.json"
    receipt_path = tmp_path / "pagination.receipt.json"
    receipt = capture_bounded_report_pagination_evidence(
        _registry(),
        RawArchive(tmp_path / "raw"),
        contract_path=_contract_path(),
        private_output_path=private_path,
        receipt_output_path=receipt_path,
        opener=opener,
    )
    return receipt, private_path, receipt_path


def test_captures_three_pages_and_measures_cross_page_duplicates(tmp_path: Path) -> None:
    opener = _PageOpener(
        {
            1: _page(1, [101, 102, 103, 104, 105]),
            2: _page(2, [105, 106, 107, 108, 109]),
            3: _page(3, [110, 111]),
        }
    )

    receipt, private_path, receipt_path = _capture(tmp_path, opener)

    assert opener.requested_pages == [1, 2, 3]
    assert receipt["evidence_kind"] == "bounded_report_pagination_evidence"
    assert receipt["summary"]["completed_page_count"] == 3
    assert receipt["summary"]["report_occurrence_count"] == 12
    assert receipt["summary"]["unique_report_id_count"] == 11
    assert receipt["summary"]["duplicate_report_occurrence_count"] == 1
    assert receipt["summary"]["empty_page_count"] == 0
    assert receipt["summary"]["all_pages_same_pagination_shape"] is True
    assert receipt["summary"]["all_integrity_checks_passed"] is True
    assert receipt["decision_boundary"]["ready_for_manual_pagination_field_review"] is True
    assert receipt["decision_boundary"]["termination_condition_verified"] is False
    assert receipt["decision_boundary"]["ready_for_full_guild_crawl"] is False
    assert receipt["decision_boundary"]["ready_for_bis25_scoring"] is False
    assert receipt["decision_boundary"]["planner_scoring_allowed"] is False

    private_payload = json.loads(private_path.read_text(encoding="utf-8"))
    assert private_payload["pages"][0]["source_report_ids"] == [101, 102, 103, 104, 105]
    assert private_payload["pages"][1]["pagination"]["page"] == 2
    assert private_payload["summary"]["contains_source_scalar_values"] is True

    safe_payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    serialized = json.dumps(safe_payload, ensure_ascii=False)
    assert "source_report_ids" not in serialized
    assert "Private report" not in serialized
    assert "Private uploader" not in serialized
    assert safe_payload["summary"]["contains_source_scalar_values"] is False


def test_explicit_window_does_not_stop_after_an_empty_page(tmp_path: Path) -> None:
    opener = _PageOpener(
        {
            1: _page(1, [201, 202]),
            2: _page(2, []),
            3: _page(3, [203]),
        }
    )

    receipt, _private_path, _receipt_path = _capture(tmp_path, opener)

    assert opener.requested_pages == [1, 2, 3]
    assert receipt["summary"]["empty_page_count"] == 1
    assert receipt["summary"]["report_occurrence_count"] == 3
    assert receipt["decision_boundary"]["automatic_termination_used"] is False


def test_rejects_contract_that_opens_full_guild_crawl(tmp_path: Path) -> None:
    contract = json.loads(_contract_path().read_text(encoding="utf-8"))
    contract["decision_boundary"]["ready_for_full_guild_crawl"] = True
    stale_contract = tmp_path / "stale-contract.json"
    stale_contract.write_text(json.dumps(contract), encoding="utf-8")

    with pytest.raises(ValueError, match="ready_for_full_guild_crawl"):
        capture_bounded_report_pagination_evidence(
            _registry(),
            RawArchive(tmp_path / "raw"),
            contract_path=stale_contract,
            private_output_path=tmp_path / "private.json",
            receipt_output_path=tmp_path / "receipt.json",
            opener=_PageOpener({1: _page(1, []), 2: _page(2, []), 3: _page(3, [])}),
        )


def test_rejects_page_without_pagination_object(tmp_path: Path) -> None:
    bad_page = _page(2, [301])
    bad_page.pop("pagination")
    opener = _PageOpener(
        {
            1: _page(1, [300]),
            2: bad_page,
            3: _page(3, [302]),
        }
    )

    with pytest.raises(ValueError, match="pagination"):
        _capture(tmp_path, opener)


@pytest.mark.parametrize("page_count", [1, 6])
def test_rejects_unbounded_page_count(tmp_path: Path, page_count: int) -> None:
    with pytest.raises(ValueError, match="between 2 and 5"):
        capture_bounded_report_pagination_evidence(
            _registry(),
            RawArchive(tmp_path / "raw"),
            contract_path=_contract_path(),
            private_output_path=tmp_path / "private.json",
            receipt_output_path=tmp_path / "receipt.json",
            page_count=page_count,
            opener=_PageOpener({}),
        )
