from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from coa_workbench.collector.report_pagination_semantic_review import (
    review_report_pagination_semantics,
)


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _shape(value: object) -> object:
    if isinstance(value, dict):
        return {
            "type": "object",
            "fields": {str(key): _shape(value[key]) for key in sorted(value)},
        }
    if isinstance(value, list):
        item_shapes: list[object] = []
        for item in value[:25]:
            candidate = _shape(item)
            if candidate not in item_shapes:
                item_shapes.append(candidate)
        return {"type": "array", "item_shapes": item_shapes}
    if value is None:
        kind = "null"
    elif isinstance(value, bool):
        kind = "boolean"
    elif isinstance(value, int):
        kind = "integer"
    elif isinstance(value, float):
        kind = "number"
    else:
        kind = "string"
    return {"type": kind}


def _write(path: Path, payload: object) -> bytes:
    body = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    path.write_bytes(body)
    return body


def _packet(tmp_path: Path, *, ambiguous_current_page: bool = False) -> tuple[Path, Path]:
    private_pages = []
    receipt_pages = []
    for page in (1, 2, 3):
        report_ids = [page * 100 + offset for offset in range(1, 6)]
        pagination = {
            "current_page": page,
            "has_more": True,
            "last_page": 9,
            "per_page": 5,
            "total": 42,
        }
        if ambiguous_current_page:
            pagination["mirror_page"] = page
        raw_id = f"{page:064x}"
        observation_id = f"{page + 10:064x}"
        payload_hash = f"{page + 20:064x}"
        schema_fingerprint = f"{page + 30:064x}"
        shape_hash = _sha256_json(_shape(pagination))
        report_hash = _sha256_json(sorted(report_ids))
        private_pages.append(
            {
                "page": page,
                "limit": 5,
                "raw_id": raw_id,
                "observation_id": observation_id,
                "payload_hash": payload_hash,
                "schema_fingerprint": schema_fingerprint,
                "source_report_ids": report_ids,
                "pagination": pagination,
                "pagination_shape": _shape(pagination),
                "top_level_keys": ["pagination", "reports", "success"],
                "report_count": 5,
                "duplicate_within_page_count": 0,
                "duplicate_with_prior_pages_count": 0,
            }
        )
        receipt_pages.append(
            {
                "page": page,
                "limit": 5,
                "http_status": 200,
                "raw_id": raw_id,
                "observation_id": observation_id,
                "payload_hash": payload_hash,
                "schema_fingerprint": schema_fingerprint,
                "report_occurrence_count": 5,
                "unique_report_id_count": 5,
                "duplicate_within_page_count": 0,
                "duplicate_with_prior_pages_count": 0,
                "report_id_set_sha256": report_hash,
                "pagination_shape_sha256": shape_hash,
                "pagination_direct_field_count": len(pagination),
                "top_level_keys": ["pagination", "reports", "success"],
            }
        )

    private = {
        "schema_version": 1,
        "evidence_kind": "bounded_report_pagination_private_batch",
        "evidence_version": "report-pagination-evidence-v1",
        "generated_at": "2026-07-29T23:52:57Z",
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
        "pages": private_pages,
        "summary": {
            "captured_page_count": 3,
            "report_occurrence_count": 15,
            "unique_report_id_count": 15,
            "duplicate_report_occurrence_count": 0,
            "empty_page_count": 0,
            "contains_source_scalar_values": True,
        },
    }
    private_path = tmp_path / "pagination.private.json"
    private_body = _write(private_path, private)

    receipt = {
        "schema_version": 1,
        "evidence_kind": "bounded_report_pagination_evidence",
        "evidence_version": "report-pagination-evidence-v1",
        "generated_at": "2026-07-29T23:52:57Z",
        "source_contract_name": "argentum-guild-report-collection-contract.json",
        "source_contract_sha256": "a" * 64,
        "source_private_evidence_name": private_path.name,
        "source_private_evidence_sha256": hashlib.sha256(private_body).hexdigest(),
        "target": {
            "guild_label": "Argentum",
            "guild_identity_status": "operator_named_target_unresolved",
        },
        "request": {
            "route_template": "/api/reports/public",
            "query_keys": ["page", "limit", "sortBy", "sortOrder"],
            "start_page": 1,
            "page_count": 3,
            "limit": 5,
            "sort_by": "created_at",
            "sort_order": "desc",
            "http_profile_version": "coa-fetch-context-v1",
        },
        "pages": receipt_pages,
        "integrity_checks": {"all_pages_completed": True},
        "decision_boundary": {
            "status": "bounded_pagination_evidence_captured",
            "automatic_termination_used": False,
            "pagination_field_semantics_verified": False,
            "termination_condition_verified": False,
            "ready_for_manual_pagination_field_review": True,
            "ready_for_full_guild_crawl": False,
            "ready_for_guild_filtering": False,
            "ready_for_multi_report_character_graph": False,
            "ready_for_performance_model": False,
            "ready_for_global_benchmark": False,
            "ready_for_bis25_scoring": False,
            "planner_scoring_allowed": False,
        },
        "summary": {
            "requested_page_count": 3,
            "completed_page_count": 3,
            "report_occurrence_count": 15,
            "unique_report_id_count": 15,
            "duplicate_report_occurrence_count": 0,
            "empty_page_count": 0,
            "distinct_pagination_shape_count": 1,
            "all_pages_same_pagination_shape": True,
            "all_integrity_checks_passed": True,
            "contains_source_scalar_values": False,
            "private_evidence_contains_source_scalar_values": True,
            "ready_for_manual_pagination_field_review": True,
            "ready_for_full_guild_crawl": False,
            "ready_for_bis25_scoring": False,
        },
    }
    receipt_path = tmp_path / "pagination.json"
    _write(receipt_path, receipt)
    return receipt_path, private_path


