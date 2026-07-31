from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from coa_workbench.collector.guild_identity_search_capture_review import (
    _load_object,
    _required_list,
    _required_object,
    _sha256_bytes,
    _write_json,
)

_DECISION_VERSION = "guild-identity-decision-v1"
_MANIFEST_KIND = "public_report_manifest_capture"
_MANIFEST_VERSION = "public-report-manifest-v1"
_PRIVATE_MANIFEST_KIND = "public_report_manifest_private_batch"
_SNAPSHOT_KIND = "guild_identity_snapshot_review"
_SNAPSHOT_PRIVATE_KIND = "guild_identity_snapshot_private_review"
_SNAPSHOT_VERSION = "guild-identity-snapshot-review-v1"
_MAPPING_KIND = "guild_identity_search_mapping_review"
_MAPPING_PRIVATE_KIND = "guild_identity_search_mapping_review_private"
_MAPPING_VERSION = "guild-identity-search-mapping-review-v1"


def _required_integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return value


def _required_nonempty_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _identity_key(value: object) -> tuple[str, str] | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError("guild identity values must be null, integer or string scalars")
    return type(value).__name__, str(value)


def _normalized_name(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized if normalized else None


def _validate_public_manifest(
    manifest: Mapping[str, Any],
    *,
    private_manifest_body: bytes,
    expected_guild_label: str,
) -> tuple[int, int, int]:
    if manifest.get("schema_version") != 1:
        raise ValueError("public manifest schema mismatch")
    if manifest.get("manifest_kind") != _MANIFEST_KIND:
        raise ValueError("public manifest kind mismatch")
    if manifest.get("manifest_version") != _MANIFEST_VERSION:
        raise ValueError("public manifest version mismatch")

    target = _required_object(manifest.get("target"), "manifest.target")
    if target.get("guild_label") != expected_guild_label:
        raise ValueError("public manifest guild label mismatch")
    if target.get("guild_identity_status") != "operator_named_target_unresolved":
        raise ValueError("public manifest identity status mismatch")

    summary = _required_object(manifest.get("summary"), "manifest.summary")
    if summary.get("all_integrity_checks_passed") is not True:
        raise ValueError("public manifest integrity checks failed")
    if summary.get("contains_source_scalar_values") is not False:
        raise ValueError("public manifest receipt contains source scalar values")
    if summary.get("ready_for_guild_identity_review") is not True:
        raise ValueError("public manifest is not ready for guild identity review")

    boundary = _required_object(
        manifest.get("decision_boundary"),
        "manifest.decision_boundary",
    )
    if boundary.get("guild_identity_verified") is not False:
        raise ValueError("public manifest already marks guild identity verified")
    if boundary.get("ready_for_guild_filtering") is not False:
        raise ValueError("public manifest enables guild filtering prematurely")

    expected_private_hash = manifest.get("source_private_manifest_sha256")
    if not isinstance(expected_private_hash, str) or len(expected_private_hash) != 64:
        raise ValueError("public manifest private SHA-256 is missing")
    if _sha256_bytes(private_manifest_body) != expected_private_hash:
        raise ValueError("private manifest SHA-256 mismatch")

    guild_summary = _required_object(
        manifest.get("guild_field_summary"),
        "manifest.guild_field_summary",
    )
    exact_count = _required_integer(
        guild_summary.get("target_label_exact_match_report_count"),
        "target label exact match report count",
    )
    distinct_id_count = _required_integer(
        guild_summary.get("target_label_distinct_non_null_guild_id_count"),
        "target label distinct guild ID count",
    )
    report_count = _required_integer(
        summary.get("report_occurrence_count"),
        "manifest report occurrence count",
    )
    if exact_count <= 0:
        raise ValueError("public manifest has no target-label reports")
    if distinct_id_count != 1:
        raise ValueError("public manifest does not identify one target guild ID")
    return report_count, exact_count, distinct_id_count


def _review_private_manifest(
    private_manifest: Mapping[str, Any],
    public_manifest: Mapping[str, Any],
    *,
    expected_guild_label: str,
    expected_report_count: int,
    expected_exact_count: int,
) -> dict[str, Any]:
    if private_manifest.get("schema_version") != 1:
        raise ValueError("private manifest schema mismatch")
    if private_manifest.get("manifest_kind") != _PRIVATE_MANIFEST_KIND:
        raise ValueError("private manifest kind mismatch")
    if private_manifest.get("manifest_version") != _MANIFEST_VERSION:
        raise ValueError("private manifest version mismatch")
    if private_manifest.get("target_guild_label") != expected_guild_label:
        raise ValueError("private manifest guild label mismatch")

    for field_name in (
        "source_terminal_receipt_sha256",
        "source_terminal_private_sha256",
        "source_mapping_sha256",
    ):
        if private_manifest.get(field_name) != public_manifest.get(field_name):
            raise ValueError(f"private/public manifest mismatch: {field_name}")

    private_summary = _required_object(
        private_manifest.get("summary"),
        "private_manifest.summary",
    )
    if private_summary.get("contains_source_scalar_values") is not True:
        raise ValueError("private manifest scalar boundary mismatch")
    if private_summary.get("report_count") != expected_report_count:
        raise ValueError("private manifest report count mismatch")

    reports = [
        _required_object(value, "private_manifest.reports[]")
        for value in _required_list(
            private_manifest.get("reports"),
            "private_manifest.reports",
        )
    ]
    if len(reports) != expected_report_count:
        raise ValueError("private manifest reports array count mismatch")

    normalized_target = expected_guild_label.strip().casefold()
    all_report_ids: list[int] = []
    exact_rows: list[dict[str, Any]] = []
    candidate_keys: set[tuple[str, str]] = set()
    identity_values: dict[tuple[str, str], object] = {}

    for report in reports:
        report_id = _required_integer(report.get("id"), "private report ID")
        all_report_ids.append(report_id)
        guild_name = _normalized_name(report.get("guild_name"))
        guild_key = _identity_key(report.get("guild_id"))
        if guild_key is not None:
            identity_values[guild_key] = report.get("guild_id")
        if guild_name is not None and guild_name.casefold() == normalized_target:
            exact_rows.append(report)
            if guild_key is not None:
                candidate_keys.add(guild_key)

    if len(set(all_report_ids)) != len(all_report_ids):
        raise ValueError("private manifest contains duplicate report IDs")
    if len(exact_rows) != expected_exact_count:
        raise ValueError("private manifest exact-label count mismatch")
    if any(report.get("guild_id") is None for report in exact_rows):
        raise ValueError("exact-label report has null guild ID")
    if len(candidate_keys) != 1:
        raise ValueError("exact-label reports do not share one guild ID")

    candidate_key = next(iter(candidate_keys))
    candidate_value = identity_values[candidate_key]
    candidate_rows = [
        report
        for report in reports
        if _identity_key(report.get("guild_id")) == candidate_key
    ]
    candidate_names = [
        _normalized_name(report.get("guild_name"))
        for report in candidate_rows
    ]
    if any(name is None for name in candidate_names):
        raise ValueError("candidate guild ID has an empty guild name")
    if any(name.casefold() != normalized_target for name in candidate_names if name):
        raise ValueError("candidate guild ID has a conflicting guild name")

    exact_report_ids = [
        _required_integer(report.get("id"), "exact-label report ID")
        for report in exact_rows
    ]
    return {
        "candidate_source_guild_id": candidate_value,
        "exact_label_report_ids": exact_report_ids,
        "exact_label_report_count": len(exact_rows),
        "candidate_guild_id_report_count": len(candidate_rows),
        "candidate_guild_id_conflicting_name_count": 0,
    }


def _validate_snapshot_reviews(
    public_review: Mapping[str, Any],
    private_review: Mapping[str, Any],
    *,
    public_manifest_body: bytes,
    private_manifest_body: bytes,
    private_review_body: bytes,
    manifest_review: Mapping[str, Any],
    expected_guild_label: str,
) -> None:
    if public_review.get("schema_version") != 1:
        raise ValueError("public snapshot review schema mismatch")
    if public_review.get("review_kind") != _SNAPSHOT_KIND:
        raise ValueError("public snapshot review kind mismatch")
    if public_review.get("review_version") != _SNAPSHOT_VERSION:
        raise ValueError("public snapshot review version mismatch")

    target = _required_object(public_review.get("target"), "snapshot.target")
    if target.get("guild_label") != expected_guild_label:
        raise ValueError("public snapshot review guild label mismatch")
    if target.get("source_guild_id_published") is not False:
        raise ValueError("public snapshot review publishes guild ID")

    public_summary = _required_object(
        public_review.get("summary"),
        "snapshot.summary",
    )
    if public_summary.get("all_integrity_checks_passed") is not True:
        raise ValueError("public snapshot review integrity checks failed")
    if public_summary.get("contains_source_scalar_values") is not False:
        raise ValueError("public snapshot review contains source scalar values")
    if public_summary.get("exact_label_report_count") != manifest_review[
        "exact_label_report_count"
    ]:
        raise ValueError("snapshot exact-label count mismatch")
    if public_summary.get("candidate_guild_id_report_count") != manifest_review[
        "candidate_guild_id_report_count"
    ]:
        raise ValueError("snapshot candidate report count mismatch")
    if public_summary.get("candidate_guild_id_conflicting_non_empty_name_count") != 0:
        raise ValueError("snapshot review contains conflicting names")

    public_boundary = _required_object(
        public_review.get("decision_boundary"),
        "snapshot.decision_boundary",
    )
    if public_boundary.get("snapshot_internal_identity_consistent") is not True:
        raise ValueError("snapshot identity is not internally consistent")
    if public_boundary.get("ready_for_independent_source_identity_review") is not True:
        raise ValueError("snapshot is not ready for independent-source review")
    if public_boundary.get("guild_identity_verified") is not False:
        raise ValueError("snapshot review already marks guild identity verified")

    if _sha256_bytes(public_manifest_body) != public_review.get(
        "source_public_manifest_receipt_sha256"
    ):
        raise ValueError("snapshot public-manifest SHA-256 mismatch")
    if _sha256_bytes(private_manifest_body) != public_review.get(
        "source_private_manifest_sha256"
    ):
        raise ValueError("snapshot private-manifest SHA-256 mismatch")
    if _sha256_bytes(private_review_body) != public_review.get(
        "source_private_review_sha256"
    ):
        raise ValueError("private snapshot review SHA-256 mismatch")

    if private_review.get("schema_version") != 1:
        raise ValueError("private snapshot review schema mismatch")
    if private_review.get("review_kind") != _SNAPSHOT_PRIVATE_KIND:
        raise ValueError("private snapshot review kind mismatch")
    if private_review.get("review_version") != _SNAPSHOT_VERSION:
        raise ValueError("private snapshot review version mismatch")
    if private_review.get("target_guild_label") != expected_guild_label:
        raise ValueError("private snapshot review guild label mismatch")
    if private_review.get("candidate_source_guild_id") != manifest_review[
        "candidate_source_guild_id"
    ]:
        raise ValueError("private snapshot candidate guild ID mismatch")
    if private_review.get("exact_label_report_ids") != manifest_review[
        "exact_label_report_ids"
    ]:
        raise ValueError("private snapshot exact-label report IDs mismatch")


def _validate_mapping_reviews(
    public_review: Mapping[str, Any],
    private_review: Mapping[str, Any],
    *,
    private_review_body: bytes,
    candidate_source_guild_id: int | str,
    expected_guild_label: str,
) -> dict[str, Any]:
    if public_review.get("schema_version") != 1:
        raise ValueError("public search mapping schema mismatch")
    if public_review.get("mapping_kind") != _MAPPING_KIND:
        raise ValueError("public search mapping kind mismatch")
    if public_review.get("mapping_version") != _MAPPING_VERSION:
        raise ValueError("public search mapping version mismatch")

    target = _required_object(public_review.get("target"), "mapping.target")
    if target.get("guild_label") != expected_guild_label:
        raise ValueError("public search mapping guild label mismatch")
    if target.get("raw_payload_published") is not False:
        raise ValueError("public search mapping publishes raw payload")
    if target.get("source_guild_id_published") is not False:
        raise ValueError("public search mapping publishes guild ID")

    summary = _required_object(public_review.get("summary"), "mapping.summary")
    if summary.get("all_integrity_checks_passed") is not True:
        raise ValueError("public search mapping integrity checks failed")
    if summary.get("cross_endpoint_identity_candidate_observed") is not True:
        raise ValueError("public search mapping lacks cross-endpoint candidate")
    if summary.get("ready_for_guild_identity_decision_review") is not True:
        raise ValueError("public search mapping is not ready for identity decision")
    if summary.get("contains_raw_payload") is not False:
        raise ValueError("public search mapping contains raw payload")
    if summary.get("contains_source_scalar_values") is not False:
        raise ValueError("public search mapping contains source scalar values")

    evidence = _required_object(
        public_review.get("evidence_summary"),
        "mapping.evidence_summary",
    )
    if evidence.get("guild_search_result_count") != 1:
        raise ValueError("identity decision requires one guild search result")
    if evidence.get("guild_id_source_candidate_match_count") != 1:
        raise ValueError("guild search ID does not match source candidate")
    if evidence.get("guild_name_casefold_match_count") != 1:
        raise ValueError("guild search name does not match target label")
    if evidence.get("cross_endpoint_identity_candidate_observed") is not True:
        raise ValueError("cross-endpoint identity candidate is absent")

    boundary = _required_object(
        public_review.get("decision_boundary"),
        "mapping.decision_boundary",
    )
    if boundary.get("independent_source_identity_candidate_observed") is not True:
        raise ValueError("independent-source identity candidate is absent")
    if boundary.get("guild_identity_verified") is not False:
        raise ValueError("mapping review already marks guild identity verified")
    if boundary.get("ready_for_guild_filtering") is not False:
        raise ValueError("mapping review enables guild filtering prematurely")

    if _sha256_bytes(private_review_body) != public_review.get(
        "source_private_review_sha256"
    ):
        raise ValueError("private search mapping review SHA-256 mismatch")

    if private_review.get("schema_version") != 1:
        raise ValueError("private search mapping schema mismatch")
    if private_review.get("mapping_kind") != _MAPPING_PRIVATE_KIND:
        raise ValueError("private search mapping kind mismatch")
    if private_review.get("mapping_version") != _MAPPING_VERSION:
        raise ValueError("private search mapping version mismatch")
    if private_review.get("target_guild_label") != expected_guild_label:
        raise ValueError("private search mapping guild label mismatch")
    if str(private_review.get("candidate_source_guild_id")) != str(
        candidate_source_guild_id
    ):
        raise ValueError("cross-endpoint guild ID mismatch")

    public_capture = _required_object(
        public_review.get("capture_binding"),
        "mapping.capture_binding",
    )
    private_capture = _required_object(
        private_review.get("capture_binding"),
        "private_mapping.capture_binding",
    )
    if public_capture != private_capture:
        raise ValueError("public/private search mapping capture bindings differ")

    reviewed = _required_object(
        private_review.get("reviewed_guild_object"),
        "private_mapping.reviewed_guild_object",
    )
    if str(reviewed.get("guild_id")) != str(candidate_source_guild_id):
        raise ValueError("reviewed guild object ID mismatch")
    guild_name = _required_nonempty_string(
        reviewed.get("guild_name"),
        "reviewed guild name",
    )
    if guild_name.casefold() != expected_guild_label.casefold():
        raise ValueError("reviewed guild name does not match target label")
    _required_nonempty_string(reviewed.get("realm"), "reviewed guild realm")
    _required_nonempty_string(
        reviewed.get("report_count"),
        "reviewed guild report count",
    )

    mapped_fields = [
        _required_object(value, "private_mapping.mapped_fields[]")
        for value in _required_list(
            private_review.get("mapped_fields"),
            "private_mapping.mapped_fields",
        )
    ]
    if len(mapped_fields) != 4:
        raise ValueError("private search mapping must contain four mapped fields")

    return {
        "guild_search_result_count": 1,
        "mapped_field_count": len(mapped_fields),
        "guild_name_casefold_match": True,
        "cross_endpoint_source_id_equal": True,
    }


def decide_guild_identity(
    *,
    public_manifest_path: Path,
    private_manifest_path: Path,
    public_snapshot_review_path: Path,
    private_snapshot_review_path: Path,
    public_mapping_review_path: Path,
    private_mapping_review_path: Path,
    private_output_path: Path,
    receipt_output_path: Path,
    promote_identity: bool,
    expected_guild_label: str = "Argentum",
) -> dict[str, Any]:
    """Explicitly promote a bound cross-endpoint guild identity decision."""
    if promote_identity is not True:
        raise ValueError("explicit guild identity promotion is required")

    public_manifest, public_manifest_body = _load_object(
        public_manifest_path,
        "public report manifest receipt",
    )
    private_manifest, private_manifest_body = _load_object(
        private_manifest_path,
        "private report manifest",
    )
    public_snapshot, public_snapshot_body = _load_object(
        public_snapshot_review_path,
        "public guild identity snapshot review",
    )
    private_snapshot, private_snapshot_body = _load_object(
        private_snapshot_review_path,
        "private guild identity snapshot review",
    )
    public_mapping, public_mapping_body = _load_object(
        public_mapping_review_path,
        "public guild search mapping review",
    )
    private_mapping, private_mapping_body = _load_object(
        private_mapping_review_path,
        "private guild search mapping review",
    )

    report_count, exact_count, distinct_id_count = _validate_public_manifest(
        public_manifest,
        private_manifest_body=private_manifest_body,
        expected_guild_label=expected_guild_label,
    )
    manifest_review = _review_private_manifest(
        private_manifest,
        public_manifest,
        expected_guild_label=expected_guild_label,
        expected_report_count=report_count,
        expected_exact_count=exact_count,
    )
    _validate_snapshot_reviews(
        public_snapshot,
        private_snapshot,
        public_manifest_body=public_manifest_body,
        private_manifest_body=private_manifest_body,
        private_review_body=private_snapshot_body,
        manifest_review=manifest_review,
        expected_guild_label=expected_guild_label,
    )
    mapping_review = _validate_mapping_reviews(
        public_mapping,
        private_mapping,
        private_review_body=private_mapping_body,
        candidate_source_guild_id=manifest_review["candidate_source_guild_id"],
        expected_guild_label=expected_guild_label,
    )

    checks = {
        "explicit_operator_promotion_recorded": True,
        "public_manifest_verified": True,
        "private_manifest_sha256_verified": True,
        "private_manifest_recomputed_without_conflicts": True,
        "public_snapshot_review_verified": True,
        "private_snapshot_review_sha256_verified": True,
        "public_search_mapping_review_verified": True,
        "private_search_mapping_review_sha256_verified": True,
        "cross_endpoint_source_id_equality_verified": mapping_review[
            "cross_endpoint_source_id_equal"
        ],
        "cross_endpoint_name_casefold_equality_verified": mapping_review[
            "guild_name_casefold_match"
        ],
        "single_search_result_verified": mapping_review[
            "guild_search_result_count"
        ]
        == 1,
        "snapshot_target_id_unique_verified": distinct_id_count == 1,
        "snapshot_conflicting_names_absent": manifest_review[
            "candidate_guild_id_conflicting_name_count"
        ]
        == 0,
        "public_decision_contains_no_source_scalar_values": True,
        "raw_payload_not_published": True,
        "source_guild_id_not_published": True,
    }
    identity_verified = all(checks.values())

    private_payload = {
        "schema_version": 1,
        "decision_kind": "guild_identity_decision_private",
        "decision_version": _DECISION_VERSION,
        "target_guild_label": expected_guild_label,
        "explicit_operator_promotion": True,
        "candidate_source_guild_id": manifest_review["candidate_source_guild_id"],
        "source_public_manifest_name": public_manifest_path.name,
        "source_public_manifest_sha256": _sha256_bytes(public_manifest_body),
        "source_private_manifest_name": private_manifest_path.name,
        "source_private_manifest_sha256": _sha256_bytes(private_manifest_body),
        "source_public_snapshot_review_name": public_snapshot_review_path.name,
        "source_public_snapshot_review_sha256": _sha256_bytes(public_snapshot_body),
        "source_private_snapshot_review_name": private_snapshot_review_path.name,
        "source_private_snapshot_review_sha256": _sha256_bytes(private_snapshot_body),
        "source_public_mapping_review_name": public_mapping_review_path.name,
        "source_public_mapping_review_sha256": _sha256_bytes(public_mapping_body),
        "source_private_mapping_review_name": private_mapping_review_path.name,
        "source_private_mapping_review_sha256": _sha256_bytes(private_mapping_body),
        "snapshot_review": manifest_review,
        "mapping_review": mapping_review,
        "integrity_checks": checks,
        "guild_identity_verified": identity_verified,
    }
    private_body = _write_json(private_output_path, private_payload)

    receipt = {
        "schema_version": 1,
        "decision_kind": "guild_identity_decision",
        "decision_version": _DECISION_VERSION,
        "source_public_manifest_name": public_manifest_path.name,
        "source_public_manifest_sha256": _sha256_bytes(public_manifest_body),
        "source_public_snapshot_review_name": public_snapshot_review_path.name,
        "source_public_snapshot_review_sha256": _sha256_bytes(public_snapshot_body),
        "source_public_mapping_review_name": public_mapping_review_path.name,
        "source_public_mapping_review_sha256": _sha256_bytes(public_mapping_body),
        "source_private_decision_name": private_output_path.name,
        "source_private_decision_sha256": _sha256_bytes(private_body),
        "target": {
            "guild_label": expected_guild_label,
            "source_guild_id_published": False,
            "raw_payload_published": False,
        },
        "promotion": {
            "explicit_operator_promotion": True,
            "promotion_mechanism": "required_cli_flag",
            "evidence_policy": "consistent_snapshot_plus_independent_search",
        },
        "evidence_summary": {
            "snapshot_report_count": report_count,
            "snapshot_exact_label_report_count": exact_count,
            "snapshot_distinct_target_guild_id_count": distinct_id_count,
            "snapshot_candidate_conflicting_name_count": manifest_review[
                "candidate_guild_id_conflicting_name_count"
            ],
            "guild_search_result_count": mapping_review[
                "guild_search_result_count"
            ],
            "guild_search_mapped_field_count": mapping_review["mapped_field_count"],
            "cross_endpoint_source_id_equal": mapping_review[
                "cross_endpoint_source_id_equal"
            ],
            "cross_endpoint_name_casefold_equal": mapping_review[
                "guild_name_casefold_match"
            ],
            "contains_raw_payload": False,
            "contains_source_scalar_values": False,
        },
        "integrity_checks": checks,
        "summary": {
            "all_integrity_checks_passed": identity_verified,
            "independent_source_identity_verified": identity_verified,
            "guild_identity_verified": identity_verified,
            "ready_for_guild_filtering": identity_verified,
            "contains_raw_payload": False,
            "contains_source_scalar_values": False,
        },
        "decision_boundary": {
            "status": (
                "guild_identity_verified"
                if identity_verified
                else "guild_identity_decision_failed"
            ),
            "snapshot_internal_identity_consistent": True,
            "guild_search_field_mapping_reviewed": True,
            "independent_source_identity_candidate_observed": True,
            "independent_source_identity_verified": identity_verified,
            "guild_api_route_semantics_verified": False,
            "guild_identity_verified": identity_verified,
            "ready_for_guild_filtering": identity_verified,
            "ready_for_full_guild_crawl": False,
            "ready_for_multi_report_character_graph": False,
            "ready_for_performance_model": False,
            "ready_for_bis25_scoring": False,
            "planner_scoring_allowed": False,
        },
    }
    _write_json(receipt_output_path, receipt)
    return receipt


__all__ = ["decide_guild_identity"]
