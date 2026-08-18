from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import pytest

from coa_workbench.collector.guild_progression_callsite_inventory import (
    inventory_guild_progression_helper_callsite,
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


def _inputs(tmp_path: Path, asset_text: str) -> tuple[Path, Path, Path, Path]:
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
    manifest_path = folder / f"{payload_hash}.content.json"
    _write_json(
        manifest_path,
        {
            "schema_version": 1,
            "endpoint_code": "guild_identity_asset_recovery",
            "payload_hash": payload_hash,
            "payload_path": payload_path.relative_to(raw_root).as_posix(),
            "compression": "gzip",
            "bytes_uncompressed": len(payload),
        },
    )

    private_path = tmp_path / "private-recovery.json"
    private_body = _write_json(
        private_path,
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
    public_path = tmp_path / "public-recovery.json"
    public_body = _write_json(
        public_path,
        {
            "schema_version": 1,
            "recovery_kind": "guild_identity_asset_profiled_recovery",
            "recovery_version": "guild-identity-asset-profiled-recovery-v1",
            "source_private_recovery_sha256": _sha256(private_body),
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
    review_path = tmp_path / "usage-review.json"
    _write_json(
        review_path,
        {
            "schema_version": 1,
            "review_kind": "guild_progression_usage_context_review",
            "review_version": "guild-progression-usage-context-review-v1",
            "source_public_recovery_sha256": _sha256(public_body),
            "usage_review": {
                "route_template": _ROUTE,
                "occurrence_count": 1,
                "call_style_candidates": ["literal_reference"],
                "method_candidates": [],
                "method_candidate_unambiguous": False,
                "method_resolution_status": "unresolved",
                "actual_invocation_observed": False,
                "literal_reference_only": True,
                "request_shape_sufficient_for_bounded_probe": False,
                "usage_context_reviewed": True,
                "route_semantics_verified": False,
                "contains_raw_context": False,
                "contains_source_scalar_values": False,
                "blockers": [
                    "http_method_unresolved",
                    "literal_reference_without_call_site",
                    "invocation_shape_unresolved",
                ],
            },
            "integrity_checks": _checks(30),
            "summary": {
                "all_integrity_checks_passed": True,
                "integrity_check_count": 30,
                "guild_progression_usage_context_reviewed": True,
                "method_candidate_unambiguous": False,
                "actual_invocation_observed": False,
                "request_shape_sufficient_for_bounded_probe": False,
                "ready_for_bounded_progression_route_probe": False,
                "guild_api_route_semantics_verified": False,
                "pagination_semantics_verified": False,
                "termination_semantics_verified": False,
                "completeness_verified": False,
                "ready_for_full_guild_crawl": False,
                "planner_scoring_allowed": False,
                "contains_raw_context": False,
                "contains_source_scalar_values": False,
            },
            "decision_boundary": {
                "status": "guild_progression_usage_reviewed_probe_blocked",
                "guild_progression_route_candidate_observed": True,
                "guild_progression_usage_context_observed": True,
                "guild_progression_usage_context_reviewed": True,
                "guild_progression_method_candidate_unambiguous": False,
                "guild_progression_request_shape_verified": False,
                "ready_for_bounded_progression_route_probe": False,
                "guild_api_route_semantics_verified": False,
                "pagination_semantics_verified": False,
                "termination_semantics_verified": False,
                "completeness_verified": False,
                "automatic_full_guild_crawl_allowed": False,
                "ready_for_full_guild_crawl": False,
                "ready_for_multi_report_character_graph": False,
                "ready_for_performance_model": False,
                "ready_for_bis25_scoring": False,
                "planner_scoring_allowed": False,
            },
        },
    )
    return review_path, public_path, private_path, raw_root


def _inventory(tmp_path: Path, asset_text: str) -> dict[str, object]:
    review, public, private, raw_root = _inputs(tmp_path, asset_text)
    return inventory_guild_progression_helper_callsite(
        usage_review_path=review,
        public_recovery_path=public,
        private_recovery_path=private,
        raw_root=raw_root,
        private_output_path=tmp_path / "private-output.json",
        receipt_output_path=tmp_path / "public-output.json",
    )


def test_fetch_post_call_is_classified_without_authorizing_probe(tmp_path: Path) -> None:
    receipt = _inventory(
        tmp_path,
        'const load=()=>fetch("/api/guilds/progression",{method:"POST",body:x});',
    )

    evidence = receipt["cross_occurrence_evidence"]
    boundary = receipt["decision_boundary"]
    assert evidence["call_candidate_count"] == 1
    assert evidence["direct_invocation_candidate_count"] == 1
    assert evidence["method_candidates"] == ["POST"]
    assert evidence["method_candidate_unambiguous"] is True
    assert evidence["call_classes"] == ["fetch_call"]
    assert boundary["guild_progression_method_candidate_unambiguous"] is True
    assert boundary["ready_for_bounded_progression_route_probe"] is False
    assert boundary["guild_api_route_semantics_verified"] is False


def test_member_post_call_is_classified(tmp_path: Path) -> None:
    receipt = _inventory(
        tmp_path,
        'client.post("/api/guilds/progression",{data:x});',
    )

    evidence = receipt["cross_occurrence_evidence"]
    assert evidence["call_classes"] == ["http_member_call"]
    assert evidence["method_candidates"] == ["POST"]
    assert evidence["method_candidate_unambiguous"] is True


def test_url_property_without_call_stays_method_unresolved(tmp_path: Path) -> None:
    receipt = _inventory(
        tmp_path,
        'const api={query:()=>({url:"/api/guilds/progression",params:{guildId:x}})};',
    )

    evidence = receipt["cross_occurrence_evidence"]
    occurrence = receipt["occurrences"][0]
    assert occurrence["assignment_kind"] == "url_property_value"
    assert occurrence["enclosing_function_candidate"] is True
    assert occurrence["function_candidate_kind"] == "concise_arrow_object_return"
    assert occurrence["context_property_markers"] == ["params", "url"]
    assert evidence["property_markers"] == ["params", "url"]
    assert evidence["call_candidate_count"] == 0
    assert evidence["helper_callsite_candidate_observed"] is True
    assert evidence["method_candidates"] == []
    assert evidence["method_candidate_unambiguous"] is False
    assert receipt["summary"]["ready_for_bounded_progression_route_probe"] is False


def test_fetch_without_method_is_classified_as_get_candidate(tmp_path: Path) -> None:
    receipt = _inventory(
        tmp_path,
        'const load=()=>fetch("/api/guilds/progression");',
    )

    evidence = receipt["cross_occurrence_evidence"]
    call = receipt["occurrences"][0]["call_candidates"][0]
    assert evidence["call_classes"] == ["fetch_call"]
    assert evidence["method_candidates"] == ["GET"]
    assert evidence["method_candidate_unambiguous"] is True
    assert call["method_evidence"] == ["fetch_default_method"]
    assert receipt["summary"]["ready_for_bounded_progression_route_probe"] is False


def test_generic_helper_call_does_not_infer_http_method(tmp_path: Path) -> None:
    receipt = _inventory(
        tmp_path,
        'request("/api/guilds/progression",{params:{guildId:x}});',
    )

    evidence = receipt["cross_occurrence_evidence"]
    assert evidence["call_classes"] == ["generic_helper_call"]
    assert evidence["method_candidates"] == []
    assert evidence["method_candidate_unambiguous"] is False
    assert evidence["property_markers"] == ["params"]
    assert receipt["decision_boundary"]["ready_for_bounded_progression_route_probe"] is False


def test_public_receipt_property_names_exclude_private_fields(tmp_path: Path) -> None:
    receipt = _inventory(
        tmp_path,
        'secretClient.post("/api/guilds/progression",{data:privateGuildId});',
    )

    def property_names(value: object) -> set[str]:
        if isinstance(value, dict):
            names = set(value)
            for child in value.values():
                names.update(property_names(child))
            return names
        if isinstance(value, list):
            names: set[str] = set()
            for child in value:
                names.update(property_names(child))
            return names
        return set()

    assert property_names(receipt).isdisjoint(
        {
            "asset_url",
            "callee",
            "context",
            "private_query",
            "raw_payload",
            "raw_records",
            "request_url",
            "source_guild_id",
            "symbol",
        }
    )


def test_public_receipt_contains_no_raw_context_or_callee(tmp_path: Path) -> None:
    receipt = _inventory(
        tmp_path,
        'secretClient.post("/api/guilds/progression",{data:privateGuildId});',
    )
    encoded = json.dumps(receipt)

    assert "secretClient" not in encoded
    assert "privateGuildId" not in encoded
    assert _ROUTE in encoded
    assert receipt["summary"]["contains_raw_context"] is False
    assert receipt["summary"]["contains_raw_callee"] is False
    assert receipt["summary"]["integrity_check_count"] == 32


def test_usage_review_overclaim_is_rejected(tmp_path: Path) -> None:
    review, public, private, raw_root = _inputs(
        tmp_path,
        'const route="/api/guilds/progression";',
    )
    payload = json.loads(review.read_text())
    payload["summary"]["ready_for_bounded_progression_route_probe"] = True
    _write_json(review, payload)

    with pytest.raises(ValueError, match="usage review summary mismatch"):
        inventory_guild_progression_helper_callsite(
            usage_review_path=review,
            public_recovery_path=public,
            private_recovery_path=private,
            raw_root=raw_root,
            private_output_path=tmp_path / "private-output.json",
            receipt_output_path=tmp_path / "public-output.json",
        )


def test_unbalanced_or_non_string_route_is_rejected(tmp_path: Path) -> None:
    review, public, private, raw_root = _inputs(
        tmp_path,
        "const value=/api/guilds/progression;",
    )

    with pytest.raises(ValueError, match="not inside a string literal"):
        inventory_guild_progression_helper_callsite(
            usage_review_path=review,
            public_recovery_path=public,
            private_recovery_path=private,
            raw_root=raw_root,
            private_output_path=tmp_path / "private-output.json",
            receipt_output_path=tmp_path / "public-output.json",
        )
