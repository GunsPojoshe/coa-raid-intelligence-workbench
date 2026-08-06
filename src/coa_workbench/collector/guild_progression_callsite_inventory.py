from __future__ import annotations

from pathlib import Path
from typing import Any

from .guild_progression_callsite_contract import (
    FORBIDDEN_PUBLIC_FIELDS,
    KIND,
    PRIVATE_KIND,
    ROUTE,
    VERSION,
    canonical_lf,
    document_hashes,
    generated_at,
    load_asset,
    load_json,
    property_names,
    sha256,
    sha256_value,
    validate_recovery,
    validate_usage_review,
    write_json,
)
from .guild_progression_js_index import (
    assignment_candidate,
    call_candidates,
    function_candidate,
    openers_of,
    private_excerpt,
    property_markers,
    scan_structure,
    string_span_for,
)


def _positions(text: str, max_occurrences: int) -> list[int]:
    positions: list[int] = []
    cursor = 0
    while (position := text.find(ROUTE, cursor)) >= 0:
        positions.append(position)
        if len(positions) > max_occurrences:
            raise ValueError("progression route occurrence count exceeds bounded maximum")
        cursor = position + len(ROUTE)
    if not positions:
        raise ValueError("progression route candidate was not found in recovered asset")
    return positions


def _checks() -> dict[str, bool]:
    names = (
        "usage_review_contract_verified usage_review_integrity_checks_verified "
        "usage_review_blocked_boundary_verified usage_review_privacy_boundary_verified "
        "public_profiled_recovery_verified public_recovery_integrity_checks_verified "
        "public_recovery_privacy_boundary_verified private_profiled_recovery_sha256_verified "
        "private_recovery_scalar_boundary_verified usage_review_public_recovery_binding_verified "
        "asset_content_manifest_unique asset_content_manifest_verified "
        "asset_payload_path_confined_to_raw_root asset_payload_sha256_verified "
        "asset_uncompressed_byte_count_verified route_occurrence_count_bounded "
        "route_occurrence_observed route_string_literal_verified "
        "structural_delimiter_index_completed helper_callsite_scan_bounded "
        "raw_helper_context_kept_private public_receipt_contains_no_raw_context "
        "public_receipt_contains_no_raw_callee public_receipt_scalar_boundary_preserved "
        "network_requests_performed_false route_probe_remains_disabled "
        "route_semantics_not_overclaimed pagination_not_overclaimed "
        "termination_not_overclaimed completeness_not_overclaimed "
        "full_crawl_remains_disabled planner_scoring_remains_disabled"
    ).split()
    checks = {name: True for name in names}
    if len(checks) != 32:
        raise RuntimeError("helper/call-site integrity-check contract drift")
    return checks


