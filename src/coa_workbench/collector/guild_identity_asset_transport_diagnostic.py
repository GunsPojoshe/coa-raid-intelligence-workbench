from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence
from urllib.parse import urlsplit

from .source_registry import SourceRegistry

_DIAGNOSTIC_VERSION = "guild-identity-asset-transport-diagnostic-v1"
_RECOVERY_VERSION = "guild-identity-asset-recovery-v1"
_PUBLIC_RECOVERY_KIND = "guild_identity_asset_recovery"
_PRIVATE_RECOVERY_KIND = "guild_identity_asset_recovery_private"
_DEFAULT_MAX_PROBE_BYTES = 1024 * 1024

RunCommand = Callable[..., Any]

_TRANSPORT_PROFILES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("http1_1", ("--http1.1",)),
    ("ipv4_http1_1", ("--ipv4", "--http1.1")),
    (
        "tls12_http1_1",
        ("--tlsv1.2", "--tls-max", "1.2", "--http1.1"),
    ),
    (
        "ipv4_tls12_http1_1",
        ("--ipv4", "--tlsv1.2", "--tls-max", "1.2", "--http1.1"),
    ),
    (
        "revocation_best_effort_http1_1",
        ("--ssl-revoke-best-effort", "--http1.1"),
    ),
)


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
        raise ValueError(f"guild transport diagnostic field {field_name} must be an object")
    return value


def _candidate_scalar(value: object) -> int | str:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError("candidate source guild ID must be an integer or string scalar")
    prepared = str(value).strip()
    if not prepared or len(prepared) > 160:
        raise ValueError("candidate source guild ID is empty or too long")
    return value


