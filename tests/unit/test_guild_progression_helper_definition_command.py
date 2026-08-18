from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import coa_workbench.collector.guild_progression_helper_definition_command as command


def _body(payload: object) -> bytes:
    return (json.dumps(payload, sort_keys=True) + "\n").encode()


def _write(path: Path, payload: object) -> bytes:
    body = _body(payload)
    path.write_bytes(body)
    return body


def _checks(count: int) -> dict[str, bool]:
    return {f"check_{index}": True for index in range(count)}


def _files(tmp_path: Path) -> dict[str, Path]:
    public_recovery_path = tmp_path / "public-recovery.json"
    private_recovery_path = tmp_path / "private-recovery.json"
    public_recovery_body = _write(public_recovery_path, {"kind": "public"})
    private_recovery_body = _write(private_recovery_path, {"kind": "private"})

    private_callsite_path = tmp_path / "private-callsite.json"
    private_callsite_body = _write(
        private_callsite_path,
        {
            "schema_version": 1,
            "inventory_kind": "guild_progression_helper_callsite_inventory_private",
            "inventory_version": "guild-progression-helper-callsite-inventory-v1",
            "route": "/api/guilds/progression",
            "source_public_recovery_name": public_recovery_path.name,
            "source_public_recovery_sha256": hashlib.sha256(public_recovery_body).hexdigest(),
            "source_private_recovery_name": private_recovery_path.name,
            "source_private_recovery_sha256": hashlib.sha256(private_recovery_body).hexdigest(),
        },
    )
    public_callsite_path = tmp_path / "public-callsite.json"
    public_callsite_body = _write(
        public_callsite_path,
        {
            "schema_version": 1,
            "inventory_kind": "guild_progression_helper_callsite_inventory",
            "inventory_version": "guild-progression-helper-callsite-inventory-v1",
            "source_private_inventory_name": private_callsite_path.name,
            "source_private_inventory_sha256": hashlib.sha256(private_callsite_body).hexdigest(),
            "source_public_recovery_name": public_recovery_path.name,
            "source_public_recovery_sha256": hashlib.sha256(public_recovery_body).hexdigest(),
            "source_private_recovery_name": private_recovery_path.name,
            "source_private_recovery_sha256": hashlib.sha256(private_recovery_body).hexdigest(),
            "target": {
                "guild_label": "Argentum",
                "route_template": "/api/guilds/progression",
                "asset_url_published": False,
                "source_guild_id_published": False,
                "raw_context_published": False,
                "raw_callee_published": False,
                "source_scalar_values_published": False,
            },
            "request_contract": {
                "network_requests_performed": False,
                "raw_archive_only": True,
                "max_occurrences": 20,
                "max_call_depth": 8,
                "private_context_chars_per_side": 2048,
            },
            "integrity_checks": _checks(32),
            "decision_boundary": {
                "status": "guild_progression_helper_callsite_inventory_observed",
                "guild_progression_route_candidate_observed": True,
                "guild_progression_usage_context_reviewed": True,
                "guild_progression_helper_callsite_inventory_observed": True,
                "guild_progression_method_candidate_unambiguous": True,
                "guild_progression_request_shape_verified": False,
                "ready_for_guild_progression_helper_callsite_review": True,
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
    review_path = tmp_path / "review.json"
    _write(
        review_path,
        {
            "schema_version": 1,
            "review_kind": "guild_progression_helper_callsite_review",
            "review_version": "guild-progression-helper-callsite-review-v1",
            "source_inventory_name": public_callsite_path.name,
            "source_inventory_sha256": hashlib.sha256(public_callsite_body).hexdigest(),
            "source_public_recovery_name": public_recovery_path.name,
            "source_public_recovery_sha256": hashlib.sha256(public_recovery_body).hexdigest(),
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
            "decision_boundary": {
                "status": "guild_progression_helper_callsite_reviewed_probe_blocked",
                "guild_progression_route_candidate_observed": True,
                "guild_progression_usage_context_reviewed": True,
                "guild_progression_helper_callsite_inventory_observed": True,
                "guild_progression_helper_callsite_reviewed": True,
                "guild_progression_method_candidate_unambiguous": True,
                "guild_progression_http_method_candidate": "POST",
                "guild_progression_helper_identity_resolved": False,
                "guild_progression_request_payload_mapping_resolved": False,
                "guild_progression_request_shape_verified": False,
                "ready_for_guild_progression_helper_definition_inventory": True,
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
    return {
        "review": review_path,
        "public_callsite": public_callsite_path,
        "private_callsite": private_callsite_path,
        "public_recovery": public_recovery_path,
        "private_recovery": private_recovery_path,
    }


def _run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, **kwargs: object) -> object:
    paths = _files(tmp_path)
    monkeypatch.setattr(command, "_inventory", lambda **values: values)
    return command.inventory_guild_progression_helper_definition(
        callsite_review_path=paths["review"],
        public_callsite_path=paths["public_callsite"],
        private_callsite_path=paths["private_callsite"],
        public_recovery_path=paths["public_recovery"],
        private_recovery_path=paths["private_recovery"],
        raw_root=tmp_path / "raw",
        private_output_path=tmp_path / "private-output.json",
        receipt_output_path=tmp_path / "public-output.json",
        **kwargs,
    )


def test_valid_chain_reaches_inventory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    result = _run(tmp_path, monkeypatch)
    assert result["max_symbol_occurrences"] == 500
    assert result["expected_guild_label"] == "Argentum"


def test_review_boundary_overclaim_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = _files(tmp_path)
    review = json.loads(paths["review"].read_text())
    review["decision_boundary"]["ready_for_bounded_progression_route_probe"] = True
    _write(paths["review"], review)
    monkeypatch.setattr(command, "_inventory", lambda **values: values)
    with pytest.raises(ValueError, match="call-site review boundary mismatch"):
        command.inventory_guild_progression_helper_definition(
            callsite_review_path=paths["review"],
            public_callsite_path=paths["public_callsite"],
            private_callsite_path=paths["private_callsite"],
            public_recovery_path=paths["public_recovery"],
            private_recovery_path=paths["private_recovery"],
            raw_root=tmp_path / "raw",
            private_output_path=tmp_path / "private-output.json",
            receipt_output_path=tmp_path / "public-output.json",
        )


def test_unbounded_symbol_limit_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ValueError, match="max_symbol_occurrences"):
        _run(tmp_path, monkeypatch, max_symbol_occurrences=10001)


def test_recovery_hash_drift_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = _files(tmp_path)
    paths["public_recovery"].write_text("{}\n")
    monkeypatch.setattr(command, "_inventory", lambda **values: values)
    with pytest.raises(ValueError, match="public recovery SHA-256 mismatch"):
        command.inventory_guild_progression_helper_definition(
            callsite_review_path=paths["review"],
            public_callsite_path=paths["public_callsite"],
            private_callsite_path=paths["private_callsite"],
            public_recovery_path=paths["public_recovery"],
            private_recovery_path=paths["private_recovery"],
            raw_root=tmp_path / "raw",
            private_output_path=tmp_path / "private-output.json",
            receipt_output_path=tmp_path / "public-output.json",
        )
