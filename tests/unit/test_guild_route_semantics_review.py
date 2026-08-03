from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from coa_workbench.collector.guild_route_semantics_review import (
    review_guild_route_semantics,
)


def _body(payload: object) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _contract() -> dict[str, object]:
    return {
        "schema_version": 1,
        "contract_kind": "guild_full_crawl_collection_contract",
        "contract_version": "guild-full-crawl-contract-v1",
        "target": {
            "guild_label": "Argentum",
            "source_guild_id_published": False,
            "report_ids_published": False,
        },
        "summary": {
            "all_integrity_checks_passed": True,
            "contains_source_scalar_values": False,
            "full_crawl_collection_contract_reviewed": True,
            "ready_for_bounded_route_semantics_capture": True,
        },
        "decision_boundary": {
            "automatic_full_guild_crawl_allowed": False,
            "guild_api_route_semantics_verified": False,
            "ready_for_full_guild_crawl": False,
            "planner_scoring_allowed": False,
        },
    }


def _access() -> dict[str, object]:
    return {
        "schema_version": 1,
        "diagnostic_kind": "guild_identity_search_access_diagnostic",
        "diagnostic_version": "guild-identity-search-access-diagnostic-v1",
        "target": {
            "guild_label": "Argentum",
            "request_url_published": False,
            "source_guild_id_published": False,
        },
        "summary": {
            "all_integrity_checks_passed": True,
            "selected_access_profile": "spa_fetch_context",
            "contains_source_scalar_values": False,
        },
        "decision_boundary": {
            "ready_for_profiled_guild_search_probe": True,
            "selected_access_profile": "spa_fetch_context",
            "guild_api_route_semantics_verified": False,
            "ready_for_full_guild_crawl": False,
            "planner_scoring_allowed": False,
        },
    }


def _shape() -> dict[str, object]:
    return {
        "contains_source_scalar_values": False,
        "distinct_non_null_id_count": 1,
        "guild_collection_observed": True,
        "guild_field_inventory": [
            {"field": "id", "types": ["integer"]},
            {"field": "name", "types": ["string"]},
            {"field": "realm", "types": ["string"]},
            {"field": "report_count", "types": ["string"]},
        ],
        "guild_field_inventory_sha256": "1" * 64,
        "guild_object_count": 1,
        "guild_result_count": 1,
        "id_value_set_sha256": "2" * 64,
        "ordered_guild_records_sha256": "3" * 64,
        "pagination_field_types": [],
        "pagination_keys": [],
        "pagination_object_observed": False,
        "target_name_casefold_match_count": 1,
        "top_level_keys": ["guilds", "success"],
        "top_level_kind": "object",
    }


def _attempt(case: str, query_keys: list[str], limit: int | None, seed: str) -> dict[str, object]:
    return {
        "body_bytes": 93,
        "body_captured": True,
        "capture": {
            "bytes_uncompressed": 93,
            "observation_id": seed * 64,
            "payload_hash": "4" * 64,
            "raw_id": seed * 64,
            "schema_fingerprint": "5" * 64,
        },
        "case": case,
        "contains_error_text": False,
        "contains_source_scalar_values": False,
        "content_type": "application/json",
        "failure_class": None,
        "http_status": 200,
        "json_valid": True,
        "limit": limit,
        "query_keys": query_keys,
        "response_candidate": True,
        "return_code": 0,
        "route_template": "/api/guilds/search",
        "shape_summary": _shape(),
    }


