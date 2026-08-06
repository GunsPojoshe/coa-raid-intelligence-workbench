from __future__ import annotations

import gzip
import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import quote, urljoin, urlsplit
from urllib.request import urlopen

from .armory_capture import _capture_one_page, build_page_capture_to_dict
from .raw_archive import RawArchive
from .route_discovery import discover_api_route_candidates
from .source_registry import SourceRegistry
from .spa_route_inventory import normalize_api_route_shape

_DISCOVERY_VERSION = "guild-identity-route-discovery-v2"
_SNAPSHOT_REVIEW_VERSION = "guild-identity-snapshot-review-v1"
_PUBLIC_REVIEW_KIND = "guild_identity_snapshot_review"
_PRIVATE_REVIEW_KIND = "guild_identity_snapshot_private_review"
_MAX_ARCHIVED_SCAN_BYTES = 16 * 1024 * 1024


def _generated_at() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _load_object(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    try:
        body = path.read_bytes()
    except OSError as exc:
        raise ValueError(f"unable to read {label}: {path}") from exc
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is not valid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return payload, body


def _write_json(path: Path, payload: Mapping[str, Any]) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = (json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(body)
    temporary.replace(path)
    return body


def _required_object(value: object, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"guild route discovery field {field_name} must be an object")
    return value


def _candidate_scalar(value: object) -> int | str:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError("candidate source guild ID must be an integer or string scalar")
    prepared = str(value).strip()
    if not prepared or len(prepared) > 160:
        raise ValueError("candidate source guild ID is empty or too long")
    return value


def _validate_reviews(
    public_review: Mapping[str, Any],
    private_review: Mapping[str, Any],
    *,
    private_review_body: bytes,
    expected_guild_label: str,
) -> int | str:
    if public_review.get("schema_version") != 1:
        raise ValueError("public snapshot review schema mismatch")
    if public_review.get("review_kind") != _PUBLIC_REVIEW_KIND:
        raise ValueError("public snapshot review kind mismatch")
    if public_review.get("review_version") != _SNAPSHOT_REVIEW_VERSION:
        raise ValueError("public snapshot review version mismatch")
    public_target = _required_object(public_review.get("target"), "public_review.target")
    if public_target.get("guild_label") != expected_guild_label:
        raise ValueError("public snapshot review guild label mismatch")
    if public_target.get("source_guild_id_published") is not False:
        raise ValueError("public snapshot review unexpectedly publishes the source guild ID")
    public_summary = _required_object(public_review.get("summary"), "public_review.summary")
    if public_summary.get("all_integrity_checks_passed") is not True:
        raise ValueError("public snapshot review integrity checks did not pass")
    if public_summary.get("contains_source_scalar_values") is not False:
        raise ValueError("public snapshot review is not scalar-free")
    public_boundary = _required_object(
        public_review.get("decision_boundary"), "public_review.decision_boundary"
    )
    if public_boundary.get("snapshot_internal_identity_consistent") is not True:
        raise ValueError("snapshot identity is not internally consistent")
    if public_boundary.get("ready_for_independent_source_identity_review") is not True:
        raise ValueError("snapshot review is not ready for independent route discovery")
    for field_name in (
        "independent_source_identity_verified",
        "guild_identity_verified",
        "ready_for_guild_filtering",
        "ready_for_full_guild_crawl",
        "planner_scoring_allowed",
    ):
        if public_boundary.get(field_name) is not False:
            raise ValueError(f"public snapshot review boundary mismatch: {field_name}")

    expected_private_hash = public_review.get("source_private_review_sha256")
    if not isinstance(expected_private_hash, str) or len(expected_private_hash) != 64:
        raise ValueError("public snapshot review private hash is missing")
    if _sha256_bytes(private_review_body) != expected_private_hash:
        raise ValueError("private snapshot review SHA-256 does not match public review")

    if private_review.get("schema_version") != 1:
        raise ValueError("private snapshot review schema mismatch")
    if private_review.get("review_kind") != _PRIVATE_REVIEW_KIND:
        raise ValueError("private snapshot review kind mismatch")
    if private_review.get("review_version") != _SNAPSHOT_REVIEW_VERSION:
        raise ValueError("private snapshot review version mismatch")
    if private_review.get("target_guild_label") != expected_guild_label:
        raise ValueError("private snapshot review guild label mismatch")
    private_summary = _required_object(private_review.get("summary"), "private_review.summary")
    if private_summary.get("contains_source_scalar_values") is not True:
        raise ValueError("private snapshot review scalar boundary mismatch")
    private_boundary = _required_object(
        private_review.get("decision_boundary"), "private_review.decision_boundary"
    )
    if private_boundary.get("snapshot_internal_identity_consistent") is not True:
        raise ValueError("private snapshot review is not internally consistent")
    if private_boundary.get("guild_identity_verified") is not False:
        raise ValueError("private snapshot review unexpectedly verifies guild identity")

    for field_name in (
        "source_private_manifest_sha256",
        "source_public_manifest_receipt_sha256",
    ):
        if private_review.get(field_name) != public_review.get(field_name):
            raise ValueError(f"private/public snapshot review mismatch: {field_name}")
    return _candidate_scalar(private_review.get("candidate_source_guild_id"))


def _redacted_route_shape(candidate: str, source_guild_id: int | str) -> str:
    prepared = candidate.replace("\\/", "/")
    tokens = {str(source_guild_id), quote(str(source_guild_id), safe="")}
    for token in sorted(tokens, key=len, reverse=True):
        if token:
            prepared = prepared.replace(token, "{guild_id}")
    return normalize_api_route_shape(prepared)


def _archived_capture_route_candidates(capture: object) -> tuple[str, ...]:
    payload_path = getattr(capture, "payload_path", None)
    payload_hash = getattr(capture, "payload_hash", None)
    expected_size = getattr(capture, "bytes_uncompressed", None)
    if not isinstance(payload_path, str) or not isinstance(payload_hash, str):
        return ()
    try:
        with gzip.open(Path(payload_path), "rb") as stream:
            body = stream.read(_MAX_ARCHIVED_SCAN_BYTES + 1)
    except (OSError, EOFError):
        return ()
    if len(body) > _MAX_ARCHIVED_SCAN_BYTES:
        return ()
    if isinstance(expected_size, int) and len(body) != expected_size:
        return ()
    if _sha256_bytes(body) != payload_hash:
        return ()
    return discover_api_route_candidates(body)


def _asset_failure_classes(asset: object) -> tuple[str, ...]:
    classes: set[str] = set()
    status = getattr(asset, "status", None)
    error = str(getattr(asset, "error", "") or "").casefold()
    if isinstance(status, int) and not 200 <= status < 300:
        classes.add("http_status_failure")
    if "timeout" in error or "timed out" in error:
        classes.add("timeout")
    if "incomplete" in error:
        classes.add("incomplete_response")
    if "exceeded" in error or "too large" in error:
        classes.add("response_too_large")
    if "remote disconnected" in error:
        classes.add("remote_disconnect")
    if "network" in error or "i/o" in error:
        classes.add("network_error")
    if "archive" in error:
        classes.add("archive_fallback_unavailable")
    if not classes:
        classes.add("unclassified_failure")
    return tuple(sorted(classes))


def discover_guild_identity_route_candidates(
    registry: SourceRegistry,
    archive: RawArchive,
    *,
    public_snapshot_review_path: Path,
    private_snapshot_review_path: Path,
    private_output_path: Path,
    receipt_output_path: Path,
    expected_guild_label: str = "Argentum",
    timeout_seconds: float = 30.0,
    opener: Any = urlopen,
) -> dict[str, Any]:
    """Capture one guild UI page and inventory scalar-free guild API route candidates."""
    if timeout_seconds <= 0 or timeout_seconds > 120:
        raise ValueError("timeout_seconds must be greater than zero and at most 120")

    public_review, public_review_body = _load_object(
        public_snapshot_review_path, "public guild identity snapshot review"
    )
    private_review, private_review_body = _load_object(
        private_snapshot_review_path, "private guild identity snapshot review"
    )
    source_guild_id = _validate_reviews(
        public_review,
        private_review,
        private_review_body=private_review_body,
        expected_guild_label=expected_guild_label,
    )

    source_segment = quote(str(source_guild_id), safe="")
    page_url = urljoin(
        f"{registry.base_url.rstrip('/')}/",
        f"guilds/{source_segment}/reports",
    )
    result = _capture_one_page(
        registry=registry,
        archive=archive,
        page_kind="guild_identity",
        url=page_url,
        timeout_seconds=timeout_seconds,
        opener=opener,
        asset_cache={},
    )

    source_host = urlsplit(registry.base_url).hostname
    page_completed = (
        result.capture is not None
        and result.status is not None
        and 200 <= result.status < 300
    )
    successful_assets = [
        asset
        for asset in result.assets
        if asset.capture is not None
        and asset.status is not None
        and 200 <= asset.status < 300
    ]
    captured_assets = [asset for asset in result.assets if asset.capture is not None]
    failed_assets = [asset for asset in result.assets if asset.capture is None]

    page_candidates = set(_archived_capture_route_candidates(result.capture))
    embedded_candidates = {
        candidate
        for embedded in result.embedded_json
        for candidate in _archived_capture_route_candidates(embedded.capture)
    }
    asset_candidates = {
        candidate for asset in result.assets for candidate in asset.api_route_candidates
    }
    all_candidates = sorted(page_candidates | embedded_candidates | asset_candidates)
    route_shapes = sorted(
        {_redacted_route_shape(candidate, source_guild_id) for candidate in all_candidates}
    )
    guild_route_shapes = [shape for shape in route_shapes if "guild" in shape.casefold()]
    source_tokens = {str(source_guild_id), quote(str(source_guild_id), safe="")}
    scalar_redaction_verified = all(
        not any(token and token in shape for token in source_tokens) for shape in route_shapes
    )
    all_asset_urls_same_origin = all(
        urlsplit(asset.url).hostname == source_host for asset in result.assets
    )
    failure_class_counts = Counter(
        failure_class
        for asset in failed_assets
        for failure_class in _asset_failure_classes(asset)
    )
    route_candidate_sources = {
        "page_html": len(page_candidates),
        "embedded_json": len(embedded_candidates),
        "assets": len(asset_candidates),
    }

    checks = {
        "public_snapshot_review_verified": True,
        "private_snapshot_review_sha256_verified": True,
        "snapshot_boundary_preserved": True,
        "guild_page_url_same_origin": urlsplit(page_url).hostname == source_host,
        "guild_page_archived": page_completed,
        "all_asset_urls_same_origin": all_asset_urls_same_origin,
        "public_route_shapes_redact_candidate_id": scalar_redaction_verified,
        "public_receipt_scalar_boundary_preserved": True,
    }
    all_integrity_checks_passed = all(checks.values())
    ready_for_route_review = all_integrity_checks_passed and bool(guild_route_shapes)

    private_payload = {
        "schema_version": 1,
        "discovery_kind": "guild_identity_route_discovery_private",
        "discovery_version": _DISCOVERY_VERSION,
        "generated_at": _generated_at(),
        "source_public_snapshot_review_name": public_snapshot_review_path.name,
        "source_public_snapshot_review_sha256": _sha256_bytes(public_review_body),
        "source_private_snapshot_review_name": private_snapshot_review_path.name,
        "source_private_snapshot_review_sha256": _sha256_bytes(private_review_body),
        "target_guild_label": expected_guild_label,
        "candidate_source_guild_id": source_guild_id,
        "guild_page_url": page_url,
        "page_capture": build_page_capture_to_dict(result),
        "route_candidate_sources": {
            "page_html": sorted(page_candidates),
            "embedded_json": sorted(embedded_candidates),
            "assets": sorted(asset_candidates),
        },
        "api_route_candidates": all_candidates,
        "guild_api_route_candidates": [
            candidate for candidate in all_candidates if "guild" in candidate.casefold()
        ],
        "summary": {
            "page_capture_completed": page_completed,
            "asset_count": len(result.assets),
            "captured_asset_count": len(captured_assets),
            "successful_live_asset_count": len(successful_assets),
            "failed_asset_count": len(failed_assets),
            "api_route_candidate_count": len(all_candidates),
            "guild_api_route_candidate_count": len(guild_route_shapes),
            "route_candidate_sources": route_candidate_sources,
            "asset_failure_class_counts": dict(sorted(failure_class_counts.items())),
            "contains_source_scalar_values": True,
        },
    }
    private_body = _write_json(private_output_path, private_payload)

    receipt = {
        "schema_version": 1,
        "discovery_kind": "guild_identity_route_discovery",
        "discovery_version": _DISCOVERY_VERSION,
        "generated_at": _generated_at(),
        "source_public_snapshot_review_name": public_snapshot_review_path.name,
        "source_public_snapshot_review_sha256": _sha256_bytes(public_review_body),
        "source_private_snapshot_review_name": private_snapshot_review_path.name,
        "source_private_snapshot_review_sha256": _sha256_bytes(private_review_body),
        "source_private_discovery_name": private_output_path.name,
        "source_private_discovery_sha256": _sha256_bytes(private_body),
        "target": {
            "guild_label": expected_guild_label,
            "source_guild_id_published": False,
        },
        "request": {
            "page_route_shape": "/guilds/{guild_id}/reports",
            "same_origin_only": True,
            "timeout_seconds": timeout_seconds,
        },
        "route_inventory": {
            "guild_api_route_shapes": guild_route_shapes,
            "all_api_route_shape_count": len(route_shapes),
            "guild_api_route_shape_count": len(guild_route_shapes),
            "candidate_source_counts": route_candidate_sources,
        },
        "asset_failure_summary": {
            "failed_asset_count": len(failed_assets),
            "failure_class_counts": dict(sorted(failure_class_counts.items())),
            "contains_error_text": False,
            "contains_asset_urls": False,
        },
        "summary": {
            "page_capture_completed": page_completed,
            "page_payload_archived": result.capture is not None,
            "asset_count": len(result.assets),
            "captured_asset_count": len(captured_assets),
            "successful_live_asset_count": len(successful_assets),
            "failed_asset_count": len(failed_assets),
            "api_route_candidate_count": len(all_candidates),
            "guild_api_route_candidate_count": len(guild_route_shapes),
            "integrity_check_count": len(checks),
            "all_integrity_checks_passed": all_integrity_checks_passed,
            "contains_source_scalar_values": False,
        },
        "integrity_checks": checks,
        "decision_boundary": {
            "status": (
                "guild_api_route_candidates_observed"
                if ready_for_route_review
                else "guild_api_route_discovery_incomplete"
            ),
            "snapshot_internal_identity_consistent": True,
            "guild_api_route_candidates_observed": bool(guild_route_shapes),
            "guild_api_route_semantics_verified": False,
            "independent_source_identity_verified": False,
            "guild_identity_verified": False,
            "ready_for_guild_api_route_review": ready_for_route_review,
            "ready_for_guild_filtering": False,
            "ready_for_full_guild_crawl": False,
            "ready_for_multi_report_character_graph": False,
            "ready_for_performance_model": False,
            "ready_for_bis25_scoring": False,
            "planner_scoring_allowed": False,
        },
    }
    _write_json(receipt_output_path, receipt)
    return receipt


__all__ = ["discover_guild_identity_route_candidates"]
