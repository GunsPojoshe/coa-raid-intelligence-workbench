from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from coa_workbench.collector.guild_progression_helper_owner_review import (
    review_guild_progression_helper_owners,
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


def _reference_review() -> dict[str, object]:
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
        "review_kind": "guild_progression_helper_reference_review",
        "review_version": "guild-progression-helper-reference-review-v1",
        "integrity_checks": _checks(46),
        "summary": {
            "all_integrity_checks_passed": True,
            "integrity_check_count": 46,
            "guild_progression_helper_reference_reviewed": True,
            "reference_count": 31,
            "reference_review_disposition": (
                "unresolved_references_without_route_or_transport_binding"
            ),
            "route_context_reference_count": 0,
            "direct_transport_context_count": 0,
            "route_transport_binding_count": 0,
            "route_request_shape_binding_count": 0,
            "helper_identity_resolved": False,
            "helper_owner_binding_resolved": False,
            "request_payload_mapping_resolved": False,
            "request_shape_sufficient_for_bounded_probe": False,
            "ready_for_guild_progression_helper_owner_inventory": True,
            **false_gates,
            "contains_raw_callee": False,
            "contains_raw_symbol": False,
            "contains_raw_context": False,
            "contains_source_scalar_values": False,
            "network_requests_performed": False,
        },
    }


