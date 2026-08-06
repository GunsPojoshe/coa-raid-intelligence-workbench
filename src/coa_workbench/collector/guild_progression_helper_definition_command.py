from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .guild_progression_callsite_contract import (
    document_hashes,
    expect,
    load_json,
    object_value,
    require_checks,
    sha256_value,
)
from .guild_progression_helper_definition_inventory import (
    inventory_guild_progression_helper_definition as _inventory,
)

_ROUTE = "/api/guilds/progression"
_REVIEW_KIND = "guild_progression_helper_callsite_review"
_REVIEW_VERSION = "guild-progression-helper-callsite-review-v1"
_CALLSITE_KIND = "guild_progression_helper_callsite_inventory"
_CALLSITE_PRIVATE_KIND = f"{_CALLSITE_KIND}_private"
_CALLSITE_VERSION = "guild-progression-helper-callsite-inventory-v1"
_FALSE_SUMMARY_GATES = {
    "ready_for_bounded_progression_route_probe": False,
    "guild_api_route_semantics_verified": False,
    "pagination_semantics_verified": False,
    "termination_semantics_verified": False,
    "completeness_verified": False,
    "ready_for_full_guild_crawl": False,
    "planner_scoring_allowed": False,
}
_FALSE_BOUNDARY_GATES = {
    **_FALSE_SUMMARY_GATES,
    "automatic_full_guild_crawl_allowed": False,
    "ready_for_multi_report_character_graph": False,
    "ready_for_performance_model": False,
    "ready_for_bis25_scoring": False,
}


def _validate_review(review: Mapping[str, Any]) -> None:
    expect(
        review,
        {
            "schema_version": 1,
            "review_kind": _REVIEW_KIND,
            "review_version": _REVIEW_VERSION,
        },
        "call-site review",
    )
    require_checks(review.get("integrity_checks"), 36, "call-site review checks")
    summary = object_value(review.get("summary"), "call-site review summary")
    expect(
        summary,
        {
            "all_integrity_checks_passed": True,
            "integrity_check_count": 36,
            "guild_progression_helper_callsite_reviewed": True,
            "method_candidate_unambiguous": True,
            "http_method_candidate": "POST",
            "helper_identity_resolved": False,
            "request_payload_mapping_resolved": False,
            "request_shape_sufficient_for_bounded_probe": False,
            "ready_for_guild_progression_helper_definition_inventory": True,
            **_FALSE_SUMMARY_GATES,
            "contains_raw_callee": False,
            "contains_raw_context": False,
            "contains_source_scalar_values": False,
        },
        "call-site review summary",
    )
    boundary = object_value(review.get("decision_boundary"), "call-site review boundary")
    expect(
        boundary,
        {
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
            **_FALSE_BOUNDARY_GATES,
        },
        "call-site review boundary",
    )


def _validate_public_callsite(
    callsite: Mapping[str, Any],
    expected_guild_label: str,
) -> None:
    expect(
        callsite,
        {
            "schema_version": 1,
            "inventory_kind": _CALLSITE_KIND,
            "inventory_version": _CALLSITE_VERSION,
        },
        "public call-site inventory",
    )
    require_checks(callsite.get("integrity_checks"), 32, "public call-site checks")
    target = object_value(callsite.get("target"), "public call-site target")
    expect(
        target,
        {
            "guild_label": expected_guild_label,
            "route_template": _ROUTE,
            "asset_url_published": False,
            "source_guild_id_published": False,
            "raw_context_published": False,
            "raw_callee_published": False,
            "source_scalar_values_published": False,
        },
        "public call-site target",
    )
    request = object_value(callsite.get("request_contract"), "public call-site request")
    expect(
        request,
        {
            "network_requests_performed": False,
            "raw_archive_only": True,
            "max_occurrences": 20,
            "max_call_depth": 8,
            "private_context_chars_per_side": 2048,
        },
        "public call-site request",
    )
    boundary = object_value(callsite.get("decision_boundary"), "public call-site boundary")
    expect(
        boundary,
        {
            "status": "guild_progression_helper_callsite_inventory_observed",
            "guild_progression_route_candidate_observed": True,
            "guild_progression_usage_context_reviewed": True,
            "guild_progression_helper_callsite_inventory_observed": True,
            "guild_progression_method_candidate_unambiguous": True,
            "guild_progression_request_shape_verified": False,
            "ready_for_guild_progression_helper_callsite_review": True,
            **_FALSE_BOUNDARY_GATES,
        },
        "public call-site boundary",
    )