def test_reviews_unique_pagination_relations_without_source_values(tmp_path: Path) -> None:
    receipt_path, private_path = _packet(tmp_path)

    review = review_report_pagination_semantics(receipt_path, private_path)

    assignments = review["semantic_assignments"]
    assert assignments["current_page_field"] == "current_page"
    assert assignments["page_size_field"] == "per_page"
    assert assignments["total_record_count_field"] == "total"
    assert assignments["total_page_count_field"] == "last_page"
    assert assignments["has_next_page_field"] == "has_more"
    assert review["summary"]["relationship_verified_field_count"] == 5
    assert review["summary"]["termination_condition_verified"] is True
    assert review["decision_boundary"]["ready_for_exhaustive_public_report_manifest_capture"] is True
    assert review["decision_boundary"]["ready_for_full_guild_crawl"] is False
    assert review["decision_boundary"]["ready_for_bis25_scoring"] is False
    serialized = json.dumps(review, ensure_ascii=False)
    assert "101" not in serialized
    assert "42" not in serialized


def test_keeps_termination_unresolved_when_current_page_relation_is_ambiguous(
    tmp_path: Path,
) -> None:
    receipt_path, private_path = _packet(tmp_path, ambiguous_current_page=True)

    review = review_report_pagination_semantics(receipt_path, private_path)

    assert review["semantic_assignments"]["current_page_candidate_count"] == 2
    assert review["semantic_assignments"]["current_page_field"] is None
    assert review["summary"]["pagination_field_semantics_verified"] is False
    assert review["summary"]["termination_condition_verified"] is False
    assert review["decision_boundary"]["ready_for_exhaustive_public_report_manifest_capture"] is False


def test_rejects_private_batch_changed_after_capture(tmp_path: Path) -> None:
    receipt_path, private_path = _packet(tmp_path)
    private = json.loads(private_path.read_text(encoding="utf-8"))
    private["pages"][0]["pagination"]["total"] = 43
    _write(private_path, private)

    with pytest.raises(ValueError, match="hash changed"):
        review_report_pagination_semantics(receipt_path, private_path)


def test_rejects_report_identity_hash_mismatch(tmp_path: Path) -> None:
    receipt_path, private_path = _packet(tmp_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["pages"][1]["report_id_set_sha256"] = "f" * 64
    _write(receipt_path, receipt)

    with pytest.raises(ValueError, match="report id hash mismatch"):
        review_report_pagination_semantics(receipt_path, private_path)