def _inputs(tmp_path: Path, *, converged: bool = False) -> dict[str, Path]:
    reference_review_path = tmp_path / "helper-reference-review.json"
    reference_review_body = _write(reference_review_path, _reference_review())

    callee = "client.helper"
    callee_hash = _sha(callee)
    definition_owner = "client"
    full_chain_owner = definition_owner if converged else "transport"

    private_candidates = [
        {
            "candidate_index": 1,
            "reference_index": 1,
            "symbol_scope": "terminal_symbol",
            "reference_kind": "definition_candidate",
            "definition_candidate_overlap": True,
            "candidate_source": "terminal_member_receiver",
            "raw_owner_chain": definition_owner,
            "owner_start": 10,
            "owner_end": 10 + len(definition_owner),
            "owner_chain_sha256": _sha(definition_owner),
            "owner_chain_character_count": len(definition_owner),
            "owner_chain_depth": 1,
            "source_reference_context_sha256": _sha("definition-context"),
        },
        {
            "candidate_index": 2,
            "reference_index": 6,
            "symbol_scope": "full_chain",
            "reference_kind": "invocation",
            "definition_candidate_overlap": False,
            "candidate_source": "full_chain_member_receiver",
            "raw_owner_chain": full_chain_owner,
            "owner_start": 30,
            "owner_end": 30 + len(full_chain_owner),
            "owner_chain_sha256": _sha(full_chain_owner),
            "owner_chain_character_count": len(full_chain_owner),
            "owner_chain_depth": 1,
            "source_reference_context_sha256": _sha("full-chain-context-1"),
        },
        {
            "candidate_index": 3,
            "reference_index": 20,
            "symbol_scope": "full_chain",
            "reference_kind": "invocation",
            "definition_candidate_overlap": False,
            "candidate_source": "full_chain_member_receiver",
            "raw_owner_chain": full_chain_owner,
            "owner_start": 50,
            "owner_end": 50 + len(full_chain_owner),
            "owner_chain_sha256": _sha(full_chain_owner),
            "owner_chain_character_count": len(full_chain_owner),
            "owner_chain_depth": 1,
            "source_reference_context_sha256": _sha("full-chain-context-2"),
        },
        {
            "candidate_index": 4,
            "reference_index": 24,
            "symbol_scope": "terminal_symbol",
            "reference_kind": "invocation",
            "definition_candidate_overlap": False,
            "candidate_source": "terminal_member_receiver",
            "raw_owner_chain": definition_owner,
            "owner_start": 70,
            "owner_end": 70 + len(definition_owner),
            "owner_chain_sha256": _sha(definition_owner),
            "owner_chain_character_count": len(definition_owner),
            "owner_chain_depth": 1,
            "source_reference_context_sha256": _sha("definition-invocation-context"),
        },
    ]

    if converged:
        private_groups = [
            {
                "owner_group_index": 1,
                "raw_owner_chain": definition_owner,
                "owner_chain_sha256": _sha(definition_owner),
                "owner_chain_character_count": len(definition_owner),
                "owner_chain_depth": 1,
                "occurrence_count": 4,
                "reference_indexes": [1, 6, 20, 24],
                "candidate_sources": [
                    "full_chain_member_receiver",
                    "terminal_member_receiver",
                ],
                "definition_candidate_count": 1,
                "non_definition_candidate_count": 3,
                "cross_definition_reference_binding_observed": True,
            }
        ]
        group_index_by_owner = {definition_owner: 1}
    else:
        private_groups = [
            {
                "owner_group_index": 1,
                "raw_owner_chain": full_chain_owner,
                "owner_chain_sha256": _sha(full_chain_owner),
                "owner_chain_character_count": len(full_chain_owner),
                "owner_chain_depth": 1,
                "occurrence_count": 2,
                "reference_indexes": [6, 20],
                "candidate_sources": ["full_chain_member_receiver"],
                "definition_candidate_count": 0,
                "non_definition_candidate_count": 2,
                "cross_definition_reference_binding_observed": False,
            },
            {
                "owner_group_index": 2,
                "raw_owner_chain": definition_owner,
                "owner_chain_sha256": _sha(definition_owner),
                "owner_chain_character_count": len(definition_owner),
                "owner_chain_depth": 1,
                "occurrence_count": 2,
                "reference_indexes": [1, 24],
                "candidate_sources": ["terminal_member_receiver"],
                "definition_candidate_count": 1,
                "non_definition_candidate_count": 1,
                "cross_definition_reference_binding_observed": True,
            },
        ]
        group_index_by_owner = {full_chain_owner: 1, definition_owner: 2}

    private = {
        "schema_version": 1,
        "inventory_kind": "guild_progression_helper_owner_inventory_private",
        "inventory_version": "guild-progression-helper-owner-inventory-v1",
        "source_reference_review_sha256": hashlib.sha256(reference_review_body).hexdigest(),
        "route": "/api/guilds/progression",
        "callee": callee,
        "callee_sha256": callee_hash,
        "owner_candidates": private_candidates,
        "owner_groups": private_groups,
        "summary": {
            "reference_count": 31,
            "owner_candidate_occurrence_count": len(private_candidates),
            "unique_owner_group_count": len(private_groups),
            "contains_raw_owner_chain": True,
            "contains_source_scalar_values": True,
            "network_requests_performed": False,
        },
    }
    private_path = tmp_path / "helper-owner.private.json"
    private_body = _write(private_path, private)

    public_candidates = []
    for candidate in private_candidates:
        public_candidates.append(
            {
                "candidate_index": candidate["candidate_index"],
                "reference_index": candidate["reference_index"],
                "symbol_scope": candidate["symbol_scope"],
                "reference_kind": candidate["reference_kind"],
                "definition_candidate_overlap": candidate["definition_candidate_overlap"],
                "candidate_source": candidate["candidate_source"],
                "owner_group_index": group_index_by_owner[candidate["raw_owner_chain"]],
                "owner_chain_depth": candidate["owner_chain_depth"],
                "source_reference_context_sha256": candidate["source_reference_context_sha256"],
                "contains_raw_owner_chain": False,
                "contains_raw_symbol": False,
                "contains_raw_context": False,
                "contains_source_scalar_values": False,
            }
        )

    public_groups = [
        {
            "owner_group_index": group["owner_group_index"],
            "owner_chain_depth": group["owner_chain_depth"],
            "occurrence_count": group["occurrence_count"],
            "reference_indexes": group["reference_indexes"],
            "candidate_sources": group["candidate_sources"],
            "definition_candidate_count": group["definition_candidate_count"],
            "non_definition_candidate_count": group["non_definition_candidate_count"],
            "cross_definition_reference_binding_observed": group[
                "cross_definition_reference_binding_observed"
            ],
            "raw_owner_chain_published": False,
            "contains_source_scalar_values": False,
        }
        for group in private_groups
    ]

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
        "inventory_kind": "guild_progression_helper_owner_inventory",
        "inventory_version": "guild-progression-helper-owner-inventory-v1",
        "source_reference_review_name": reference_review_path.name,
        "source_reference_review_sha256": hashlib.sha256(reference_review_body).hexdigest(),
        "source_private_inventory_name": private_path.name,
        "source_private_inventory_sha256": hashlib.sha256(private_body).hexdigest(),
        "target": {
            "guild_label": "Argentum",
            "route_template": "/api/guilds/progression",
            "callee_sha256": callee_hash,
            "callee_published": False,
            "owner_chain_published": False,
            "raw_symbol_published": False,
            "raw_context_published": False,
            "source_scalar_values_published": False,
        },
        "owner_candidates": public_candidates,
        "owner_groups": public_groups,
        "integrity_checks": _checks(54),
        "summary": {
            "all_integrity_checks_passed": True,
            "integrity_check_count": 54,
            "reference_count": 31,
            "owner_candidate_occurrence_count": len(public_candidates),
            "unique_owner_group_count": len(public_groups),
            "guild_progression_helper_owner_inventory_completed": True,
            "helper_identity_resolved": False,
            "helper_owner_binding_resolved": False,
            "request_payload_mapping_resolved": False,
            "request_shape_sufficient_for_bounded_probe": False,
            "ready_for_guild_progression_helper_owner_review": True,
            **false_gates,
            "contains_raw_owner_chain": False,
            "contains_raw_symbol": False,
            "contains_raw_context": False,
            "contains_source_scalar_values": False,
            "network_requests_performed": False,
        },
    }
    public_path = tmp_path / "helper-owner.json"
    _write(public_path, public)
    return {
        "public": public_path,
        "private": private_path,
        "reference": reference_review_path,
    }