def inventory_guild_progression_helper_callsite(
    *,
    usage_review_path: Path,
    public_recovery_path: Path,
    private_recovery_path: Path,
    raw_root: Path,
    private_output_path: Path,
    receipt_output_path: Path,
    expected_guild_label: str = "Argentum",
    max_occurrences: int = 20,
    max_call_depth: int = 8,
    private_context_chars: int = 2048,
) -> dict[str, Any]:
    """Inventory structural helper/call-site candidates without network requests."""
    if not 1 <= max_occurrences <= 100:
        raise ValueError("max_occurrences must be between 1 and 100")
    if not 1 <= max_call_depth <= 32:
        raise ValueError("max_call_depth must be between 1 and 32")
    if not 512 <= private_context_chars <= 16384:
        raise ValueError("private_context_chars must be between 512 and 16384")

    review, review_body = load_json(usage_review_path, "progression usage review")
    validate_usage_review(review)
    public, public_body = load_json(public_recovery_path, "public profiled recovery")
    private, private_body = load_json(private_recovery_path, "private profiled recovery")
    payload_hash = validate_recovery(public, private, private_body, expected_guild_label)
    declared_recovery = sha256_value(
        review.get("source_public_recovery_sha256"),
        "review recovery SHA-256",
    )
    if declared_recovery not in document_hashes(public_body):
        raise ValueError("usage review public recovery SHA-256 mismatch")

    asset_body, manifest_path = load_asset(raw_root, payload_hash)
    text = asset_body.decode("utf-8", errors="ignore").replace("\\/", "/")
    positions = _positions(text, max_occurrences)
    index = scan_structure(text)

    private_rows: list[dict[str, Any]] = []
    public_rows: list[dict[str, Any]] = []
    methods: set[str] = set()
    call_classes: set[str] = set()
    assignment_kinds: set[str] = set()
    aggregate_markers: set[str] = set()
    total_calls = direct_calls = function_count = 0

    for occurrence_index, position in enumerate(positions, 1):
        span = string_span_for(position, index.string_spans)
        assignment = assignment_candidate(text, span)
        function = function_candidate(text, index, position)
        braces = openers_of(text, index, position, "{")
        context_value = text[braces[0] : index.pairs[braces[0]] + 1] if braces else ""
        if len(context_value) > 131072:
            context_value = text[max(0, position - 65536) : position + 65536]
        context_markers = property_markers(context_value)
        calls = call_candidates(text, index, position, span, max_call_depth)

        total_calls += len(calls)
        direct_calls += bool(calls)
        function_count += bool(function["observed"])
        assignment_kinds.add(assignment["kind"])
        aggregate_markers.update(context_markers)
        for call in calls:
            methods.update(call["methods"])
            call_classes.add(call["class"])
            aggregate_markers.update(call["property_markers"])

        start = min([span.start, *(call["start"] for call in calls)])
        end = max([span.end, *(call["end"] for call in calls)])
        envelope = text[start:end]
        context, context_start, context_end = private_excerpt(
            text,
            start,
            end,
            private_context_chars,
        )
        private_calls = []
        for call in calls:
            raw_call, raw_start, raw_end = private_excerpt(
                text,
                call["start"],
                call["end"],
                private_context_chars,
            )
            private_calls.append(
                {
                    **call,
                    "raw_excerpt": raw_call,
                    "raw_excerpt_start": raw_start,
                    "raw_excerpt_end": raw_end,
                    "raw_excerpt_sha256": sha256(raw_call.encode()),
                }
            )
        private_rows.append(
            {
                "occurrence_index": occurrence_index,
                "route_character_offset": position,
                "assignment": assignment,
                "enclosing_function": function,
                "context_property_markers": context_markers,
                "call_candidates": private_calls,
                "structural_envelope": {
                    "start": start,
                    "end": end,
                    "text": envelope,
                    "sha256": sha256(envelope.encode()),
                },
                "private_excerpt": {
                    "start": context_start,
                    "end": context_end,
                    "text": context,
                    "sha256": sha256(context.encode()),
                },
            }
        )
        public_rows.append(
            {
                "occurrence_index": occurrence_index,
                "string_literal_verified": True,
                "string_quote_class": {
                    "'": "single_quote",
                    '"': "double_quote",
                    "`": "template_literal",
                }[span.quote],
                "assignment_kind": assignment["kind"],
                "assignment_symbol_sha256": assignment["symbol_sha256"],
                "property_name_sha256": assignment["property_sha256"],
                "context_property_markers": context_markers,
                "enclosing_function_candidate": function["observed"],
                "function_candidate_kind": function["kind"],
                "function_span_sha256": function["span_sha256"],
                "function_character_count": function["character_count"],
                "function_prefix_sha256": function["prefix_sha256"],
                "structural_envelope_sha256": sha256(envelope.encode()),
                "structural_envelope_character_count": len(envelope),
                "call_candidate_count": len(calls),
                "call_candidates": [
                    {
                        "call_depth": call["depth"],
                        "callee_class": call["class"],
                        "callee_sha256": call["callee_sha256"],
                        "call_span_sha256": call["span_sha256"],
                        "call_character_count": call["character_count"],
                        "method_candidates": call["methods"],
                        "method_evidence": call["method_evidence"],
                        "route_direct_argument_candidate": call["direct_argument"],
                        "property_markers": call["property_markers"],
                        "contains_raw_callee": False,
                        "contains_raw_call_text": False,
                    }
                    for call in calls
                ],
                "contains_raw_context": False,
                "contains_raw_callee": False,
                "contains_source_scalar_values": False,
            }
        )

    method_unambiguous = len(methods) == 1 and direct_calls > 0
    candidate_observed = total_calls > 0 or function_count > 0 or assignment_kinds != {"none"}
    private_payload = {
        "schema_version": 1,
        "inventory_kind": PRIVATE_KIND,
        "inventory_version": VERSION,
        "generated_at": generated_at(),
        "source_usage_review_name": usage_review_path.name,
        "source_usage_review_sha256": sha256(review_body),
        "source_public_recovery_name": public_recovery_path.name,
        "source_public_recovery_sha256": sha256(canonical_lf(public_body)),
        "source_private_recovery_name": private_recovery_path.name,
        "source_private_recovery_sha256": sha256(private_body),
        "asset_payload_hash": payload_hash,
        "asset_content_manifest_path": str(manifest_path),
        "route": ROUTE,
        "occurrences": private_rows,
        "summary": {
            "occurrence_count": len(private_rows),
            "call_candidate_count": total_calls,
            "direct_invocation_candidate_count": direct_calls,
            "enclosing_function_candidate_count": function_count,
            "method_candidates": sorted(methods),
            "call_classes": sorted(call_classes),
            "assignment_kinds": sorted(assignment_kinds),
            "property_markers": sorted(aggregate_markers),
            "contains_source_scalar_values": True,
            "network_requests_performed": False,
        },
    }
    private_body_out = write_json(private_output_path, private_payload)

    false_gates = {
        "ready_for_bounded_progression_route_probe": False,
        "guild_api_route_semantics_verified": False,
        "pagination_semantics_verified": False,
        "termination_semantics_verified": False,
        "completeness_verified": False,
        "ready_for_full_guild_crawl": False,
        "planner_scoring_allowed": False,
    }
    evidence = {
        "occurrence_count": len(public_rows),
        "call_candidate_count": total_calls,
        "direct_invocation_candidate_count": direct_calls,
        "enclosing_function_candidate_count": function_count,
        "helper_callsite_candidate_observed": candidate_observed,
        "method_candidates": sorted(methods),
        "method_candidate_count": len(methods),
        "method_candidate_unambiguous": method_unambiguous,
        "call_classes": sorted(call_classes),
        "assignment_kinds": sorted(assignment_kinds),
        "property_markers": sorted(aggregate_markers),
        "contains_raw_context": False,
        "contains_raw_callee": False,
        "contains_source_scalar_values": False,
    }
    checks = _checks()
    receipt = {
        "schema_version": 1,
        "inventory_kind": KIND,
        "inventory_version": VERSION,
        "generated_at": generated_at(),
        "source_usage_review_name": usage_review_path.name,
        "source_usage_review_sha256": sha256(canonical_lf(review_body)),
        "source_public_recovery_name": public_recovery_path.name,
        "source_public_recovery_sha256": sha256(canonical_lf(public_body)),
        "source_private_recovery_name": private_recovery_path.name,
        "source_private_recovery_sha256": sha256(private_body),
        "source_private_inventory_name": private_output_path.name,
        "source_private_inventory_sha256": sha256(private_body_out),
        "target": {
            "guild_label": expected_guild_label,
            "route_template": ROUTE,
            "asset_url_published": False,
            "source_guild_id_published": False,
            "raw_context_published": False,
            "raw_callee_published": False,
            "source_scalar_values_published": False,
        },
        "request_contract": {
            "network_requests_performed": False,
            "raw_archive_only": True,
            "max_occurrences": max_occurrences,
            "max_call_depth": max_call_depth,
            "private_context_chars_per_side": private_context_chars,
        },
        "occurrences": public_rows,
        "cross_occurrence_evidence": evidence,
        "integrity_checks": checks,
        "summary": {
            "all_integrity_checks_passed": True,
            "integrity_check_count": len(checks),
            "route_occurrence_count": len(public_rows),
            "call_candidate_count": total_calls,
            "direct_invocation_candidate_count": direct_calls,
            "enclosing_function_candidate_count": function_count,
            "helper_callsite_candidate_observed": candidate_observed,
            "method_candidate_count": len(methods),
            "method_candidate_unambiguous": method_unambiguous,
            "ready_for_guild_progression_helper_callsite_review": True,
            **false_gates,
            "contains_raw_context": False,
            "contains_raw_callee": False,
            "contains_source_scalar_values": False,
            "network_requests_performed": False,
        },
        "decision_boundary": {
            "status": "guild_progression_helper_callsite_inventory_observed",
            "guild_progression_route_candidate_observed": True,
            "guild_progression_usage_context_reviewed": True,
            "guild_progression_helper_callsite_inventory_observed": True,
            "ready_for_guild_progression_helper_callsite_review": True,
            "guild_progression_method_candidate_unambiguous": method_unambiguous,
            "guild_progression_request_shape_verified": False,
            **false_gates,
            "automatic_full_guild_crawl_allowed": False,
            "ready_for_multi_report_character_graph": False,
            "ready_for_performance_model": False,
            "ready_for_bis25_scoring": False,
        },
    }
    if property_names(receipt) & FORBIDDEN_PUBLIC_FIELDS:
        raise ValueError("public helper/call-site receipt contains forbidden fields")
    write_json(receipt_output_path, receipt)
    return receipt


__all__ = ["inventory_guild_progression_helper_callsite"]
