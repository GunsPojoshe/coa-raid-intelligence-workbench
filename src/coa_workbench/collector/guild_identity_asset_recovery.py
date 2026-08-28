from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence
from urllib.parse import quote, urlsplit

from .raw_archive import RawArchive, request_key_from_url
from .route_discovery import discover_api_route_candidates
from .source_registry import SourceRegistry
from .spa_route_inventory import normalize_api_route_shape

_RECOVERY_VERSION = "guild-identity-asset-recovery-v1"
_ROUTE_DISCOVERY_VERSION = "guild-identity-route-discovery-v2"
_PUBLIC_DISCOVERY_KIND = "guild_identity_route_discovery"
_PRIVATE_DISCOVERY_KIND = "guild_identity_route_discovery_private"
_DEFAULT_MAX_BYTES = 64 * 1024 * 1024

RunCommand = Callable[..., Any]


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
        raise ValueError(f"guild asset recovery field {field_name} must be an object")
    return value


def _required_list(value: object, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"guild asset recovery field {field_name} must be a list")
    return value


def _candidate_scalar(value: object) -> int | str:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError("candidate source guild ID must be an integer or string scalar")
    prepared = str(value).strip()
    if not prepared or len(prepared) > 160:
        raise ValueError("candidate source guild ID is empty or too long")
    return value


def _validate_discovery(
    public_discovery: Mapping[str, Any],
    private_discovery: Mapping[str, Any],
    *,
    private_discovery_body: bytes,
    expected_guild_label: str,
) -> tuple[int | str, dict[str, Any]]:
    if public_discovery.get("schema_version") != 1:
        raise ValueError("public route discovery schema mismatch")
    if public_discovery.get("discovery_kind") != _PUBLIC_DISCOVERY_KIND:
        raise ValueError("public route discovery kind mismatch")
    if public_discovery.get("discovery_version") != _ROUTE_DISCOVERY_VERSION:
        raise ValueError("public route discovery version mismatch")

    target = _required_object(public_discovery.get("target"), "public_discovery.target")
    if target.get("guild_label") != expected_guild_label:
        raise ValueError("public route discovery guild label mismatch")
    if target.get("source_guild_id_published") is not False:
        raise ValueError("public route discovery unexpectedly publishes source guild ID")

    summary = _required_object(public_discovery.get("summary"), "public_discovery.summary")
    if summary.get("all_integrity_checks_passed") is not True:
        raise ValueError("public route discovery integrity checks did not pass")
    if summary.get("contains_source_scalar_values") is not False:
        raise ValueError("public route discovery is not scalar-free")
    if summary.get("failed_asset_count") != 1:
        raise ValueError("asset recovery requires exactly one failed asset")

    failure_summary = _required_object(
        public_discovery.get("asset_failure_summary"),
        "public_discovery.asset_failure_summary",
    )
    failure_counts = _required_object(
        failure_summary.get("failure_class_counts"),
        "public_discovery.asset_failure_summary.failure_class_counts",
    )
    if failure_counts.get("timeout") != 1:
        raise ValueError("asset recovery requires one timeout-class asset failure")
    if failure_summary.get("contains_asset_urls") is not False:
        raise ValueError("public route discovery unexpectedly publishes asset URLs")
    if failure_summary.get("contains_error_text") is not False:
        raise ValueError("public route discovery unexpectedly publishes error text")

    boundary = _required_object(
        public_discovery.get("decision_boundary"),
        "public_discovery.decision_boundary",
    )
    if boundary.get("snapshot_internal_identity_consistent") is not True:
        raise ValueError("snapshot identity is not internally consistent")
    for field_name in (
        "guild_api_route_candidates_observed",
        "guild_api_route_semantics_verified",
        "independent_source_identity_verified",
        "guild_identity_verified",
        "ready_for_guild_api_route_review",
        "ready_for_guild_filtering",
        "ready_for_full_guild_crawl",
        "planner_scoring_allowed",
    ):
        if boundary.get(field_name) is not False:
            raise ValueError(f"public route discovery boundary mismatch: {field_name}")

    expected_private_hash = public_discovery.get("source_private_discovery_sha256")
    if not isinstance(expected_private_hash, str) or len(expected_private_hash) != 64:
        raise ValueError("public route discovery private hash is missing")
    if _sha256_bytes(private_discovery_body) != expected_private_hash:
        raise ValueError("private route discovery SHA-256 does not match public receipt")

    if private_discovery.get("schema_version") != 1:
        raise ValueError("private route discovery schema mismatch")
    if private_discovery.get("discovery_kind") != _PRIVATE_DISCOVERY_KIND:
        raise ValueError("private route discovery kind mismatch")
    if private_discovery.get("discovery_version") != _ROUTE_DISCOVERY_VERSION:
        raise ValueError("private route discovery version mismatch")
    if private_discovery.get("target_guild_label") != expected_guild_label:
        raise ValueError("private route discovery guild label mismatch")

    private_summary = _required_object(
        private_discovery.get("summary"), "private_discovery.summary"
    )
    if private_summary.get("contains_source_scalar_values") is not True:
        raise ValueError("private route discovery scalar boundary mismatch")
    if private_summary.get("failed_asset_count") != 1:
        raise ValueError("private route discovery must contain one failed asset")

    source_guild_id = _candidate_scalar(private_discovery.get("candidate_source_guild_id"))
    page_capture = _required_object(
        private_discovery.get("page_capture"), "private_discovery.page_capture"
    )
    assets = _required_list(page_capture.get("assets"), "private_discovery.page_capture.assets")
    failed_assets: list[dict[str, Any]] = []
    for asset in assets:
        if not isinstance(asset, dict):
            raise ValueError("private route discovery asset entry must be an object")
        error = str(asset.get("error") or "").casefold()
        if asset.get("capture") is None and ("timeout" in error or "timed out" in error):
            failed_assets.append(asset)
    if len(failed_assets) != 1:
        raise ValueError("private route discovery must contain one timeout-class asset")
    return source_guild_id, failed_assets[0]