def _review(tmp_path: Path, paths: dict[str, Path]) -> dict[str, object]:
    return review_guild_progression_helper_owners(
        inventory_path=paths["public"],
        private_inventory_path=paths["private"],
        reference_review_path=paths["reference"],
        receipt_output_path=tmp_path / "owner-review.json",
    )


def test_owner_review_detects_full_chain_definition_owner_mismatch(tmp_path: Path) -> None:
    paths = _inputs(tmp_path)
    receipt = _review(tmp_path, paths)

    summary = receipt["summary"]
    assert summary["integrity_check_count"] == 16
    assert summary["owner_review_disposition"] == (
        "unresolved_full_chain_owner_differs_from_definition_owner"
    )
    assert summary["full_chain_owner_group_index"] == 1
    assert summary["definition_owner_group_index"] == 2
    assert summary["full_chain_definition_owner_group_match"] is False
    assert summary["helper_owner_binding_resolved"] is False
    assert summary["ready_for_guild_progression_helper_owner_relationship_inventory"] is True
    assert summary["ready_for_bounded_progression_route_probe"] is False

    review = receipt["owner_binding_review"]
    assert review["definition_owner_group_non_definition_invocation_count"] == 1
    assert review["cross_definition_reference_owner_group_indexes"] == [2]
    assert review["blockers"] == [
        "full_chain_owner_group_differs_from_definition_owner_group",
        "multiple_receiver_owner_groups_observed",
        "owner_alias_or_equivalence_relation_unresolved",
        "helper_identity_unresolved",
        "request_payload_mapping_unresolved",
    ]

    encoded = json.dumps(receipt)
    assert "client" not in encoded
    assert "transport" not in encoded
    assert _sha("client") not in encoded
    assert _sha("transport") not in encoded
    assert '"owner_chain_sha256"' not in encoded
    assert '"owner_chain_character_count"' not in encoded
    assert '"raw_owner_chain"' not in encoded


def test_converged_owner_binding_does_not_enable_route_probe(tmp_path: Path) -> None:
    paths = _inputs(tmp_path, converged=True)
    receipt = _review(tmp_path, paths)

    summary = receipt["summary"]
    assert (
        summary["owner_review_disposition"] == "owner_binding_converged_helper_identity_unresolved"
    )
    assert summary["full_chain_owner_group_index"] == 1
    assert summary["definition_owner_group_index"] == 1
    assert summary["full_chain_definition_owner_group_match"] is True
    assert summary["helper_owner_binding_resolved"] is True
    assert summary["ready_for_guild_progression_helper_owner_relationship_inventory"] is False
    assert summary["helper_identity_resolved"] is False
    assert summary["ready_for_bounded_progression_route_probe"] is False


def test_private_inventory_hash_mismatch_blocks_owner_review(tmp_path: Path) -> None:
    paths = _inputs(tmp_path)
    paths["private"].write_text(
        paths["private"].read_text(encoding="utf-8") + " ", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="private helper-owner inventory SHA-256 mismatch"):
        _review(tmp_path, paths)


def test_public_owner_hash_field_is_rejected(tmp_path: Path) -> None:
    paths = _inputs(tmp_path)
    public = json.loads(paths["public"].read_text(encoding="utf-8"))
    public["owner_candidates"][0]["owner_chain_sha256"] = _sha("client")
    _write(paths["public"], public)
    with pytest.raises(ValueError, match="contains forbidden fields"):
        _review(tmp_path, paths)


def test_public_private_owner_group_mismatch_is_rejected(tmp_path: Path) -> None:
    paths = _inputs(tmp_path)
    public = json.loads(paths["public"].read_text(encoding="utf-8"))
    public["owner_candidates"][0]["owner_group_index"] = 1
    _write(paths["public"], public)
    with pytest.raises(ValueError, match="public/private owner candidate group mismatch"):
        _review(tmp_path, paths)