def _capture(contract_path: Path, contract_body: bytes, access_path: Path, access_body: bytes) -> dict[str, object]:
    return {
        "schema_version": 1,
        "capture_kind": "guild_route_semantics_capture",
        "capture_version": "guild-route-semantics-capture-v1",
        "source_contract_name": contract_path.name,
        "source_contract_sha256": _sha256(contract_body),
        "source_public_access_name": access_path.name,
        "source_public_access_sha256": _sha256(access_body),
        "source_private_capture_name": "capture.private.json",
        "source_private_capture_sha256": "6" * 64,
        "target": {
            "guild_label": "Argentum",
            "report_ids_published": False,
            "request_urls_published": False,
            "source_guild_id_published": False,
        },
        "request_contract": {
            "case_count": 3,
            "credentials_supplied": False,
            "observed_query_shapes": [["q", "limit"], ["q"]],
            "redirects_allowed": False,
            "route_template": "/api/guilds/search",
            "selected_profile": "spa_fetch_context",
        },
        "attempts": [
            _attempt("exact_label_limit_1", ["q", "limit"], 1, "a"),
            _attempt("exact_label_limit_reviewed", ["q", "limit"], 25, "b"),
            _attempt("exact_label_without_limit", ["q"], None, "c"),
        ],
        "cross_case_review": {
            "all_responses_completed": True,
            "contains_source_scalar_values": False,
            "guild_collection_observed_on_all_cases": True,
            "limit_parameter_accepted": True,
            "limit_truncation_semantics_verified": False,
            "pagination_object_observed": False,
            "pagination_semantics_verified": False,
            "response_shape_consistent": True,
            "route_shapes_observed": True,
            "source_id_set_stable_by_hash": True,
            "target_name_casefold_match_stable": True,
        },
        "summary": {
            "all_integrity_checks_passed": True,
            "all_responses_completed": True,
            "attempt_count": 3,
            "completed_attempt_count": 3,
            "contains_raw_payload": False,
            "contains_source_scalar_values": False,
            "guild_api_route_semantics_verified": False,
            "planner_scoring_allowed": False,
            "ready_for_full_guild_crawl": False,
            "ready_for_route_semantics_review": True,
            "response_shape_consistent": True,
        },
    }


def _write_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    contract_path = tmp_path / "contract.json"
    contract_body = _body(_contract())
    contract_path.write_bytes(contract_body)

    access_path = tmp_path / "access.json"
    access_body = _body(_access())
    access_path.write_bytes(access_body)

    capture_path = tmp_path / "capture.json"
    capture_path.write_bytes(_body(_capture(contract_path, contract_body, access_path, access_body)))
    return capture_path, contract_path, access_path


def _review(tmp_path: Path, capture_path: Path, contract_path: Path, access_path: Path) -> dict[str, object]:
    return review_guild_route_semantics(
        capture_path=capture_path,
        full_crawl_contract_path=contract_path,
        public_access_diagnostic_path=access_path,
        receipt_output_path=tmp_path / "review.json",
    )


def test_review_promotes_only_route_shape_and_schema(tmp_path: Path) -> None:
    capture_path, contract_path, access_path = _write_inputs(tmp_path)

    receipt = _review(tmp_path, capture_path, contract_path, access_path)

    summary = receipt["summary"]
    boundary = receipt["decision_boundary"]
    assert summary["all_integrity_checks_passed"] is True
    assert summary["route_shape_and_response_schema_reviewed"] is True
    assert summary["ready_for_bounded_limit_semantics_capture"] is True
    assert summary["limit_truncation_semantics_verified"] is False
    assert summary["pagination_semantics_verified"] is False
    assert summary["guild_api_route_semantics_verified"] is False
    assert boundary["ready_for_full_guild_crawl"] is False
    assert boundary["planner_scoring_allowed"] is False

    public_text = (tmp_path / "review.json").read_text(encoding="utf-8")
    assert '"contains_source_scalar_values": false' in public_text
    assert '"source_guild_id_published": false' in public_text


def test_contract_hash_mismatch_blocks_review(tmp_path: Path) -> None:
    capture_path, contract_path, access_path = _write_inputs(tmp_path)
    contract_path.write_text("{}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="contract"):
        _review(tmp_path, capture_path, contract_path, access_path)


def test_schema_drift_blocks_review(tmp_path: Path) -> None:
    capture_path, contract_path, access_path = _write_inputs(tmp_path)
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    capture["attempts"][1]["shape_summary"]["guild_field_inventory"][3]["types"] = [
        "integer"
    ]
    capture_path.write_bytes(_body(capture))

    with pytest.raises(ValueError, match="field inventory mismatch"):
        _review(tmp_path, capture_path, contract_path, access_path)


def test_capture_cannot_pre_enable_full_crawl(tmp_path: Path) -> None:
    capture_path, contract_path, access_path = _write_inputs(tmp_path)
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    capture["summary"]["ready_for_full_guild_crawl"] = True
    capture_path.write_bytes(_body(capture))

    with pytest.raises(ValueError, match="full-crawl readiness"):
        _review(tmp_path, capture_path, contract_path, access_path)