def _validate_recovery(
    public_recovery: Mapping[str, Any],
    private_recovery: Mapping[str, Any],
    *,
    private_recovery_body: bytes,
    expected_guild_label: str,
) -> tuple[int | str, str]:
    if public_recovery.get("schema_version") != 1:
        raise ValueError("public asset recovery schema mismatch")
    if public_recovery.get("recovery_kind") != _PUBLIC_RECOVERY_KIND:
        raise ValueError("public asset recovery kind mismatch")
    if public_recovery.get("recovery_version") != _RECOVERY_VERSION:
        raise ValueError("public asset recovery version mismatch")

    target = _required_object(public_recovery.get("target"), "public_recovery.target")
    if target.get("guild_label") != expected_guild_label:
        raise ValueError("public asset recovery guild label mismatch")
    if target.get("source_guild_id_published") is not False:
        raise ValueError("public asset recovery unexpectedly publishes source guild ID")
    if target.get("asset_url_published") is not False:
        raise ValueError("public asset recovery unexpectedly publishes asset URL")

    summary = _required_object(public_recovery.get("summary"), "public_recovery.summary")
    if summary.get("all_integrity_checks_passed") is not True:
        raise ValueError("public asset recovery integrity checks did not pass")
    if summary.get("contains_source_scalar_values") is not False:
        raise ValueError("public asset recovery is not scalar-free")
    if summary.get("asset_download_completed") is not False:
        raise ValueError("transport diagnostic requires an incomplete asset recovery")
    if summary.get("asset_bytes") != 0:
        raise ValueError("transport diagnostic requires zero recovered asset bytes")

    transport = _required_object(
        public_recovery.get("transport"), "public_recovery.transport"
    )
    if transport.get("kind") != "curl":
        raise ValueError("public asset recovery transport mismatch")
    if transport.get("return_code") != 35:
        raise ValueError("transport diagnostic requires curl return code 35")
    if transport.get("http_status") not in {None, 0}:
        raise ValueError("transport diagnostic requires no observed HTTP status")
    if transport.get("failure_class") != "network_or_tls_failure":
        raise ValueError("public asset recovery failure class mismatch")
    if transport.get("redirects_allowed") is not False:
        raise ValueError("public asset recovery unexpectedly allowed redirects")
    if transport.get("credentials_supplied") is not False:
        raise ValueError("public asset recovery unexpectedly supplied credentials")
    if transport.get("contains_error_text") is not False:
        raise ValueError("public asset recovery unexpectedly publishes error text")

    boundary = _required_object(
        public_recovery.get("decision_boundary"), "public_recovery.decision_boundary"
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
            raise ValueError(f"public asset recovery boundary mismatch: {field_name}")

    expected_private_hash = public_recovery.get("source_private_recovery_sha256")
    if not isinstance(expected_private_hash, str) or len(expected_private_hash) != 64:
        raise ValueError("public asset recovery private hash is missing")
    if _sha256_bytes(private_recovery_body) != expected_private_hash:
        raise ValueError("private asset recovery SHA-256 does not match public receipt")

    if private_recovery.get("schema_version") != 1:
        raise ValueError("private asset recovery schema mismatch")
    if private_recovery.get("recovery_kind") != _PRIVATE_RECOVERY_KIND:
        raise ValueError("private asset recovery kind mismatch")
    if private_recovery.get("recovery_version") != _RECOVERY_VERSION:
        raise ValueError("private asset recovery version mismatch")
    if private_recovery.get("target_guild_label") != expected_guild_label:
        raise ValueError("private asset recovery guild label mismatch")

    private_summary = _required_object(
        private_recovery.get("summary"), "private_recovery.summary"
    )
    if private_summary.get("contains_source_scalar_values") is not True:
        raise ValueError("private asset recovery scalar boundary mismatch")
    if private_summary.get("asset_download_completed") is not False:
        raise ValueError("private asset recovery unexpectedly completed")
    if private_recovery.get("curl_return_code") != 35:
        raise ValueError("private asset recovery curl return code mismatch")
    if private_recovery.get("http_status") not in {None, 0}:
        raise ValueError("private asset recovery HTTP status mismatch")

    source_guild_id = _candidate_scalar(private_recovery.get("candidate_source_guild_id"))
    asset_url = private_recovery.get("asset_url")
    if not isinstance(asset_url, str) or not asset_url:
        raise ValueError("private asset recovery asset URL is missing")
    return source_guild_id, asset_url


def _resolve_curl(executable: str | None) -> str:
    if executable:
        return executable
    for candidate in ("curl.exe", "curl"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    raise ValueError("curl executable was not found")


def _http_status(stdout: object) -> int | None:
    prepared = str(stdout or "").strip()
    if len(prepared) >= 3 and prepared[-3:].isdigit():
        return int(prepared[-3:])
    return None


def _failure_class(
    return_code: int | None,
    *,
    http_status: int | None,
    process_timed_out: bool,
) -> str | None:
    if http_status is not None and 100 <= http_status <= 599:
        return None
    if process_timed_out or return_code == 28:
        return "timeout"
    if return_code == 2:
        return "unsupported_option"
    if return_code == 6:
        return "name_resolution_failure"
    if return_code == 7:
        return "connect_failure"
    if return_code == 35:
        return "tls_handshake_failure"
    if return_code == 60:
        return "certificate_validation_failure"
    if return_code in {18, 52, 56}:
        return "incomplete_response"
    if return_code in {23, 26, 63}:
        return "response_too_large_or_write_failure"
    if return_code not in {None, 0}:
        return "curl_failure"
    return "missing_http_status"


def diagnose_guild_identity_asset_transport(
    registry: SourceRegistry,
    *,
    public_recovery_path: Path,
    private_recovery_path: Path,
    private_output_path: Path,
    receipt_output_path: Path,
    expected_guild_label: str = "Argentum",
    curl_executable: str | None = None,
    timeout_seconds: float = 60.0,
    max_probe_bytes: int = _DEFAULT_MAX_PROBE_BYTES,
    runner: RunCommand = subprocess.run,
) -> dict[str, Any]:
    """Probe bounded curl transport profiles without downloading the full SPA asset."""
    if timeout_seconds < 15 or timeout_seconds > 180:
        raise ValueError("timeout_seconds must be between 15 and 180")
    if max_probe_bytes < 1024 or max_probe_bytes > 4 * 1024 * 1024:
        raise ValueError("max_probe_bytes must be between 1 KiB and 4 MiB")

    public_recovery, public_recovery_body = _load_object(
        public_recovery_path, "public guild asset recovery"
    )
    private_recovery, private_recovery_body = _load_object(
        private_recovery_path, "private guild asset recovery"
    )
    source_guild_id, asset_url = _validate_recovery(
        public_recovery,
        private_recovery,
        private_recovery_body=private_recovery_body,
        expected_guild_label=expected_guild_label,
    )

    asset_parts = urlsplit(asset_url)
    source_parts = urlsplit(registry.base_url)
    if asset_parts.scheme != "https" or asset_parts.hostname != source_parts.hostname:
        raise ValueError("transport diagnostic URL escaped the configured HTTPS source host")

    executable = _resolve_curl(curl_executable)
    private_output_path.parent.mkdir(parents=True, exist_ok=True)
    probe_path = private_output_path.with_name(
        f".{private_output_path.stem}.{os.getpid()}.probe.part"
    )
    attempts: list[dict[str, Any]] = []
    selected_profile: str | None = None
    try:
        for profile_name, profile_args in _TRANSPORT_PROFILES:
            probe_path.unlink(missing_ok=True)
            command: Sequence[str] = (
                executable,
                "--silent",
                "--show-error",
                "--compressed",
                "--proto",
                "=https",
                "--max-redirs",
                "0",
                "--connect-timeout",
                "20",
                "--max-time",
                f"{timeout_seconds:g}",
                "--retry",
                "0",
                "--range",
                "0-0",
                "--max-filesize",
                str(max_probe_bytes),
                "--user-agent",
                "CoA-Raid-Intelligence-Workbench/0.1 guild-asset-transport-diagnostic",
                *profile_args,
                "--output",
                str(probe_path),
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
                    timeout=timeout_seconds + 30,
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

            http_status = _http_status(stdout)
            probe_bytes = probe_path.stat().st_size if probe_path.is_file() else 0
            transport_reached = http_status is not None and 100 <= http_status <= 599
            failure_class = _failure_class(
                return_code,
                http_status=http_status,
                process_timed_out=process_timed_out,
            )
            attempts.append(
                {
                    "profile": profile_name,
                    "profile_args": list(profile_args),
                    "return_code": return_code,
                    "http_status": http_status,
                    "probe_bytes": probe_bytes,
                    "transport_reached": transport_reached,
                    "failure_class": failure_class,
                    "stderr": stderr,
                }
            )
            if transport_reached:
                selected_profile = profile_name
                break
    finally:
        probe_path.unlink(missing_ok=True)

    public_attempts = [
        {
            "profile": attempt["profile"],
            "return_code": attempt["return_code"],
            "http_status": attempt["http_status"],
            "probe_bytes": attempt["probe_bytes"],
            "transport_reached": attempt["transport_reached"],
            "failure_class": attempt["failure_class"],
        }
        for attempt in attempts
    ]
    probe_size_bounded = all(
        int(attempt["probe_bytes"]) <= max_probe_bytes for attempt in attempts
    )
    checks = {
        "public_asset_recovery_verified": True,
        "private_asset_recovery_sha256_verified": True,
        "baseline_tls_failure_verified": True,
        "asset_url_same_origin": asset_parts.hostname == source_parts.hostname,
        "asset_url_https": asset_parts.scheme == "https",
        "redirects_disabled": True,
        "credentials_not_supplied": True,
        "range_probe_used": True,
        "probe_size_bounded": probe_size_bounded,
        "profile_attempt_count_bounded": len(attempts) <= len(_TRANSPORT_PROFILES),
        "public_receipt_scalar_boundary_preserved": True,
    }
    all_integrity_checks_passed = all(checks.values())
    ready_for_profiled_recovery = all_integrity_checks_passed and selected_profile is not None

    private_payload = {
        "schema_version": 1,
        "diagnostic_kind": "guild_identity_asset_transport_diagnostic_private",
        "diagnostic_version": _DIAGNOSTIC_VERSION,
        "generated_at": _generated_at(),
        "source_public_recovery_name": public_recovery_path.name,
        "source_public_recovery_sha256": _sha256_bytes(public_recovery_body),
        "source_private_recovery_name": private_recovery_path.name,
        "source_private_recovery_sha256": _sha256_bytes(private_recovery_body),
        "target_guild_label": expected_guild_label,
        "candidate_source_guild_id": source_guild_id,
        "asset_url": asset_url,
        "curl_executable": executable,
        "attempts": attempts,
        "selected_profile": selected_profile,
        "summary": {
            "attempt_count": len(attempts),
            "transport_profile_candidate_observed": selected_profile is not None,
            "contains_source_scalar_values": True,
        },
    }
    private_body = _write_json(private_output_path, private_payload)

    receipt = {
        "schema_version": 1,
        "diagnostic_kind": "guild_identity_asset_transport_diagnostic",
        "diagnostic_version": _DIAGNOSTIC_VERSION,
        "generated_at": _generated_at(),
        "source_public_recovery_name": public_recovery_path.name,
        "source_public_recovery_sha256": _sha256_bytes(public_recovery_body),
        "source_private_recovery_name": private_recovery_path.name,
        "source_private_recovery_sha256": _sha256_bytes(private_recovery_body),
        "source_private_diagnostic_name": private_output_path.name,
        "source_private_diagnostic_sha256": _sha256_bytes(private_body),
        "target": {
            "guild_label": expected_guild_label,
            "source_guild_id_published": False,
            "asset_url_published": False,
        },
        "baseline": {
            "transport": "curl",
            "return_code": 35,
            "http_status": 0,
            "failure_class": "network_or_tls_failure",
        },
        "probe": {
            "timeout_seconds_per_profile": timeout_seconds,
            "max_probe_bytes": max_probe_bytes,
            "redirects_allowed": False,
            "credentials_supplied": False,
            "range_request": "0-0",
        },
        "attempts": public_attempts,
        "summary": {
            "attempt_count": len(attempts),
            "selected_profile": selected_profile,
            "transport_profile_candidate_observed": selected_profile is not None,
            "integrity_check_count": len(checks),
            "all_integrity_checks_passed": all_integrity_checks_passed,
            "contains_source_scalar_values": False,
            "contains_error_text": False,
        },
        "integrity_checks": checks,
        "decision_boundary": {
            "status": (
                "guild_asset_transport_profile_observed"
                if ready_for_profiled_recovery
                else "guild_asset_transport_diagnostic_incomplete"
            ),
            "snapshot_internal_identity_consistent": True,
            "transport_profile_candidate_observed": selected_profile is not None,
            "ready_for_profiled_asset_recovery": ready_for_profiled_recovery,
            "guild_api_route_candidates_observed": False,
            "guild_api_route_semantics_verified": False,
            "independent_source_identity_verified": False,
            "guild_identity_verified": False,
            "ready_for_guild_api_route_review": False,
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


__all__ = ["diagnose_guild_identity_asset_transport"]
