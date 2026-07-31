from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .guild_identity_asset_recovery import recover_guild_identity_asset
from .raw_archive import RawArchive
from .source_registry import SourceRegistry

_PROFILED_RECOVERY_VERSION = "guild-identity-asset-profiled-recovery-v1"
_DIAGNOSTIC_VERSION = "guild-identity-asset-transport-diagnostic-v1"
_PUBLIC_DIAGNOSTIC_KIND = "guild_identity_asset_transport_diagnostic"
_PRIVATE_DIAGNOSTIC_KIND = "guild_identity_asset_transport_diagnostic_private"

_PROFILE_ARGS: dict[str, tuple[str, ...]] = {
    "http1_1": ("--http1.1",),
    "ipv4_http1_1": ("--ipv4", "--http1.1"),
    "tls12_http1_1": ("--tlsv1.2", "--tls-max", "1.2", "--http1.1"),
    "ipv4_tls12_http1_1": (
        "--ipv4",
        "--tlsv1.2",
        "--tls-max",
        "1.2",
        "--http1.1",
    ),
    "revocation_best_effort_http1_1": (
        "--ssl-revoke-best-effort",
        "--http1.1",
    ),
}

RunCommand = Callable[..., Any]


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
    path.write_bytes(body)
    return body


def _required_object(value: object, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"profiled recovery field {field_name} must be an object")
    return value


def _required_list(value: object, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"profiled recovery field {field_name} must be a list")
    return value


def _validate_hash(path: Path, expected: object, label: str) -> bytes:
    if not isinstance(expected, str) or len(expected) != 64:
        raise ValueError(f"{label} SHA-256 is missing")
    try:
        body = path.read_bytes()
    except OSError as exc:
        raise ValueError(f"unable to read {label}: {path}") from exc
    if _sha256_bytes(body) != expected:
        raise ValueError(f"{label} SHA-256 mismatch")
    return body


def _selected_attempt(
    public_diagnostic: Mapping[str, Any], selected_profile: str
) -> dict[str, Any]:
    attempts = _required_list(public_diagnostic.get("attempts"), "diagnostic.attempts")
    matches = [
        attempt
        for attempt in attempts
        if isinstance(attempt, dict) and attempt.get("profile") == selected_profile
    ]
    if len(matches) != 1:
        raise ValueError("diagnostic must contain exactly one selected profile attempt")
    return matches[0]