def _redacted_route_shape(candidate: str, source_guild_id: int | str) -> str:
    prepared = candidate.replace("\\/", "/")
    tokens = {str(source_guild_id), quote(str(source_guild_id), safe="")}
    for token in sorted(tokens, key=len, reverse=True):
        if token:
            prepared = prepared.replace(token, "{guild_id}")
    return normalize_api_route_shape(prepared)


def _curl_failure_class(return_code: int | None, *, process_timed_out: bool) -> str | None:
    if process_timed_out or return_code == 28:
        return "timeout"
    if return_code in {22}:
        return "http_status_failure"
    if return_code in {18, 56}:
        return "incomplete_response"
    if return_code in {23, 26, 63}:
        return "response_too_large_or_write_failure"
    if return_code in {5, 6, 7, 35, 52, 55, 60, 92}:
        return "network_or_tls_failure"
    if return_code not in {None, 0}:
        return "curl_failure"
    return None


def _resolve_curl(executable: str | None) -> str:
    if executable:
        return executable
    for candidate in ("curl.exe", "curl"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    raise ValueError("curl executable was not found")


def recover_guild_identity_asset(
    registry: SourceRegistry,
    archive: RawArchive,
    *,
    public_route_discovery_path: Path,
    private_route_discovery_path: Path,
    private_output_path: Path,
    receipt_output_path: Path,
    expected_guild_label: str = "Argentum",
    curl_executable: str | None = None,
    timeout_seconds: float = 300.0,
    max_bytes: int = _DEFAULT_MAX_BYTES,
    runner: RunCommand = subprocess.run,
) -> dict[str, Any]:
    """Recover one timed-out same-origin SPA asset through bounded curl transport."""
    if timeout_seconds < 30 or timeout_seconds > 900:
        raise ValueError("timeout_seconds must be between 30 and 900")
    if max_bytes < 1024 * 1024 or max_bytes > 128 * 1024 * 1024:
        raise ValueError("max_bytes must be between 1 MiB and 128 MiB")

    public_discovery, public_discovery_body = _load_object(
        public_route_discovery_path, "public guild route discovery"
    )
    private_discovery, private_discovery_body = _load_object(
        private_route_discovery_path, "private guild route discovery"
    )
    source_guild_id, failed_asset = _validate_discovery(
        public_discovery,
        private_discovery,
        private_discovery_body=private_discovery_body,
        expected_guild_label=expected_guild_label,
    )

    asset_url = failed_asset.get("url")
    if not isinstance(asset_url, str) or not asset_url:
        raise ValueError("private route discovery asset URL is missing")
    asset_parts = urlsplit(asset_url)
    source_parts = urlsplit(registry.base_url)
    if asset_parts.scheme != "https" or asset_parts.hostname != source_parts.hostname:
        raise ValueError("asset recovery URL escaped the configured HTTPS source host")

    executable = _resolve_curl(curl_executable)
    private_output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_asset = private_output_path.with_name(
        f".{private_output_path.stem}.{os.getpid()}.asset.part"
    )
    try:
        temporary_asset.unlink(missing_ok=True)
        command: Sequence[str] = (
            executable,
            "--silent",
            "--show-error",
            "--fail",
            "--compressed",
            "--proto",
            "=https",
            "--max-redirs",
            "0",
            "--connect-timeout",
            "30",
            "--max-time",
            f"{timeout_seconds:g}",
            "--retry",
            "2",
            "--retry-delay",
            "2",
            "--retry-all-errors",
            "--max-filesize",
            str(max_bytes),
            "--user-agent",
            "CoA-Raid-Intelligence-Workbench/0.1 guild-asset-recovery",
            "--output",
            str(temporary_asset),
            "--write-out",
            "%{http_code}",
            asset_url,
        )
        process_timed_out = False
        try:
            completed = runner(
                list(command),
                capture_output=True,
                text=True,
                timeout=timeout_seconds + 45,
                check=False,
            )
            return_code = int(completed.returncode)
            stdout = str(completed.stdout or "").strip()
            stderr = str(completed.stderr or "").strip()
        except subprocess.TimeoutExpired as exc:
            process_timed_out = True
            return_code = None
            stdout = ""
            stderr = str(exc)

        http_status = int(stdout[-3:]) if len(stdout) >= 3 and stdout[-3:].isdigit() else None
        body: bytes | None = None
        failure_class = _curl_failure_class(return_code, process_timed_out=process_timed_out)
        if return_code == 0 and temporary_asset.is_file():
            body = temporary_asset.read_bytes()
            if not body:
                failure_class = "empty_response"
                body = None
            elif len(body) > max_bytes:
                failure_class = "response_too_large_or_write_failure"
                body = None
        elif failure_class is None:
            failure_class = "missing_download"

        raw_candidates: tuple[str, ...] = ()
        capture = None
        if body is not None:
            raw_candidates = discover_api_route_candidates(body)
            capture = archive.capture_bytes(
                body,
                source_code=registry.source_code,
                endpoint_code="guild_identity_asset_recovery",
                request_key=request_key_from_url("GET", asset_url),
                fetched_at=datetime.now(timezone.utc),
                http_status=http_status,
                content_type=str(failed_asset.get("content_type") or "application/javascript"),
                request_url=asset_url,
                metadata={
                    "capture_mode": "bounded_curl_asset_recovery",
                    "transport": "curl",
                    "redirects_allowed": False,
                    "credentials_supplied": False,
                    "source_private_discovery_sha256": _sha256_bytes(private_discovery_body),
                    "max_bytes": max_bytes,
                    "timeout_seconds": timeout_seconds,
                },
            )

        route_shapes = sorted(
            {_redacted_route_shape(candidate, source_guild_id) for candidate in raw_candidates}
        )
        guild_route_shapes = [
            shape for shape in route_shapes if "guild" in shape.casefold()
        ]
        source_tokens = {str(source_guild_id), quote(str(source_guild_id), safe="")}
        scalar_redaction_verified = all(
            not any(token and token in shape for token in source_tokens)
            for shape in route_shapes
        )

        checks = {
            "public_route_discovery_verified": True,
            "private_route_discovery_sha256_verified": True,
            "single_timeout_asset_selected": True,
            "asset_url_same_origin": asset_parts.hostname == source_parts.hostname,
            "asset_url_https": asset_parts.scheme == "https",
            "redirects_disabled": True,
            "credentials_not_supplied": True,
            "download_size_bounded": body is None or len(body) <= max_bytes,
            "public_route_shapes_redact_candidate_id": scalar_redaction_verified,
            "public_receipt_scalar_boundary_preserved": True,
        }
        all_integrity_checks_passed = all(checks.values())
        asset_download_completed = body is not None and capture is not None
        ready_for_route_review = (
            all_integrity_checks_passed
            and asset_download_completed
            and bool(guild_route_shapes)
        )

        private_payload = {
            "schema_version": 1,
            "recovery_kind": "guild_identity_asset_recovery_private",
            "recovery_version": _RECOVERY_VERSION,
            "generated_at": _generated_at(),
            "source_public_route_discovery_name": public_route_discovery_path.name,
            "source_public_route_discovery_sha256": _sha256_bytes(public_discovery_body),
            "source_private_route_discovery_name": private_route_discovery_path.name,
            "source_private_route_discovery_sha256": _sha256_bytes(private_discovery_body),
            "target_guild_label": expected_guild_label,
            "candidate_source_guild_id": source_guild_id,
            "asset_url": asset_url,
            "curl_executable": executable,
            "curl_return_code": return_code,
            "curl_stdout": stdout,
            "curl_stderr": stderr,
            "http_status": http_status,
            "failure_class": failure_class,
            "asset_capture_payload_hash": getattr(capture, "payload_hash", None),
            "asset_bytes": len(body) if body is not None else 0,
            "api_route_candidates": list(raw_candidates),
            "guild_api_route_candidates": [
                candidate for candidate in raw_candidates if "guild" in candidate.casefold()
            ],
            "summary": {
                "asset_download_completed": asset_download_completed,
                "api_route_candidate_count": len(raw_candidates),
                "guild_api_route_candidate_count": len(guild_route_shapes),
                "contains_source_scalar_values": True,
            },
        }
        private_body = _write_json(private_output_path, private_payload)

        receipt = {
            "schema_version": 1,
            "recovery_kind": "guild_identity_asset_recovery",
            "recovery_version": _RECOVERY_VERSION,
            "generated_at": _generated_at(),
            "source_public_route_discovery_name": public_route_discovery_path.name,
            "source_public_route_discovery_sha256": _sha256_bytes(public_discovery_body),
            "source_private_route_discovery_name": private_route_discovery_path.name,
            "source_private_route_discovery_sha256": _sha256_bytes(private_discovery_body),
            "source_private_recovery_name": private_output_path.name,
            "source_private_recovery_sha256": _sha256_bytes(private_body),
            "target": {
                "guild_label": expected_guild_label,
                "source_guild_id_published": False,
                "asset_url_published": False,
            },
            "transport": {
                "kind": "curl",
                "redirects_allowed": False,
                "credentials_supplied": False,
                "timeout_seconds": timeout_seconds,
                "max_bytes": max_bytes,
                "return_code": return_code,
                "http_status": http_status,
                "failure_class": failure_class,
                "contains_error_text": False,
            },
            "route_inventory": {
                "guild_api_route_shapes": guild_route_shapes,
                "all_api_route_shape_count": len(route_shapes),
                "guild_api_route_shape_count": len(guild_route_shapes),
            },
            "summary": {
                "asset_download_completed": asset_download_completed,
                "asset_bytes": len(body) if body is not None else 0,
                "api_route_candidate_count": len(raw_candidates),
                "guild_api_route_candidate_count": len(guild_route_shapes),
                "integrity_check_count": len(checks),
                "all_integrity_checks_passed": all_integrity_checks_passed,
                "contains_source_scalar_values": False,
            },
            "integrity_checks": checks,
            "decision_boundary": {
                "status": (
                    "guild_api_route_candidates_recovered"
                    if ready_for_route_review
                    else "guild_asset_recovery_incomplete"
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
    finally:
        temporary_asset.unlink(missing_ok=True)


__all__ = ["recover_guild_identity_asset"]
