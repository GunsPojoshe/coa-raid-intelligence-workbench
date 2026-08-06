from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import pytest

from coa_workbench.collector.guild_progression_helper_reference_inventory import (
    inventory_guild_progression_helper_references,
)

_ROUTE = "/api/guilds/progression"


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _write_json(path: Path, payload: object) -> bytes:
    body = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return body


def _checks(count: int) -> dict[str, bool]:
    return {f"check_{index:02d}": True for index in range(1, count + 1)}


def _inputs(tmp_path: Path) -> dict[str, Path]:
    callee = "client.post"
    definition = "post(payload){return transport(payload)}"
    asset_text = (
        f"const client={{ {definition} }};"
        f'client.post("{_ROUTE}",{{id:1}});'
        'client.post("/api/other",{id:2});'
    )
    definition_start = asset_text.index(definition)
    definition_end = definition_start + len(definition)

    raw_root = tmp_path / "raw"
    payload = asset_text.encode()
    payload_hash = _sha256(payload)
    folder = raw_root / "source=test" / "year=2026" / "month=08" / "endpoint=test"
    folder.mkdir(parents=True)
    payload_path = folder / f"{payload_hash}.bin.gz"
    with payload_path.open("wb") as raw_stream:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw_stream, mtime=0) as stream:
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
    span_hash = _sha256(definition.encode())
    private_inventory_path = tmp_path / "private-definition.json"
    private_inventory_body = _write_json(
        private_inventory_path,
        {
            "schema_version": 1,
            "inventory_kind": "guild_progression_helper_definition_inventory_private",
            "inventory_version": "guild-progression-helper-definition-inventory-v1",
            "route": _ROUTE,
            "asset_payload_hash": payload_hash,
            "callee": callee,
            "callee_sha256": callee_hash,
            "definition_candidates": [
                {
                    "candidate_index": 1,
                    "kind": "method_definition",
                    "binding_scope": "terminal_symbol",
                    "start": definition_start,
                    "end": definition_end,
                    "span": definition,
                    "span_sha256": span_hash,
                }
            ],
        },
    )

    public_inventory_path = tmp_path / "public-definition.json"
    public_inventory_body = _write_json(
        public_inventory_path,
        {
            "schema_version": 1,
            "inventory_kind": "guild_progression_helper_definition_inventory",
            "inventory_version": "guild-progression-helper-definition-inventory-v1",
            "source_private_inventory_name": private_inventory_path.name,
            "source_private_inventory_sha256": _sha256(private_inventory_body),
            "target": {
                "guild_label": "Argentum",
                "route_template": _ROUTE,
                "callee_sha256": callee_hash,
                "callee_published": False,
                "asset_url_published": False,
                "source_guild_id_published": False,
                "raw_definition_published": False,
                "alias_target_published": False,
                "source_scalar_values_published": False,
            },
            "cross_definition_evidence": {
                "full_chain_occurrence_count_observed": 2,
                "full_chain_occurrence_scan_truncated": False,
                "terminal_symbol_occurrence_count_observed": 3,
                "terminal_symbol_occurrence_scan_truncated": False,
                "definition_candidate_count": 1,
                "definition_candidate_scan_truncated": False,
                "definition_kinds": ["method_definition"],
                "binding_scopes": ["terminal_symbol"],
                "alias_candidate_count": 0,
                "marker_classes": [],
                "helper_definition_candidate_observed": True,
                "contains_raw_callee": False,
                "contains_raw_definition": False,
                "contains_alias_target": False,
                "contains_source_scalar_values": False,
            },
            "integrity_checks": _checks(36),
        },
    )

    review_path = tmp_path / "definition-review.json"
    _write_json(
        review_path,
        {
            "schema_version": 1,
            "review_kind": "guild_progression_helper_definition_review",
            "review_version": "guild-progression-helper-definition-review-v1",
            "source_inventory_sha256": _sha256(public_inventory_body),
            "source_private_inventory_sha256": _sha256(private_inventory_body),
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
                "ready_for_bounded_progression_route_probe": False,
                "guild_api_route_semantics_verified": False,
                "pagination_semantics_verified": False,
                "termination_semantics_verified": False,
                "completeness_verified": False,
                "ready_for_full_guild_crawl": False,
                "planner_scoring_allowed": False,
                "contains_raw_callee": False,
                "contains_raw_definition": False,
                "contains_private_excerpt": False,
                "contains_alias_target": False,
                "contains_source_scalar_values": False,
                "network_requests_performed": False,
            },
        },
    )
    return {
        "review": review_path,
        "public_inventory": public_inventory_path,
        "private_inventory": private_inventory_path,
        "raw_root": raw_root,
    }


