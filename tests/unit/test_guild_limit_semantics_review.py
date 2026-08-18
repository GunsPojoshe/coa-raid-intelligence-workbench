from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.collector.guild_limit_semantics_review import (
    review_guild_limit_semantics,
)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _copy_inputs(tmp_path: Path) -> tuple[Path, Path]:
    root = _project_root()
    capture_path = tmp_path / "argentum-guild-limit-semantics-capture.json"
    capture_path.write_bytes(
        (root / "evidence/real-data/argentum-guild-limit-semantics-capture.json").read_bytes()
    )
    route_path = tmp_path / "argentum-guild-route-semantics-review.json"
    route_path.write_bytes(
        (root / "evidence/real-data/argentum-guild-route-semantics-review.json").read_bytes()
    )
    return capture_path, route_path


def _review(tmp_path: Path, capture_path: Path, route_path: Path) -> dict[str, object]:
    return review_guild_limit_semantics(
        capture_path=capture_path,
        route_review_path=route_path,
        receipt_output_path=tmp_path / "review.json",
    )


def test_review_promotes_only_limit_truncation_semantics(tmp_path: Path) -> None:
    capture_path, route_path = _copy_inputs(tmp_path)

    receipt = _review(tmp_path, capture_path, route_path)

    summary = receipt["summary"]
    boundary = receipt["decision_boundary"]
    assert summary["all_integrity_checks_passed"] is True
    assert summary["integrity_check_count"] == 30
    assert summary["limit_truncation_semantics_verified"] is True
    assert summary["ready_for_bounded_pagination_semantics_capture"] is True
    assert summary["pagination_semantics_verified"] is False
    assert summary["termination_semantics_verified"] is False
    assert summary["completeness_verified"] is False
    assert summary["guild_api_route_semantics_verified"] is False
    assert boundary["automatic_full_guild_crawl_allowed"] is False
    assert boundary["ready_for_full_guild_crawl"] is False
    assert boundary["planner_scoring_allowed"] is False


def test_review_accepts_crlf_bound_route_review(tmp_path: Path) -> None:
    capture_path, route_path = _copy_inputs(tmp_path)
    body = route_path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    route_path.write_bytes(body)

    receipt = _review(tmp_path, capture_path, route_path)

    binding = receipt["source_binding_review"]
    assert binding["route_review_line_endings_normalized"] is False
    assert binding["semantic_document_identity_preserved"] is True


def test_route_review_hash_mismatch_blocks_review(tmp_path: Path) -> None:
    capture_path, route_path = _copy_inputs(tmp_path)
    route_path.write_bytes(route_path.read_bytes() + b" ")

    with pytest.raises(ValueError, match="route review SHA-256 mismatch"):
        _review(tmp_path, capture_path, route_path)


def test_high_limit_repeat_drift_blocks_review(tmp_path: Path) -> None:
    capture_path, route_path = _copy_inputs(tmp_path)
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    capture["attempts"][2]["shape_summary"]["ordered_record_set_sha256"] = "0" * 64
    capture_path.write_text(json.dumps(capture), encoding="utf-8")

    with pytest.raises(ValueError, match="high_limit_ordered_records_stable"):
        _review(tmp_path, capture_path, route_path)


def test_capture_privacy_violation_blocks_review(tmp_path: Path) -> None:
    capture_path, route_path = _copy_inputs(tmp_path)
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    capture["target"]["query_value_published"] = True
    capture_path.write_text(json.dumps(capture), encoding="utf-8")

    with pytest.raises(ValueError, match="query_value_published"):
        _review(tmp_path, capture_path, route_path)


def test_public_review_receipt_remains_scalar_free(tmp_path: Path) -> None:
    capture_path, route_path = _copy_inputs(tmp_path)

    receipt = _review(tmp_path, capture_path, route_path)
    public_text = (tmp_path / "review.json").read_text(encoding="utf-8")

    assert receipt["target"] == {
        "query_value_published": False,
        "request_urls_published": False,
        "source_guild_ids_published": False,
        "raw_records_published": False,
        "raw_payload_published": False,
    }
    assert '"contains_source_scalar_values": false' in public_text
    assert '"contains_query_values": false' in public_text
    assert '"planner_scoring_allowed": false' in public_text