def _validate_diagnostic(
    public_diagnostic: Mapping[str, Any],
    private_diagnostic: Mapping[str, Any],
    *,
    private_diagnostic_body: bytes,
    public_recovery_path: Path,
    private_recovery_path: Path,
    expected_guild_label: str,
) -> tuple[str, int | str, str, bytes, bytes]:
    if public_diagnostic.get("schema_version") != 1:
        raise ValueError("public transport diagnostic schema mismatch")
    if public_diagnostic.get("diagnostic_kind") != _PUBLIC_DIAGNOSTIC_KIND:
        raise ValueError("public transport diagnostic kind mismatch")
    if public_diagnostic.get("diagnostic_version") != _DIAGNOSTIC_VERSION:
        raise ValueError("public transport diagnostic version mismatch")

    target = _required_object(public_diagnostic.get("target"), "diagnostic.target")
    if target.get("guild_label") != expected_guild_label:
        raise ValueError("public transport diagnostic guild label mismatch")
    if target.get("source_guild_id_published") is not False:
        raise ValueError("public transport diagnostic publishes source guild ID")
    if target.get("asset_url_published") is not False:
        raise ValueError("public transport diagnostic publishes asset URL")

    summary = _required_object(
        public_diagnostic.get("summary"), "diagnostic.summary"
    )
    if summary.get("contains_source_scalar_values") is not False:
        raise ValueError("public transport diagnostic is not scalar-free")
    if summary.get("contains_error_text") is not False:
        raise ValueError("public transport diagnostic publishes error text")
    if summary.get("transport_profile_candidate_observed") is not True:
        raise ValueError("transport profile candidate was not observed")
    selected_profile = summary.get("selected_profile")
    if not isinstance(selected_profile, str) or selected_profile not in _PROFILE_ARGS:
        raise ValueError("selected transport profile is missing or unsupported")

    attempt = _selected_attempt(public_diagnostic, selected_profile)
    if attempt.get("transport_reached") is not True:
        raise ValueError("selected transport profile did not reach HTTP")
    http_status = attempt.get("http_status")
    if not isinstance(http_status, int) or not 200 <= http_status <= 299:
        raise ValueError("selected transport profile did not receive a 2xx response")

    checks = _required_object(
        public_diagnostic.get("integrity_checks"), "diagnostic.integrity_checks"
    )
    required_true_checks = (
        "asset_url_https",
        "asset_url_same_origin",
        "credentials_not_supplied",
        "private_asset_recovery_sha256_verified",
        "profile_attempt_count_bounded",
        "public_asset_recovery_verified",
        "public_receipt_scalar_boundary_preserved",
        "range_probe_used",
        "redirects_disabled",
    )
    for field_name in required_true_checks:
        if checks.get(field_name) is not True:
            raise ValueError(f"transport diagnostic integrity mismatch: {field_name}")

    probe = _required_object(public_diagnostic.get("probe"), "diagnostic.probe")
    probe_limit = probe.get("max_probe_bytes")
    probe_bytes = attempt.get("probe_bytes")
    all_checks_passed = summary.get("all_integrity_checks_passed") is True
    if not all_checks_passed:
        if checks.get("probe_size_bounded") is not False:
            raise ValueError("unsupported transport diagnostic integrity failure")
        if attempt.get("return_code") != 63:
            raise ValueError("range-ignored diagnostic must stop with curl code 63")
        if not isinstance(probe_limit, int) or not isinstance(probe_bytes, int):
            raise ValueError("range-ignored diagnostic byte counts are missing")
        if probe_bytes <= probe_limit:
            raise ValueError("range-ignored diagnostic did not exceed probe limit")

    expected_private_hash = public_diagnostic.get("source_private_diagnostic_sha256")
    if not isinstance(expected_private_hash, str) or len(expected_private_hash) != 64:
        raise ValueError("public transport diagnostic private hash is missing")
    if _sha256_bytes(private_diagnostic_body) != expected_private_hash:
        raise ValueError("private transport diagnostic SHA-256 mismatch")

    if private_diagnostic.get("schema_version") != 1:
        raise ValueError("private transport diagnostic schema mismatch")
    if private_diagnostic.get("diagnostic_kind") != _PRIVATE_DIAGNOSTIC_KIND:
        raise ValueError("private transport diagnostic kind mismatch")
    if private_diagnostic.get("diagnostic_version") != _DIAGNOSTIC_VERSION:
        raise ValueError("private transport diagnostic version mismatch")
    if private_diagnostic.get("target_guild_label") != expected_guild_label:
        raise ValueError("private transport diagnostic guild label mismatch")
    if private_diagnostic.get("selected_profile") != selected_profile:
        raise ValueError("private transport diagnostic selected profile mismatch")

    private_summary = _required_object(
        private_diagnostic.get("summary"), "private_diagnostic.summary"
    )
    if private_summary.get("contains_source_scalar_values") is not True:
        raise ValueError("private transport diagnostic scalar boundary mismatch")
    source_guild_id = private_diagnostic.get("candidate_source_guild_id")
    if isinstance(source_guild_id, bool) or not isinstance(
        source_guild_id, (int, str)
    ):
        raise ValueError("private transport diagnostic guild ID is invalid")
    asset_url = private_diagnostic.get("asset_url")
    if not isinstance(asset_url, str) or not asset_url:
        raise ValueError("private transport diagnostic asset URL is missing")

    public_recovery_body = _validate_hash(
        public_recovery_path,
        public_diagnostic.get("source_public_recovery_sha256"),
        "public asset recovery",
    )
    private_recovery_body = _validate_hash(
        private_recovery_path,
        public_diagnostic.get("source_private_recovery_sha256"),
        "private asset recovery",
    )
    return (
        selected_profile,
        source_guild_id,
        asset_url,
        public_recovery_body,
        private_recovery_body,
    )


