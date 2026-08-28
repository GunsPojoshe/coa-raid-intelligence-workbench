from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import pytest

from coa_workbench.collector.guild_progression_helper_definition_inventory import (
    inventory_guild_progression_helper_definition,
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


def _inputs(tmp_path: Path, asset_text: str, callee: str = "request") -> dict[str, Path]:
    raw_root = tmp_path / "raw"
    payload = asset_text.encode()
    payload_hash = _sha256(payload)
    folder = raw_root / "source=test" / "year=2026" / "month=08" / "endpoint=test"
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

    private_recovery_path = tmp_path / "private-recovery.json"
    private_recovery_body = _write_json(
        private_recovery_path,
        {
            "schema_version": 1,
            "recovery_kind": "guild_identity_asset_profiled_recovery_private",
            "recovery_version": "guild-identity-asset-profiled-recovery-v1",
            "target_guild_label": "Argentum",
            "asset_capture_payload_hash": payload_hash,
            "api_route_candidates": [_ROUTE],
            "summary": {
                "asset_download_completed": True,
                "contains_source_scalar_values": True,
            },
        },
    )
    public_recovery_path = tmp_path / "public-recovery.json"
    _write_json(
        public_recovery_path,
        {
            "schema_version": 1,
            "recovery_kind": "guild_identity_asset_profiled_recovery",
            "recovery_version": "guild-identity-asset-profiled-recovery-v1",
            "source_private_recovery_sha256": _sha256(private_recovery_body),
            "target": {
                "guild_label": "Argentum",
                "asset_url_published": False,
                "source_guild_id_published": False,
            },
            "summary": {
                "all_integrity_checks_passed": True,
                "asset_download_completed": True,
                "contains_source_scalar_values": False,
                "guild_api_route_candidate_count": 3,
            },
            "integrity_checks": _checks(15),
            "route_inventory": {
                "guild_api_route_shapes": [
                    _ROUTE,
                    "/api/guilds/search?q=<value>",
                    "/api/guilds/search?q=<value>&limit=<value>",
                ]
            },
        },
    )

    callee_hash = _sha256(callee.encode())
    private_callsite_path = tmp_path / "private-callsite.json"
    private_callsite_body = _write_json(
        private_callsite_path,
        {
            "schema_version": 1,
            "inventory_kind": "guild_progression_helper_callsite_inventory_private",
            "inventory_version": "guild-progression-helper-callsite-inventory-v1",
            "asset_payload_hash": payload_hash,
            "route": _ROUTE,
            "occurrences": [
                {
                    "call_candidates": [
                        {
                            "class": "generic_helper_call",
                            "callee": callee,
                        }
                    ]
                }
            ],
        },
    )
    public_callsite_path = tmp_path / "public-callsite.json"
    public_callsite_body = _write_json(
        public_callsite_path,
        {
            "schema_version": 1,
            "inventory_kind": "guild_progression_helper_callsite_inventory",
            "inventory_version": "guild-progression-helper-callsite-inventory-v1",
            "source_private_inventory_sha256": _sha256(private_callsite_body),
            "integrity_checks": _checks(32),
            "occurrences": [
                {
                    "call_candidates": [
                        {
                            "callee_class": "generic_helper_call",
                            "callee_sha256": callee_hash,
                            "method_candidates": ["POST"],
                            "method_evidence": ["method_property_literal"],
                            "route_direct_argument_candidate": True,
                            "contains_raw_callee": False,
                            "contains_raw_call_text": False,
                        }
                    ]
                }
            ],
            "summary": {
                "all_integrity_checks_passed": True,
                "integrity_check_count": 32,
                "route_occurrence_count": 1,
                "call_candidate_count": 1,
                "direct_invocation_candidate_count": 1,
                "method_candidate_count": 1,
                "method_candidate_unambiguous": True,
                "ready_for_guild_progression_helper_callsite_review": True,
                "ready_for_bounded_progression_route_probe": False,
                "guild_api_route_semantics_verified": False,
                "pagination_semantics_verified": False,
                "termination_semantics_verified": False,
                "completeness_verified": False,
                "ready_for_full_guild_crawl": False,
                "planner_scoring_allowed": False,
                "contains_raw_context": False,
                "contains_raw_callee": False,
                "contains_source_scalar_values": False,
                "network_requests_performed": False,
            },
        },
    )
    callsite_review_path = tmp_path / "callsite-review.json"
    _write_json(
        callsite_review_path,
        {
            "schema_version": 1,
            "review_kind": "guild_progression_helper_callsite_review",
            "review_version": "guild-progression-helper-callsite-review-v1",
            "source_inventory_sha256": _sha256(public_callsite_body),
            "integrity_checks": _checks(36),
            "summary": {
                "all_integrity_checks_passed": True,
                "integrity_check_count": 36,
                "guild_progression_helper_callsite_reviewed": True,
                "method_candidate_unambiguous": True,
                "http_method_candidate": "POST",
                "helper_identity_resolved": False,
                "request_payload_mapping_resolved": False,
                "request_shape_sufficient_for_bounded_probe": False,
                "ready_for_guild_progression_helper_definition_inventory": True,
                "ready_for_bounded_progression_route_probe": False,
                "guild_api_route_semantics_verified": False,
                "pagination_semantics_verified": False,
                "termination_semantics_verified": False,
                "completeness_verified": False,
                "ready_for_full_guild_crawl": False,
                "planner_scoring_allowed": False,
                "contains_raw_callee": False,
                "contains_raw_context": False,
                "contains_source_scalar_values": False,
            },
        },
    )
    return {
        "callsite_review": callsite_review_path,
        "public_callsite": public_callsite_path,
        "private_callsite": private_callsite_path,
        "public_recovery": public_recovery_path,
        "private_recovery": private_recovery_path,
        "raw_root": raw_root,
    }


def _inventory(tmp_path: Path, asset_text: str, callee: str = "request") -> dict[str, object]:
    paths = _inputs(tmp_path, asset_text, callee)
    return inventory_guild_progression_helper_definition(
        callsite_review_path=paths["callsite_review"],
        public_callsite_path=paths["public_callsite"],
        private_callsite_path=paths["private_callsite"],
        public_recovery_path=paths["public_recovery"],
        private_recovery_path=paths["private_recovery"],
        raw_root=paths["raw_root"],
        private_output_path=tmp_path / "private-output.json",
        receipt_output_path=tmp_path / "public-output.json",
    )


def test_definition_inventory_is_scalar_free_and_probe_blocked(tmp_path: Path) -> None:
    receipt = _inventory(
        tmp_path,
        (
            'function request(url,data){return fetch(url,{method:"POST",'
            'body:JSON.stringify(data)})};request("/api/guilds/progression",{id:1});'
        ),
    )

    evidence = receipt["cross_definition_evidence"]
    assert evidence["definition_candidate_count"] == 1
    assert evidence["definition_kinds"] == ["function_declaration"]
    assert evidence["helper_definition_candidate_observed"] is True
    assert receipt["summary"]["integrity_check_count"] == 36
    assert receipt["summary"][
        "ready_for_guild_progression_helper_definition_review"
    ] is True
    assert receipt["summary"]["ready_for_bounded_progression_route_probe"] is False
    encoded = json.dumps(receipt)
    assert "function request" not in encoded
    assert '"callee"' not in encoded
    assert '"span"' not in encoded


def test_alias_candidate_does_not_resolve_helper_identity(tmp_path: Path) -> None:
    receipt = _inventory(
        tmp_path,
        'const request=transport;request("/api/guilds/progression");',
    )

    assert receipt["summary"]["alias_candidate_count"] == 1
    assert receipt["summary"]["guild_progression_helper_identity_resolved"] is False
    assert receipt["decision_boundary"]["ready_for_bounded_progression_route_probe"] is False


def test_private_callee_hash_mismatch_is_rejected(tmp_path: Path) -> None:
    paths = _inputs(tmp_path, 'function request(){};request("x");')
    private_payload = json.loads(paths["private_callsite"].read_text())
    private_payload["occurrences"][0]["call_candidates"][0]["callee"] = "other"
    private_body = _write_json(paths["private_callsite"], private_payload)
    public_payload = json.loads(paths["public_callsite"].read_text())
    public_payload["source_private_inventory_sha256"] = _sha256(private_body)
    public_body = _write_json(paths["public_callsite"], public_payload)
    review_payload = json.loads(paths["callsite_review"].read_text())
    review_payload["source_inventory_sha256"] = _sha256(public_body)
    _write_json(paths["callsite_review"], review_payload)

    with pytest.raises(ValueError, match="callee hash mismatch"):
        inventory_guild_progression_helper_definition(
            callsite_review_path=paths["callsite_review"],
            public_callsite_path=paths["public_callsite"],
            private_callsite_path=paths["private_callsite"],
            public_recovery_path=paths["public_recovery"],
            private_recovery_path=paths["private_recovery"],
            raw_root=paths["raw_root"],
            private_output_path=tmp_path / "private-output.json",
            receipt_output_path=tmp_path / "public-output.json",
        )


def test_review_overclaim_is_rejected(tmp_path: Path) -> None:
    paths = _inputs(tmp_path, 'function request(){};request("x");')
    review_payload = json.loads(paths["callsite_review"].read_text())
    review_payload["summary"]["ready_for_bounded_progression_route_probe"] = True
    _write_json(paths["callsite_review"], review_payload)

    with pytest.raises(ValueError, match="call-site review summary mismatch"):
        inventory_guild_progression_helper_definition(
            callsite_review_path=paths["callsite_review"],
            public_callsite_path=paths["public_callsite"],
            private_callsite_path=paths["private_callsite"],
            public_recovery_path=paths["public_recovery"],
            private_recovery_path=paths["private_recovery"],
            raw_root=paths["raw_root"],
            private_output_path=tmp_path / "private-output.json",
            receipt_output_path=tmp_path / "public-output.json",
        )
