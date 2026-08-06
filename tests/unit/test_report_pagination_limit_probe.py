from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

from coa_workbench.collector import RawArchive, load_source_registry
from coa_workbench.collector.report_pagination_limit_probe import (
    capture_report_pagination_limit_probe,
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


class _LimitAwareOpener:
    def __init__(self) -> None:
        self.requests = []

    def __call__(self, request, **_kwargs):
        self.requests.append(request)
        query = parse_qs(urlsplit(request.full_url).query)
        page = int(query["page"][0])
        limit = int(query["limit"][0])
        first_id = page * 1_000_000
        payload = {
            "reports": [{"id": first_id + index} for index in range(limit)],
            "pagination": {
                "page": page,
                "limit": limit,
                "offset": (page - 1) * limit,
                "hasPrevious": page > 1,
                "hasMore": True,
            },
            "success": True,
        }
        return _Response(payload)


def _registry():
    return load_source_registry(Path("config/ascension_logs_sources.yaml"))


def _contains_key(value: object, key: str) -> bool:
    if isinstance(value, dict):
        return key in value or any(_contains_key(item, key) for item in value.values())
    if isinstance(value, list):
        return any(_contains_key(item, key) for item in value)
    return False


def test_limit_probe_selects_largest_observed_candidate_and_keeps_receipt_scalar_free(tmp_path):
    opener = _LimitAwareOpener()
    private_output = tmp_path / "limit-probe.private.json"
    receipt_output = tmp_path / "limit-probe.json"

    receipt = capture_report_pagination_limit_probe(
        _registry(),
        RawArchive(tmp_path / "raw"),
        private_output_path=private_output,
        receipt_output_path=receipt_output,
        candidates=(5, 25),
        opener=opener,
    )

    assert len(opener.requests) == 4
    assert receipt["summary"]["observed_supported_limit_count"] == 2
    assert receipt["summary"]["selected_limit_candidate"] == 25
    assert receipt["summary"]["larger_limit_candidate_observed"] is True
    assert receipt["decision_boundary"]["ready_for_manual_limit_promotion"] is True
    assert receipt["decision_boundary"]["production_manifest_limit_changed"] is False
    assert receipt["decision_boundary"]["ready_for_fast_manifest_capture"] is False
    assert receipt["summary"]["contains_source_scalar_values"] is False
    assert _contains_key(receipt, "source_report_ids") is False

    private = json.loads(private_output.read_text(encoding="utf-8"))
    assert private["result"]["selected_limit_candidate"] == 25
    assert _contains_key(private, "source_report_ids") is True
    assert json.loads(receipt_output.read_text(encoding="utf-8")) == receipt


def test_limit_probe_rejects_candidates_without_verified_control(tmp_path):
    with pytest.raises(ValueError, match="start with the verified control value 5"):
        capture_report_pagination_limit_probe(
            _registry(),
            RawArchive(tmp_path / "raw"),
            private_output_path=tmp_path / "private.json",
            receipt_output_path=tmp_path / "receipt.json",
            candidates=(25, 50),
            opener=_LimitAwareOpener(),
        )
