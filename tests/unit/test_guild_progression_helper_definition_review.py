from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from coa_workbench.collector.guild_progression_helper_definition_review import (
    review_guild_progression_helper_definition,
)


def _write(path: Path, payload: object) -> bytes:
    body = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return body


def _callsite_review() -> dict[str, object]:
    false_gates = {
        "ready_for_bounded_progression_route_probe": False,
        "guild_api_route_semantics_verified": False,
        "pagination_semantics_verified": False,
        "termination_semantics_verified": False,
        "completeness_verified": False,
        "ready_for_full_guild_crawl": False,
        "planner_scoring_allowed": False,
    }
    return {
        "schema_version": 1,
        "review_kind": "guild_progression_helper_callsite_review",
        "review_version": "guild-progression-helper-callsite-review-v1",
        "integrity_checks": {f"check_{index}": True for index in range(36)},
        "summary": {
            "all_integrity_checks_passed": True,
            "integrity_check_count": 36,
            "guild_progression_helper_callsite_reviewed": True,
            "method_candidate_unambiguous": True,
            "http_method_candidate": "POST",
            "actual_helper_invocation_candidate_observed": True,
            "helper_identity_resolved": False,
            "request_payload_mapping_resolved": False,
            "request_shape_sufficient_for_bounded_probe": False,
            "ready_for_guild_progression_helper_definition_inventory": True,
            **false_gates,
            "contains_raw_callee": False,
            "contains_raw_context": False,
            "contains_source_scalar_values": False,
        },
    }


def _inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    root = Path(__file__).resolve().parents[2]
    public = json.loads(
        (
            root
            / "evidence/real-data/argentum-guild-progression-helper-definition.json"
        ).read_text(encoding="utf-8")
    )
    callsite_path = tmp_path / "argentum-guild-progression-callsite-review.json"
    callsite_body = _write(callsite_path, _callsite_review())

    callee = "client.helper"
    callee_hash = hashlib.sha256(callee.encode()).hexdigest()
    span = "helper(x){return x&&x.value?x.value:0; }"
    assert len(span) == 40
    span_hash = hashlib.sha256(span.encode()).hexdigest()
    excerpt = (
        "const endpoint='/api/guilds/progression';"
        "client.helper;const client={"
        f"{span}"
        "};"
    )
    private = {
        "schema_version": 1,
        "inventory_kind": "guild_progression_helper_definition_inventory_private",
        "inventory_version": "guild-progression-helper-definition-inventory-v1",
        "generated_at": "2026-08-04T17:40:56Z",
        "route": "/api/guilds/progression",
        "callee": callee,
        "callee_sha256": callee_hash,
        "definition_candidates": [
            {
                "candidate_index": 1,
                "kind": "method_definition",
                "binding_scope": "terminal_symbol",
                "start": 100,
                "end": 140,
                "span": span,
                "span_sha256": span_hash,
                "character_count": 40,
                "prefix_sha256": span_hash,
                "parameter_count": 1,
                "async_candidate": False,
                "marker_classes": [],
                "alias_target": None,
                "alias_target_sha256": None,
                "private_excerpt": excerpt,
                "private_excerpt_start": 0,
                "private_excerpt_end": len(excerpt),
            }
        ],
        "summary": {
            "full_chain_occurrence_count_observed": 2,
            "full_chain_occurrence_scan_truncated": False,
            "terminal_symbol_occurrence_count_observed": 31,
            "terminal_symbol_occurrence_scan_truncated": False,
            "definition_candidate_count": 1,
            "definition_candidate_scan_truncated": False,
            "definition_kinds": ["method_definition"],
            "binding_scopes": ["terminal_symbol"],
            "alias_candidate_count": 0,
            "marker_classes": [],
            "contains_source_scalar_values": True,
            "network_requests_performed": False,
        },
    }
    private_path = (
        tmp_path / "argentum-guild-progression-helper-definition.private.json"
    )
    private_body = _write(private_path, private)

    public["source_callsite_review_name"] = callsite_path.name
    public["source_callsite_review_sha256"] = hashlib.sha256(callsite_body).hexdigest()
    public["source_private_inventory_name"] = private_path.name
    public["source_private_inventory_sha256"] = hashlib.sha256(private_body).hexdigest()
    public["target"]["callee_sha256"] = callee_hash
    candidate = public["definition_candidates"][0]
    candidate["definition_span_sha256"] = span_hash
    candidate["definition_prefix_sha256"] = span_hash
    inventory_path = tmp_path / "public-inventory.json"
    _write(inventory_path, public)
    return inventory_path, private_path, callsite_path


