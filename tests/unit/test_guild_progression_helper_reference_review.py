from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from coa_workbench.collector.guild_progression_helper_reference_review import (
    review_guild_progression_helper_references,
)


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _write(path: Path, payload: object) -> bytes:
    body = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return body


def _checks(count: int) -> dict[str, bool]:
    return {f"check_{index:02d}": True for index in range(1, count + 1)}


def _definition_review() -> dict[str, object]:
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
        "review_kind": "guild_progression_helper_definition_review",
        "review_version": "guild-progression-helper-definition-review-v1",
        "integrity_checks": _checks(42),
        "summary": {
            "all_integrity_checks_passed": True,
            "integrity_check_count": 42,
            "guild_progression_helper_definition_reviewed": True,
            "definition_candidate_count": 1,
            "definition_candidate_disposition": (
                "unresolved_terminal_method_without_transport_semantics"
            ),
            "helper_identity_resolved": False,
            "request_payload_mapping_resolved": False,
            "request_shape_sufficient_for_bounded_probe": False,
            "ready_for_guild_progression_helper_reference_inventory": True,
            **false_gates,
            "contains_raw_callee": False,
            "contains_raw_definition": False,
            "contains_private_excerpt": False,
            "contains_alias_target": False,
            "contains_source_scalar_values": False,
            "network_requests_performed": False,
        },
    }


def _inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    definition_review_path = tmp_path / "definition-review.json"
    definition_review_body = _write(definition_review_path, _definition_review())

    callee = "client.helper"
    callee_hash = _sha(callee)
    private_rows = []
    public_rows = []
    request_markers = [
        ["JSON.stringify", "body"],
        ["data"],
        ["params"],
        ["url"],
    ]
    kinds = [
        "definition_candidate",
        *(["invocation"] * 10),
        *(["member_reference"] * 10),
        *(["object_key"] * 10),
    ]
    assert len(kinds) == 31
    for index, kind in enumerate(kinds, 1):
        scope = "full_chain" if index <= 2 else "terminal_symbol"
        symbol = callee if scope == "full_chain" else "helper"
        markers = request_markers[index - 1] if index <= len(request_markers) else []
        context = f"prefix-{index}-{symbol}-suffix"
        if markers:
            context += "-" + "-".join(markers)
        context_hash = _sha(context)
        start = index * 10
        end = start + len(symbol)
        context_start = start - 3
        context_end = context_start + len(context)
        private_rows.append(
            {
                "reference_index": index,
                "symbol_scope": scope,
                "raw_symbol": symbol,
                "start": start,
                "end": end,
                "reference_kind": kind,
                "context": context,
                "context_start": context_start,
                "context_end": context_end,
                "context_sha256": context_hash,
                "context_character_count": len(context),
                "definition_candidate_overlap": index == 1,
                "route_template_observed": False,
                "direct_transport_markers": [],
                "request_shape_markers": markers,
            }
        )
        public_rows.append(
            {
                "reference_index": index,
                "symbol_scope": scope,
                "reference_kind": kind,
                "context_sha256": context_hash,
                "context_character_count": len(context),
                "definition_candidate_overlap": index == 1,
                "route_template_observed": False,
                "direct_transport_markers": [],
                "request_shape_markers": markers,
                "contains_raw_symbol": False,
                "contains_raw_context": False,
                "contains_source_scalar_values": False,
            }
        )

    evidence = {
        "full_chain_occurrence_count_observed": 2,
        "full_chain_occurrence_scan_truncated": False,
        "terminal_symbol_occurrence_count_observed": 31,
        "terminal_symbol_occurrence_scan_truncated": False,
        "terminal_symbol_only_occurrence_count": 29,
        "unique_reference_candidate_count": 31,
        "reference_candidate_scan_truncated": False,
        "reference_kinds": [
            "definition_candidate",
            "invocation",
            "member_reference",
            "object_key",
        ],
        "symbol_scopes": ["full_chain", "terminal_symbol"],
        "definition_overlap_count": 1,
        "route_context_reference_count": 0,
        "direct_transport_marker_classes": [],
        "request_shape_marker_classes": ["JSON.stringify", "body", "data", "params", "url"],
    }
    private = {
        "schema_version": 1,
        "inventory_kind": "guild_progression_helper_reference_inventory_private",
        "inventory_version": "guild-progression-helper-reference-inventory-v1",
        "route": "/api/guilds/progression",
        "callee": callee,
        "callee_sha256": callee_hash,
        "references": private_rows,
        "summary": {
            **evidence,
            "contains_source_scalar_values": True,
            "network_requests_performed": False,
        },
    }
    private_path = tmp_path / "helper-reference.private.json"
    private_body = _write(private_path, private)

    false_gates = {
        "ready_for_bounded_progression_route_probe": False,
        "guild_api_route_semantics_verified": False,
        "pagination_semantics_verified": False,
        "termination_semantics_verified": False,
        "completeness_verified": False,
        "ready_for_full_guild_crawl": False,
        "planner_scoring_allowed": False,
    }
    public = {
        "schema_version": 1,
        "inventory_kind": "guild_progression_helper_reference_inventory",
        "inventory_version": "guild-progression-helper-reference-inventory-v1",
        "source_definition_review_name": definition_review_path.name,
        "source_definition_review_sha256": hashlib.sha256(definition_review_body).hexdigest(),
        "source_private_inventory_name": private_path.name,
        "source_private_inventory_sha256": hashlib.sha256(private_body).hexdigest(),
        "target": {
            "guild_label": "Argentum",
            "route_template": "/api/guilds/progression",
            "callee_sha256": callee_hash,
            "callee_published": False,
            "raw_symbol_published": False,
            "raw_context_published": False,
            "source_scalar_values_published": False,
        },
        "request_contract": {
            "network_requests_performed": False,
            "raw_archive_only": True,
            "max_symbol_occurrences": 500,
            "max_reference_candidates": 500,
            "private_context_chars_per_side": 1024,
        },
        "references": public_rows,
        "cross_reference_evidence": {
            **evidence,
            "reference_evidence_observed": True,
            "contains_raw_callee": False,
            "contains_raw_symbol": False,
            "contains_raw_context": False,
            "contains_source_scalar_values": False,
        },
        "integrity_checks": _checks(40),
        "summary": {
            "all_integrity_checks_passed": True,
            "integrity_check_count": 40,
            **evidence,
            "reference_evidence_observed": True,
            "ready_for_guild_progression_helper_reference_review": True,
            "guild_progression_helper_identity_resolved": False,
            "guild_progression_request_payload_mapping_resolved": False,
            "guild_progression_request_shape_verified": False,
            **false_gates,
            "contains_raw_callee": False,
            "contains_raw_symbol": False,
            "contains_raw_context": False,
            "contains_source_scalar_values": False,
            "network_requests_performed": False,
        },
    }
    public_path = tmp_path / "helper-reference.json"
    _write(public_path, public)
    return public_path, private_path, definition_review_path