def _inventory(tmp_path: Path, **overrides: int) -> dict[str, object]:
    paths = _inputs(tmp_path)
    return inventory_guild_progression_helper_references(
        definition_review_path=paths["review"],
        public_definition_inventory_path=paths["public_inventory"],
        private_definition_inventory_path=paths["private_inventory"],
        raw_root=paths["raw_root"],
        private_output_path=tmp_path / "private-reference.json",
        receipt_output_path=tmp_path / "public-reference.json",
        **overrides,
    )


def test_reference_inventory_is_scalar_free_and_probe_blocked(tmp_path: Path) -> None:
    receipt = _inventory(tmp_path, private_context_chars=128)

    summary = receipt["summary"]
    assert summary["integrity_check_count"] == 40
    assert summary["full_chain_occurrence_count_observed"] == 2
    assert summary["terminal_symbol_occurrence_count_observed"] == 3
    assert summary["terminal_symbol_only_occurrence_count"] == 1
    assert summary["unique_reference_candidate_count"] == 3
    assert summary["definition_overlap_count"] == 1
    assert summary["ready_for_guild_progression_helper_reference_review"] is True
    assert summary["ready_for_bounded_progression_route_probe"] is False
    assert summary["guild_progression_helper_identity_resolved"] is False
    assert summary["network_requests_performed"] is False

    encoded = json.dumps(receipt)
    assert "client.post" not in encoded
    assert '"context"' not in encoded
    assert '"raw_symbol"' not in encoded
    assert '"callee"' not in encoded

    private_payload = json.loads((tmp_path / "private-reference.json").read_text())
    assert private_payload["callee"] == "client.post"
    assert private_payload["references"][0]["context"]


def test_reference_count_drift_is_rejected(tmp_path: Path) -> None:
    paths = _inputs(tmp_path)
    public_payload = json.loads(paths["public_inventory"].read_text())
    public_payload["cross_definition_evidence"][
        "terminal_symbol_occurrence_count_observed"
    ] = 4
    public_body = _write_json(paths["public_inventory"], public_payload)
    review_payload = json.loads(paths["review"].read_text())
    review_payload["source_inventory_sha256"] = _sha256(public_body)
    _write_json(paths["review"], review_payload)

    with pytest.raises(ValueError, match="terminal-symbol-occurrence-count-observed"):
        inventory_guild_progression_helper_references(
            definition_review_path=paths["review"],
            public_definition_inventory_path=paths["public_inventory"],
            private_definition_inventory_path=paths["private_inventory"],
            raw_root=paths["raw_root"],
            private_output_path=tmp_path / "private-reference.json",
            receipt_output_path=tmp_path / "public-reference.json",
        )


def test_reference_scan_truncation_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="reference candidate scan truncated is true"):
        _inventory(tmp_path, max_reference_candidates=2, private_context_chars=128)


def test_definition_review_overclaim_is_rejected(tmp_path: Path) -> None:
    paths = _inputs(tmp_path)
    review_payload = json.loads(paths["review"].read_text())
    review_payload["summary"]["ready_for_bounded_progression_route_probe"] = True
    _write_json(paths["review"], review_payload)

    with pytest.raises(ValueError, match="helper-definition review summary mismatch"):
        inventory_guild_progression_helper_references(
            definition_review_path=paths["review"],
            public_definition_inventory_path=paths["public_inventory"],
            private_definition_inventory_path=paths["private_inventory"],
            raw_root=paths["raw_root"],
            private_output_path=tmp_path / "private-reference.json",
            receipt_output_path=tmp_path / "public-reference.json",
        )