def _review(
    tmp_path: Path,
    inventory_path: Path,
    private_path: Path,
    callsite_path: Path,
) -> dict[str, object]:
    return review_guild_progression_helper_definition(
        inventory_path=inventory_path,
        private_inventory_path=private_path,
        callsite_review_path=callsite_path,
        receipt_output_path=tmp_path / "review.json",
    )


def test_terminal_method_review_keeps_probe_blocked(tmp_path: Path) -> None:
    inventory, private, callsite = _inputs(tmp_path)
    receipt = _review(tmp_path, inventory, private, callsite)

    review = receipt["helper_definition_review"]
    candidate = receipt["candidate_reviews"][0]
    assert review["candidate_count"] == 1
    assert review["direct_transport_semantics_observed"] is False
    assert review["request_shape_semantics_observed"] is False
    assert review["blockers"] == [
        "terminal_symbol_only_definition",
        "transport_semantics_not_observed",
        "receiver_or_alias_ownership_unresolved",
        "request_payload_mapping_unresolved",
    ]
    assert candidate["terminal_method_signature_observed"] is True
    assert candidate["route_observed_in_private_excerpt"] is True
    assert candidate["helper_identity_evidence_sufficient"] is False
    assert receipt["summary"]["integrity_check_count"] == 42
    assert receipt["summary"][
        "ready_for_guild_progression_helper_reference_inventory"
    ] is True
    assert receipt["summary"]["ready_for_bounded_progression_route_probe"] is False
    assert receipt["decision_boundary"]["planner_scoring_allowed"] is False
    output = json.loads((tmp_path / "review.json").read_text(encoding="utf-8"))
    assert output["summary"]["contains_raw_definition"] is False


def test_private_inventory_hash_mismatch_blocks_review(tmp_path: Path) -> None:
    inventory, private, callsite = _inputs(tmp_path)
    private.write_text(private.read_text(encoding="utf-8") + " ", encoding="utf-8")
    with pytest.raises(ValueError, match="private helper-definition inventory SHA-256 mismatch"):
        _review(tmp_path, inventory, private, callsite)


def test_private_definition_span_mismatch_blocks_review(tmp_path: Path) -> None:
    inventory, private, callsite = _inputs(tmp_path)
    private_payload = json.loads(private.read_text(encoding="utf-8"))
    private_payload["definition_candidates"][0]["span"] = (
        "helper(x){return x&&x.value?x.value:1; }"
    )
    private_body = _write(private, private_payload)
    public_payload = json.loads(inventory.read_text(encoding="utf-8"))
    public_payload["source_private_inventory_sha256"] = hashlib.sha256(private_body).hexdigest()
    _write(inventory, public_payload)
    with pytest.raises(ValueError, match="private definition span SHA-256 mismatch"):
        _review(tmp_path, inventory, private, callsite)


def test_public_probe_overclaim_blocks_review(tmp_path: Path) -> None:
    inventory, private, callsite = _inputs(tmp_path)
    public_payload = json.loads(inventory.read_text(encoding="utf-8"))
    public_payload["summary"]["ready_for_bounded_progression_route_probe"] = True
    _write(inventory, public_payload)
    with pytest.raises(ValueError, match="public inventory summary mismatch"):
        _review(tmp_path, inventory, private, callsite)


def test_forbidden_public_definition_blocks_review(tmp_path: Path) -> None:
    inventory, private, callsite = _inputs(tmp_path)
    public_payload = json.loads(inventory.read_text(encoding="utf-8"))
    public_payload["definition_candidates"][0]["raw_definition"] = "secret"
    _write(inventory, public_payload)
    with pytest.raises(ValueError, match="contains forbidden fields"):
        _review(tmp_path, inventory, private, callsite)