def recover_guild_identity_asset_profiled(
    registry: SourceRegistry,
    archive: RawArchive,
    *,
    public_diagnostic_path: Path,
    private_diagnostic_path: Path,
    public_recovery_path: Path,
    private_recovery_path: Path,
    public_route_discovery_path: Path,
    private_route_discovery_path: Path,
    private_output_path: Path,
    receipt_output_path: Path,
    expected_guild_label: str = "Argentum",
    curl_executable: str | None = None,
    timeout_seconds: float = 300.0,
    max_bytes: int = 64 * 1024 * 1024,
    runner: RunCommand = subprocess.run,
) -> dict[str, Any]:
    """Recover the asset with the exact transport profile selected by diagnostics."""
    public_diagnostic, public_diagnostic_body = _load_object(
        public_diagnostic_path, "public transport diagnostic"
    )
    private_diagnostic, private_diagnostic_body = _load_object(
        private_diagnostic_path, "private transport diagnostic"
    )
    (
        selected_profile,
        source_guild_id,
        diagnostic_asset_url,
        public_recovery_body,
        private_recovery_body,
    ) = _validate_diagnostic(
        public_diagnostic,
        private_diagnostic,
        private_diagnostic_body=private_diagnostic_body,
        public_recovery_path=public_recovery_path,
        private_recovery_path=private_recovery_path,
        expected_guild_label=expected_guild_label,
    )

    profile_args = _PROFILE_ARGS[selected_profile]

    def profiled_runner(command: Sequence[str], **kwargs: Any) -> Any:
        prepared = list(command)
        if not prepared:
            raise ValueError("curl command is empty")
        prepared[-1:-1] = profile_args
        return runner(prepared, **kwargs)

    receipt = recover_guild_identity_asset(
        registry,
        archive,
        public_route_discovery_path=public_route_discovery_path,
        private_route_discovery_path=private_route_discovery_path,
        private_output_path=private_output_path,
        receipt_output_path=receipt_output_path,
        expected_guild_label=expected_guild_label,
        curl_executable=curl_executable,
        timeout_seconds=timeout_seconds,
        max_bytes=max_bytes,
        runner=profiled_runner,
    )

    private_payload, _ = _load_object(private_output_path, "profiled private recovery")
    if private_payload.get("candidate_source_guild_id") != source_guild_id:
        raise ValueError("profiled recovery guild ID does not match diagnostic")
    if private_payload.get("asset_url") != diagnostic_asset_url:
        raise ValueError("profiled recovery asset URL does not match diagnostic")

    private_payload.update(
        {
            "recovery_kind": "guild_identity_asset_profiled_recovery_private",
            "recovery_version": _PROFILED_RECOVERY_VERSION,
            "source_public_diagnostic_name": public_diagnostic_path.name,
            "source_public_diagnostic_sha256": _sha256_bytes(
                public_diagnostic_body
            ),
            "source_private_diagnostic_name": private_diagnostic_path.name,
            "source_private_diagnostic_sha256": _sha256_bytes(
                private_diagnostic_body
            ),
            "source_public_recovery_name": public_recovery_path.name,
            "source_public_recovery_sha256": _sha256_bytes(public_recovery_body),
            "source_private_recovery_name": private_recovery_path.name,
            "source_private_recovery_sha256": _sha256_bytes(private_recovery_body),
            "selected_transport_profile": selected_profile,
            "selected_transport_profile_args": list(profile_args),
        }
    )
    private_body = _write_json(private_output_path, private_payload)

    transport = _required_object(receipt.get("transport"), "receipt.transport")
    transport["profile"] = selected_profile
    checks = _required_object(receipt.get("integrity_checks"), "receipt.checks")
    checks.update(
        {
            "public_transport_diagnostic_verified": True,
            "private_transport_diagnostic_sha256_verified": True,
            "selected_transport_profile_verified": True,
            "diagnostic_asset_binding_verified": True,
            "diagnostic_guild_id_binding_verified": True,
        }
    )
    summary = _required_object(receipt.get("summary"), "receipt.summary")
    summary["integrity_check_count"] = len(checks)
    summary["all_integrity_checks_passed"] = all(checks.values())

    receipt.update(
        {
            "recovery_kind": "guild_identity_asset_profiled_recovery",
            "recovery_version": _PROFILED_RECOVERY_VERSION,
            "source_public_diagnostic_name": public_diagnostic_path.name,
            "source_public_diagnostic_sha256": _sha256_bytes(
                public_diagnostic_body
            ),
            "source_private_diagnostic_name": private_diagnostic_path.name,
            "source_private_diagnostic_sha256": _sha256_bytes(
                private_diagnostic_body
            ),
            "source_public_recovery_name": public_recovery_path.name,
            "source_public_recovery_sha256": _sha256_bytes(public_recovery_body),
            "source_private_recovery_name": private_output_path.name,
            "source_private_recovery_sha256": _sha256_bytes(private_body),
        }
    )
    _write_json(receipt_output_path, receipt)
    return receipt


__all__ = ["recover_guild_identity_asset_profiled"]