def _review(tmp_path: Path, public: Path, private: Path, definition: Path) -> dict[str, object]:
    return review_guild_progression_helper_references(
        inventory_path=public,
        private_inventory_path=private,
        definition_review_path=definition,
        receipt_output_path=tmp_path / "review.json",
    )


def test_reference_review_keeps_probe_blocked_and_selects_owner_inventory(tmp_path: Path) -> None:
    public, private, definition = _inputs(tmp_path)
    receipt = _review(tmp_path, public, private, definition)

    review = receipt["helper_reference_review"]
    assert review["reference_count"] == 31
    assert review["route_context_reference_count"] == 0
    assert review["direct_transport_context_count"] == 0
    assert review["request_shape_context_count"] == 4
    assert review["blockers"] == [
        "route_not_observed_in_reference_contexts",
        "direct_transport_markers_not_observed",
        "receiver_or_owner_binding_unresolved",
        "request_shape_markers_not_bound_to_route_invocation",
    ]
    assert receipt["summary"]["integrity_check_count"] == 46
    assert receipt["summary"]["ready_for_guild_progression_helper_owner_inventory"] is True
    assert receipt["summary"]["ready_for_bounded_progression_route_probe"] is False
    assert receipt["decision_boundary"]["planner_scoring_allowed"] is False
    output = json.loads((tmp_path / "review.json").read_text(encoding="utf-8"))
    encoded = json.dumps(output)
    assert '"context"' not in encoded
    assert '"raw_symbol"' not in encoded


def test_private_inventory_hash_mismatch_blocks_review(tmp_path: Path) -> None:
    public, private, definition = _inputs(tmp_path)
    private.write_text(private.read_text(encoding="utf-8") + " ", encoding="utf-8")
    with pytest.raises(ValueError, match="private helper-reference inventory SHA-256 mismatch"):
        _review(tmp_path, public, private, definition)


def test_private_context_hash_mismatch_blocks_review(tmp_path: Path) -> None:
    public, private, definition = _inputs(tmp_path)
    private_payload = json.loads(private.read_text(encoding="utf-8"))
    private_payload["references"][0]["context"] += "changed"
    private_body = _write(private, private_payload)
    public_payload = json.loads(public.read_text(encoding="utf-8"))
    public_payload["source_private_inventory_sha256"] = hashlib.sha256(private_body).hexdigest()
    _write(public, public_payload)
    with pytest.raises(ValueError, match="context SHA-256 mismatch"):
        _review(tmp_path, public, private, definition)


def test_public_route_context_overclaim_blocks_review(tmp_path: Path) -> None:
    public, private, definition = _inputs(tmp_path)
    public_payload = json.loads(public.read_text(encoding="utf-8"))
    public_payload["summary"]["route_context_reference_count"] = 1
    _write(public, public_payload)
    with pytest.raises(ValueError, match="public inventory summary mismatch"):
        _review(tmp_path, public, private, definition)


def test_forbidden_public_context_blocks_review(tmp_path: Path) -> None:
    public, private, definition = _inputs(tmp_path)
    public_payload = json.loads(public.read_text(encoding="utf-8"))
    public_payload["references"][0]["context"] = "secret"
    _write(public, public_payload)
    with pytest.raises(ValueError, match="contains forbidden fields"):
        _review(tmp_path, public, private, definition)
