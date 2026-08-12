from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import pytest

from coa_workbench.collector.guild_progression_helper_owner_inventory import (
    inventory_guild_progression_helper_owners,
)
from coa_workbench.collector.guild_progression_helper_reference_index import (
    reference_candidates,
)

_ROUTE = "/api/guilds/progression"


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _write_json(path: Path, payload: object) -> bytes:
    body = (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return body


def _checks(count: int) -> dict[str, bool]:
    return {f"check_{index:02d}": True for index in range(1, count + 1)}


def _inputs(tmp_path: Path) -> dict[str, Path]:
    callee = "client.helper"
    definition = "helper(payload){return payload}"
    asset_text = (
        f"const client={{{definition}}};"
        "client.helper();"
        "client.helper();"
        + ("helper();" * 28)
    )
    definition_start = asset_text.index(definition)
    definition_end = definition_start + len(definition)
    private_rows, evidence = reference_candidates(
        asset_text,
        callee,
        definition_spans=((definition_start, definition_end),),
        route_template=_ROUTE,
        private_context_chars=128,
    )
    assert evidence["full_chain_occurrence_count_observed"] == 2
    assert evidence["terminal_symbol_occurrence_count_observed"] == 31
    assert evidence["terminal_symbol_only_occurrence_count"] == 29
    assert len(private_rows) == 31

    raw_root = tmp_path / "raw"
    payload = asset_text.encode()
    payload_hash = _sha256(payload)
    folder = (
        raw_root
        / "source=test"
        / "year=2026"
        / "month=08"
        / "endpoint=test"
    )
    folder.mkdir(parents=True)
    payload_path = folder / f"{payload_hash}.bin.gz"
    with payload_path.open("wb") as raw_stream:
        with gzip.GzipFile(
            filename="",
            mode="wb",
            fileobj=raw_stream,
            mtime=0,
        ) as stream:
            stream.write(payload)
    _write_json(
        folder / f"{payload_hash}.content.json",
        {
            "schema_version": 1,
            "endpoint_code": "guild_identity_asset_recovery",
            "payload_hash": payload_hash,
            "payload_path": payload_path.relative_to(raw_root).as_posix(),
            "compression": "gzip",
            "bytes_uncompressed": len(payload),
        },
    )

    callee_hash = _sha256(callee.encode())
    private_reference_path = tmp_path / "helper-reference.private.json"
    private_reference_body = _write_json(
        private_reference_path,
        {
            "schema_version": 1,
            "inventory_kind": "guild_progression_helper_reference_inventory_private",
            "inventory_version": "guild-progression-helper-reference-inventory-v1",
            "route": _ROUTE,
            "asset_payload_hash": payload_hash,
            "callee": callee,
            "callee_sha256": callee_hash,
            "references": [
                {**row, "reference_index": index}
                for index, row in enumerate(private_rows, 1)
            ],
            "summary": {
                **evidence,
                "contains_source_scalar_values": True,
                "network_requests_performed": False,
            },
        },
    )

    public_rows = [
        {
            "reference_index": index,
            "symbol_scope": row["symbol_scope"],
            "reference_kind": row["reference_kind"],
            "context_sha256": row["context_sha256"],
            "context_character_count": row["context_character_count"],
            "definition_candidate_overlap": row["definition_candidate_overlap"],
            "route_template_observed": row["route_template_observed"],
            "direct_transport_markers": row["direct_transport_markers"],
            "request_shape_markers": row["request_shape_markers"],
            "contains_raw_symbol": False,
            "contains_raw_context": False,
            "contains_source_scalar_values": False,
        }
        for index, row in enumerate(private_rows, 1)
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
    public_reference_path = tmp_path / "helper-reference.json"
    public_reference_body = _write_json(
        public_reference_path,
        {
            "schema_version": 1,
            "inventory_kind": "guild_progression_helper_reference_inventory",
            "inventory_version": "guild-progression-helper-reference-inventory-v1",
            "source_private_inventory_name": private_reference_path.name,
            "source_private_inventory_sha256": _sha256(private_reference_body),
            "target": {
                "guild_label": "Argentum",
                "route_template": _ROUTE,
                "callee_sha256": callee_hash,
                "callee_published": False,
                "raw_symbol_published": False,
                "raw_context_published": False,
                "source_scalar_values_published": False,
            },
            "references": public_rows,
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
        },
    )

    reference_review_path = tmp_path / "helper-reference-review.json"
    _write_json(
        reference_review_path,
        {
            "schema_version": 1,
            "review_kind": "guild_progression_helper_reference_review",
            "review_version": "guild-progression-helper-reference-review-v1",
            "source_inventory_name": public_reference_path.name,
            "source_inventory_sha256": _sha256(public_reference_body),
            "source_private_inventory_name": private_reference_path.name,
            "source_private_inventory_sha256": _sha256(private_reference_body),
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
        },
    )
    return {
        "review": reference_review_path,
        "public": public_reference_path,
        "private": private_reference_path,
        "raw_root": raw_root,
    }


def _inventory(tmp_path: Path, paths: dict[str, Path]) -> dict[str, object]:
    return inventory_guild_progression_helper_owners(
        reference_review_path=paths["review"],
        public_reference_inventory_path=paths["public"],
        private_reference_inventory_path=paths["private"],
        raw_root=paths["raw_root"],
        private_output_path=tmp_path / "helper-owner.private.json",
        receipt_output_path=tmp_path / "helper-owner.json",
    )


def test_owner_inventory_is_scalar_free_and_selects_owner_review(
    tmp_path: Path,
) -> None:
    paths = _inputs(tmp_path)
    receipt = _inventory(tmp_path, paths)

    summary = receipt["summary"]
    assert summary["integrity_check_count"] == 54
    assert summary["reference_count"] == 31
    assert summary["owner_candidate_occurrence_count"] == 3
    assert summary["unique_owner_group_count"] == 1
    assert summary["definition_owner_candidate_occurrence_count"] == 1
    assert summary["member_receiver_candidate_occurrence_count"] == 2
    assert summary["definition_container_candidate_occurrence_count"] == 1
    assert summary["references_without_owner_candidate_count"] == 28
    assert summary["cross_definition_reference_owner_group_count"] == 1
    assert summary["helper_owner_binding_resolved"] is False
    assert summary["ready_for_guild_progression_helper_owner_review"] is True
    assert summary["ready_for_bounded_progression_route_probe"] is False
    assert summary["network_requests_performed"] is False

    encoded = json.dumps(receipt)
    assert "client" not in encoded
    assert '"raw_owner_chain"' not in encoded
    assert '"context"' not in encoded
    assert '"raw_symbol"' not in encoded

    private_payload = json.loads(
        (tmp_path / "helper-owner.private.json").read_text(encoding="utf-8")
    )
    assert {
        row["raw_owner_chain"] for row in private_payload["owner_candidates"]
    } == {"client"}


def test_private_reference_hash_mismatch_blocks_owner_inventory(
    tmp_path: Path,
) -> None:
    paths = _inputs(tmp_path)
    paths["private"].write_text(
        paths["private"].read_text(encoding="utf-8") + " ",
        encoding="utf-8",
    )
    with pytest.raises(
        ValueError,
        match="helper-reference review private inventory SHA-256 mismatch",
    ):
        _inventory(tmp_path, paths)


def test_raw_asset_symbol_span_mismatch_blocks_owner_inventory(
    tmp_path: Path,
) -> None:
    paths = _inputs(tmp_path)

    private_payload = json.loads(paths["private"].read_text(encoding="utf-8"))
    private_payload["references"][0]["start"] += 1
    private_payload["references"][0]["end"] += 1
    private_body = _write_json(paths["private"], private_payload)

    public_payload = json.loads(paths["public"].read_text(encoding="utf-8"))
    public_payload["source_private_inventory_sha256"] = _sha256(private_body)
    public_body = _write_json(paths["public"], public_payload)

    review_payload = json.loads(paths["review"].read_text(encoding="utf-8"))
    review_payload["source_private_inventory_sha256"] = _sha256(private_body)
    review_payload["source_inventory_sha256"] = _sha256(public_body)
    _write_json(paths["review"], review_payload)

    with pytest.raises(ValueError, match="raw asset reference 1 symbol span mismatch"):
        _inventory(tmp_path, paths)


def test_reference_review_route_probe_overclaim_is_rejected(
    tmp_path: Path,
) -> None:
    paths = _inputs(tmp_path)
    review_payload = json.loads(paths["review"].read_text(encoding="utf-8"))
    review_payload["summary"]["ready_for_bounded_progression_route_probe"] = True
    _write_json(paths["review"], review_payload)

    with pytest.raises(ValueError, match="helper-reference review summary mismatch"):
        _inventory(tmp_path, paths)


def test_forbidden_public_owner_scalar_is_rejected(tmp_path: Path) -> None:
    paths = _inputs(tmp_path)
    public_payload = json.loads(paths["public"].read_text(encoding="utf-8"))
    public_payload["references"][0]["raw_owner_chain"] = "secret"
    public_body = _write_json(paths["public"], public_payload)

    review_payload = json.loads(paths["review"].read_text(encoding="utf-8"))
    review_payload["source_inventory_sha256"] = _sha256(public_body)
    _write_json(paths["review"], review_payload)

    with pytest.raises(ValueError, match="contains forbidden fields"):
        _inventory(tmp_path, paths)