def _verify_hash(value: object, body: bytes, label: str) -> None:
    declared = sha256_value(value, label)
    if declared not in document_hashes(body):
        raise ValueError(f"{label} mismatch")


def inventory_guild_progression_helper_definition(
    *,
    callsite_review_path: Path,
    public_callsite_path: Path,
    private_callsite_path: Path,
    public_recovery_path: Path,
    private_recovery_path: Path,
    raw_root: Path,
    private_output_path: Path,
    receipt_output_path: Path,
    expected_guild_label: str = "Argentum",
    max_symbol_occurrences: int = 500,
    max_definition_candidates: int = 50,
    max_definition_span_chars: int = 131072,
    private_context_chars: int = 4096,
) -> dict[str, Any]:
    """Validate the exact blocked chain before running the offline inventory."""
    if not 1 <= max_symbol_occurrences <= 10000:
        raise ValueError("max_symbol_occurrences must be between 1 and 10000")

    review, review_body = load_json(callsite_review_path, "call-site review")
    public_callsite, public_callsite_body = load_json(
        public_callsite_path,
        "public call-site inventory",
    )
    private_callsite, private_callsite_body = load_json(
        private_callsite_path,
        "private call-site inventory",
    )
    _, public_recovery_body = load_json(public_recovery_path, "public recovery")
    _, private_recovery_body = load_json(private_recovery_path, "private recovery")

    _validate_review(review)
    _validate_public_callsite(public_callsite, expected_guild_label)
    expect(
        review,
        {
            "source_inventory_name": public_callsite_path.name,
            "source_public_recovery_name": public_recovery_path.name,
        },
        "call-site review source binding",
    )
    expect(
        public_callsite,
        {
            "source_private_inventory_name": private_callsite_path.name,
            "source_public_recovery_name": public_recovery_path.name,
            "source_private_recovery_name": private_recovery_path.name,
        },
        "public call-site source binding",
    )
    expect(
        private_callsite,
        {
            "schema_version": 1,
            "inventory_kind": _CALLSITE_PRIVATE_KIND,
            "inventory_version": _CALLSITE_VERSION,
            "route": _ROUTE,
            "source_public_recovery_name": public_recovery_path.name,
            "source_private_recovery_name": private_recovery_path.name,
        },
        "private call-site source binding",
    )

    _verify_hash(
        review.get("source_inventory_sha256"),
        public_callsite_body,
        "review public inventory SHA-256",
    )
    _verify_hash(
        review.get("source_public_recovery_sha256"),
        public_recovery_body,
        "review public recovery SHA-256",
    )
    _verify_hash(
        public_callsite.get("source_private_inventory_sha256"),
        private_callsite_body,
        "public call-site private inventory SHA-256",
    )
    _verify_hash(
        public_callsite.get("source_public_recovery_sha256"),
        public_recovery_body,
        "public call-site recovery SHA-256",
    )
    _verify_hash(
        public_callsite.get("source_private_recovery_sha256"),
        private_recovery_body,
        "public call-site private recovery SHA-256",
    )
    _verify_hash(
        private_callsite.get("source_public_recovery_sha256"),
        public_recovery_body,
        "private call-site public recovery SHA-256",
    )
    _verify_hash(
        private_callsite.get("source_private_recovery_sha256"),
        private_recovery_body,
        "private call-site private recovery SHA-256",
    )

    return _inventory(
        callsite_review_path=callsite_review_path,
        public_callsite_path=public_callsite_path,
        private_callsite_path=private_callsite_path,
        public_recovery_path=public_recovery_path,
        private_recovery_path=private_recovery_path,
        raw_root=raw_root,
        private_output_path=private_output_path,
        receipt_output_path=receipt_output_path,
        expected_guild_label=expected_guild_label,
        max_symbol_occurrences=max_symbol_occurrences,
        max_definition_candidates=max_definition_candidates,
        max_definition_span_chars=max_definition_span_chars,
        private_context_chars=private_context_chars,
    )


__all__ = ["inventory_guild_progression_helper_definition"]
