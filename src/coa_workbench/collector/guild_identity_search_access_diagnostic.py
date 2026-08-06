from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import parse_qsl, urlsplit

from .raw_archive import RawArchive, RawCapture, request_key_from_url
from .source_registry import SourceRegistry

_DIAGNOSTIC_VERSION = "guild-identity-search-access-diagnostic-v1"
_PROBE_VERSION = "guild-identity-search-probe-v1"
_SEARCH_ROUTE = "/api/guilds/search"
_PROFILE_ORDER = (
    "minimal_http1_1",
    "spa_fetch_context",
    "spa_fetch_context_origin",
)
_DEFAULT_MAX_BYTES = 256 * 1024

RunCommand = Callable[..., Any]


def _generated_at() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _load_object(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    try:
        body = path.read_bytes()
        payload = json.loads(body)
    except OSError as exc:
        raise ValueError(f"unable to read {label}: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is not valid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return payload, body


def _write_json(path: Path, payload: Mapping[str, Any]) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(body)
    temporary.replace(path)
    return body


def _required_object(value: object, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"guild search access field {field_name} must be an object")
    return value


def _resolve_curl(executable: str | None) -> str:
    if executable:
        return executable
    for candidate in ("curl.exe", "curl"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    raise ValueError("curl executable was not found")


def _validate_inputs(
    public_probe: Mapping[str, Any],
    private_probe: Mapping[str, Any],
    *,
    private_probe_body: bytes,
    expected_guild_label: str,
    registry: SourceRegistry,
) -> str:
    expected_public = {
        "schema_version": 1,
        "probe_kind": "guild_identity_search_probe",
        "probe_version": _PROBE_VERSION,
    }
    for field_name, expected in expected_public.items():
        if public_probe.get(field_name) != expected:
            raise ValueError(f"public guild search probe mismatch: {field_name}")

    target = _required_object(public_probe.get("target"), "public.target")
    if target.get("guild_label") != expected_guild_label:
        raise ValueError("public guild search guild label mismatch")
    if target.get("source_guild_id_published") is not False:
        raise ValueError("public guild search publishes source guild ID")
    if target.get("request_url_published") is not False:
        raise ValueError("public guild search publishes request URL")

    summary = _required_object(public_probe.get("summary"), "public.summary")
    expected_summary = {
        "all_integrity_checks_passed": True,
        "response_completed": False,
        "contains_source_scalar_values": False,
        "contains_error_text": False,
    }
    for field_name, expected in expected_summary.items():
        if summary.get(field_name) != expected:
            raise ValueError(f"public guild search summary mismatch: {field_name}")

    request = _required_object(public_probe.get("request"), "public.request")
    expected_request = {
        "route_template": _SEARCH_ROUTE,
        "query_keys": ["q", "limit"],
        "transport_profile": "http1_1",
        "redirects_allowed": False,
        "credentials_supplied": False,
    }
    for field_name, expected in expected_request.items():
        if request.get(field_name) != expected:
            raise ValueError(f"public guild search request mismatch: {field_name}")

    response = _required_object(public_probe.get("response"), "public.response")
    if response.get("http_status") != 403:
        raise ValueError("access diagnostic requires an HTTP 403 baseline")
    if response.get("failure_class") != "http_status_failure":
        raise ValueError("public guild search failure class mismatch")
    if response.get("capture") is not None:
        raise ValueError("HTTP 403 baseline unexpectedly captured a body")

    boundary = _required_object(public_probe.get("decision_boundary"), "public.boundary")
    if boundary.get("guild_api_route_candidates_observed") is not True:
        raise ValueError("guild API route candidate was not observed")
    for field_name in (
        "guild_api_route_semantics_verified",
        "independent_source_identity_verified",
        "guild_identity_verified",
        "ready_for_guild_filtering",
        "ready_for_full_guild_crawl",
        "planner_scoring_allowed",
    ):
        if boundary.get(field_name) is not False:
            raise ValueError(f"public guild search boundary mismatch: {field_name}")

    expected_private_hash = public_probe.get("source_private_probe_sha256")
    if not isinstance(expected_private_hash, str) or len(expected_private_hash) != 64:
        raise ValueError("public guild search private SHA-256 is missing")
    if _sha256_bytes(private_probe_body) != expected_private_hash:
        raise ValueError("private guild search probe SHA-256 mismatch")

    expected_private = {
        "schema_version": 1,
        "probe_kind": "guild_identity_search_probe_private",
        "probe_version": _PROBE_VERSION,
        "target_guild_label": expected_guild_label,
    }
    for field_name, expected in expected_private.items():
        if private_probe.get(field_name) != expected:
            raise ValueError(f"private guild search probe mismatch: {field_name}")

    private_summary = _required_object(private_probe.get("summary"), "private.summary")
    if private_summary.get("response_completed") is not False:
        raise ValueError("private guild search probe unexpectedly completed")
    if private_summary.get("contains_source_scalar_values") is not True:
        raise ValueError("private guild search scalar boundary mismatch")

    transport = _required_object(private_probe.get("transport"), "private.transport")
    if transport.get("profile") != "http1_1":
        raise ValueError("private guild search transport profile mismatch")
    if transport.get("http_status") != 403:
        raise ValueError("private guild search HTTP status mismatch")
    if transport.get("failure_class") != "http_status_failure":
        raise ValueError("private guild search failure class mismatch")

    request_url = private_probe.get("request_url")
    if not isinstance(request_url, str) or not request_url:
        raise ValueError("private guild search request URL is missing")
    source_parts = urlsplit(registry.base_url)
    target_parts = urlsplit(request_url)
    if target_parts.scheme != "https" or target_parts.hostname != source_parts.hostname:
        raise ValueError("private guild search URL escaped the configured HTTPS host")
    if target_parts.path != _SEARCH_ROUTE:
        raise ValueError("private guild search URL path mismatch")
    query_keys = sorted(key for key, _value in parse_qsl(target_parts.query))
    if query_keys != ["limit", "q"]:
        raise ValueError("private guild search URL query keys changed")
    return request_url


def _profile_headers(profile: str, base_url: str) -> tuple[tuple[str, str], ...]:
    if profile == "minimal_http1_1":
        return (
            ("Accept", "application/json, text/plain, */*"),
            (
                "User-Agent",
                "CoA-Raid-Intelligence-Workbench/0.1 guild-search-access",
            ),
        )
    if profile not in _PROFILE_ORDER:
        raise ValueError(f"unsupported guild search access profile: {profile}")
    headers = (
        ("Accept", "application/json, text/plain, */*"),
        ("Accept-Language", "en-US,en;q=0.9"),
        ("Cache-Control", "no-cache"),
        ("Pragma", "no-cache"),
        (
            "User-Agent",
            (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/138.0.0.0 Safari/537.36"
            ),
        ),
        ("Referer", f"{base_url.rstrip('/')}/"),
        ("Sec-Fetch-Dest", "empty"),
        ("Sec-Fetch-Mode", "cors"),
        ("Sec-Fetch-Site", "same-origin"),
    )
    if profile == "spa_fetch_context_origin":
        return (*headers, ("Origin", base_url.rstrip("/")))
    return headers


def _failure_class(return_code: int | None, timed_out: bool) -> str | None:
    if timed_out or return_code == 28:
        return "timeout"
    if return_code in {5, 6, 7, 35, 52, 55, 60, 92}:
        return "network_or_tls_failure"
    if return_code in {23, 26, 63}:
        return "response_too_large_or_write_failure"
    if return_code not in {None, 0}:
        return "curl_failure"
    return None


def _top_level_shape(payload: object | None) -> tuple[str | None, list[str]]:
    if isinstance(payload, dict):
        return "object", sorted(str(key) for key in payload)
    if isinstance(payload, list):
        return "array", []
    if payload is None:
        return None, []
    if isinstance(payload, bool):
        return "boolean", []
    if isinstance(payload, (int, float)):
        return "number", []
    return "string", []


def _error_field_names(value: object) -> list[str]:
    names: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = "".join(char for char in str(key).casefold() if char.isalnum())
            if normalized in {
                "code",
                "detail",
                "error",
                "errors",
                "message",
                "reason",
                "status",
            }:
                names.add(str(key))
            names.update(_error_field_names(child))
    elif isinstance(value, list):
        for child in value[:25]:
            names.update(_error_field_names(child))
    return sorted(names)


def _denial_category(body: bytes, payload: object | None) -> str:
    text = (
        json.dumps(payload, ensure_ascii=False, sort_keys=True)
        if payload is not None
        else body.decode("utf-8", errors="replace")
    ).casefold()
    categories = (
        ("csrf_required", ("csrf", "cross-site request forgery")),
        ("bot_challenge", ("captcha", "challenge", "cloudflare", "bot")),
        (
            "authentication_required",
            ("authenticate", "authentication", "login", "token"),
        ),
        ("access_denied", ("forbidden", "access denied", "permission")),
        ("rate_limited", ("rate limit", "too many requests")),
        ("validation_error", ("invalid", "required", "validation")),
    )
    for category, tokens in categories:
        if any(token in text for token in tokens):
            return category
    return "unclassified"


def _capture_summary(capture: RawCapture | None) -> dict[str, Any] | None:
    if capture is None:
        return None
    return {
        "raw_id": capture.raw_id,
        "observation_id": capture.observation_id,
        "payload_hash": capture.payload_hash,
        "schema_fingerprint": capture.schema_fingerprint,
        "bytes_uncompressed": capture.bytes_uncompressed,
    }


def capture_guild_identity_search_access_diagnostic(
    registry: SourceRegistry,
    archive: RawArchive,
    *,
    public_search_probe_path: Path,
    private_search_probe_path: Path,
    private_output_path: Path,
    receipt_output_path: Path,
    expected_guild_label: str = "Argentum",
    curl_executable: str | None = None,
    timeout_seconds: float = 60.0,
    max_bytes: int = _DEFAULT_MAX_BYTES,
    runner: RunCommand = subprocess.run,
) -> dict[str, Any]:
    """Capture denied bodies and test bounded no-credential browser profiles."""
    if timeout_seconds < 10 or timeout_seconds > 300:
        raise ValueError("timeout_seconds must be between 10 and 300")
    if max_bytes < 64 * 1024 or max_bytes > 1024 * 1024:
        raise ValueError("max_bytes must be between 64 KiB and 1 MiB")

    public_probe, public_probe_body = _load_object(
        public_search_probe_path,
        "public guild search probe",
    )
    private_probe, private_probe_body = _load_object(
        private_search_probe_path,
        "private guild search probe",
    )
    request_url = _validate_inputs(
        public_probe,
        private_probe,
        private_probe_body=private_probe_body,
        expected_guild_label=expected_guild_label,
        registry=registry,
    )

    executable = _resolve_curl(curl_executable)
    private_output_path.parent.mkdir(parents=True, exist_ok=True)
    private_attempts: list[dict[str, Any]] = []
    public_attempts: list[dict[str, Any]] = []
    selected_profile: str | None = None

    for profile in _PROFILE_ORDER:
        temporary_body = private_output_path.with_name(
            f".{private_output_path.stem}.{os.getpid()}.{profile}.body.part"
        )
        temporary_body.unlink(missing_ok=True)
        headers = _profile_headers(profile, registry.base_url)
        forbidden_headers = {
            "authorization",
            "cookie",
            "proxy-authorization",
            "x-api-key",
        }
        if any(name.casefold() in forbidden_headers for name, _value in headers):
            raise ValueError("guild search access profile contains credentials")

        command = [
            executable,
            "--silent",
            "--show-error",
            "--compressed",
            "--http1.1",
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
            "--max-filesize",
            str(max_bytes),
        ]
        for name, value in headers:
            command.extend(("--header", f"{name}: {value}"))
        command.extend(
            (
                "--output",
                str(temporary_body),
                "--write-out",
                "%{http_code}\n%{content_type}",
                request_url,
            )
        )

        timed_out = False
        stderr = ""
        try:
            completed = runner(
                command,
                capture_output=True,
                text=True,
                timeout=timeout_seconds + 30,
                check=False,
            )
            return_code = int(completed.returncode)
            stdout_lines = str(completed.stdout or "").strip().splitlines()
            stderr = str(completed.stderr or "").strip()
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            return_code = None
            stdout_lines = []
            stderr = str(exc)

        http_status = (
            int(stdout_lines[0])
            if stdout_lines and stdout_lines[0].isdigit()
            else None
        )
        content_type = stdout_lines[1].strip() if len(stdout_lines) > 1 else None
        body = temporary_body.read_bytes() if temporary_body.is_file() else None
        failure_class = _failure_class(return_code, timed_out)
        if body is not None and not body:
            body = None
            failure_class = failure_class or "empty_response"
        if body is not None and len(body) > max_bytes:
            body = None
            failure_class = "response_too_large_or_write_failure"
        if body is None and failure_class is None:
            failure_class = "missing_response"

        payload: object | None = None
        json_valid = False
        if body is not None:
            try:
                payload = json.loads(body)
                json_valid = True
            except (UnicodeDecodeError, json.JSONDecodeError):
                pass

        capture = None
        if body is not None:
            capture = archive.capture_bytes(
                body,
                source_code=registry.source_code,
                endpoint_code="guild_identity_search_access_diagnostic",
                request_key=request_key_from_url("GET", request_url),
                fetched_at=datetime.now(timezone.utc),
                http_status=http_status,
                content_type=content_type or "application/octet-stream",
                request_url=request_url,
                metadata={
                    "capture_mode": "bounded_guild_search_access_diagnostic",
                    "profile": profile,
                    "transport": "curl_http1_1",
                    "redirects_allowed": False,
                    "credentials_supplied": False,
                    "max_bytes": max_bytes,
                    "timeout_seconds": timeout_seconds,
                    "source_public_probe_sha256": _sha256_bytes(public_probe_body),
                    "source_private_probe_sha256": _sha256_bytes(private_probe_body),
                },
            )

        top_level_kind, top_level_keys = _top_level_shape(payload)
        denial_category = (
            _denial_category(body, payload)
            if body is not None and http_status == 403
            else None
        )
        response_candidate = (
            return_code == 0
            and body is not None
            and json_valid
            and http_status is not None
            and 200 <= http_status <= 299
        )
        capture_summary = _capture_summary(capture)

        private_attempts.append(
            {
                "profile": profile,
                "header_names": [name for name, _value in headers],
                "return_code": return_code,
                "http_status": http_status,
                "content_type": content_type,
                "failure_class": failure_class,
                "stderr": stderr,
                "body": payload if json_valid else None,
                "body_text": (
                    body.decode("utf-8", errors="replace")
                    if body is not None and not json_valid
                    else None
                ),
                "capture": capture_summary,
                "denial_category": denial_category,
                "response_candidate": response_candidate,
            }
        )
        public_attempts.append(
            {
                "profile": profile,
                "return_code": return_code,
                "http_status": http_status,
                "content_type": content_type,
                "failure_class": failure_class,
                "body_captured": body is not None,
                "body_bytes": len(body) if body is not None else 0,
                "json_valid": json_valid,
                "top_level_kind": top_level_kind,
                "top_level_keys": top_level_keys,
                "error_field_names": _error_field_names(payload),
                "denial_category": denial_category,
                "capture": capture_summary,
                "response_candidate": response_candidate,
                "contains_source_scalar_values": False,
                "contains_error_text": False,
            }
        )
        temporary_body.unlink(missing_ok=True)
        if response_candidate:
            selected_profile = profile
            break

    denial_categories = sorted(
        {
            str(attempt["denial_category"])
            for attempt in public_attempts
            if attempt["denial_category"] is not None
        }
    )
    access_candidate = selected_profile is not None
    denial_observed = bool(denial_categories)
    checks = {
        "public_search_probe_verified": True,
        "private_search_probe_sha256_verified": True,
        "http_403_baseline_verified": True,
        "request_url_https": urlsplit(request_url).scheme == "https",
        "request_url_same_origin": (
            urlsplit(request_url).hostname == urlsplit(registry.base_url).hostname
        ),
        "attempt_count_bounded": 1 <= len(public_attempts) <= len(_PROFILE_ORDER),
        "profile_order_bounded": [row["profile"] for row in public_attempts]
        == list(_PROFILE_ORDER[: len(public_attempts)]),
        "redirects_disabled": True,
        "credentials_not_supplied": True,
        "response_size_bounded": all(
            int(row["body_bytes"]) <= max_bytes for row in public_attempts
        ),
        "captured_bodies_archived": all(
            not row["body_captured"] or row["capture"] is not None
            for row in public_attempts
        ),
        "public_receipt_scalar_boundary_preserved": True,
        "error_text_not_published": True,
    }

    private_payload = {
        "schema_version": 1,
        "diagnostic_kind": "guild_identity_search_access_diagnostic_private",
        "diagnostic_version": _DIAGNOSTIC_VERSION,
        "generated_at": _generated_at(),
        "source_public_probe_name": public_search_probe_path.name,
        "source_public_probe_sha256": _sha256_bytes(public_probe_body),
        "source_private_probe_name": private_search_probe_path.name,
        "source_private_probe_sha256": _sha256_bytes(private_probe_body),
        "target_guild_label": expected_guild_label,
        "request_url": request_url,
        "attempts": private_attempts,
        "selected_profile": selected_profile,
        "summary": {
            "attempt_count": len(private_attempts),
            "access_profile_candidate_observed": access_candidate,
            "denial_categories": denial_categories,
            "contains_source_scalar_values": True,
        },
    }
    private_body = _write_json(private_output_path, private_payload)

    status = (
        "guild_search_access_profile_candidate_observed"
        if access_candidate
        else "guild_search_access_denial_observed"
        if denial_observed
        else "guild_search_access_diagnostic_incomplete"
    )
    receipt = {
        "schema_version": 1,
        "diagnostic_kind": "guild_identity_search_access_diagnostic",
        "diagnostic_version": _DIAGNOSTIC_VERSION,
        "generated_at": _generated_at(),
        "source_public_probe_name": public_search_probe_path.name,
        "source_public_probe_sha256": _sha256_bytes(public_probe_body),
        "source_private_diagnostic_name": private_output_path.name,
        "source_private_diagnostic_sha256": _sha256_bytes(private_body),
        "target": {
            "guild_label": expected_guild_label,
            "request_url_published": False,
            "source_guild_id_published": False,
        },
        "request": {
            "route_template": _SEARCH_ROUTE,
            "query_keys": ["q", "limit"],
            "transport": "curl_http1_1",
            "profile_order": list(_PROFILE_ORDER),
            "max_attempt_count": len(_PROFILE_ORDER),
            "timeout_seconds_per_profile": timeout_seconds,
            "max_bytes_per_profile": max_bytes,
            "redirects_allowed": False,
            "credentials_supplied": False,
        },
        "attempts": public_attempts,
        "integrity_checks": checks,
        "decision_boundary": {
            "status": status,
            "guild_api_route_candidates_observed": True,
            "guild_search_http_403_baseline_observed": True,
            "guild_search_denial_category_observed": denial_observed,
            "guild_search_access_profile_candidate_observed": access_candidate,
            "selected_access_profile": selected_profile,
            "ready_for_profiled_guild_search_probe": access_candidate,
            "guild_api_route_semantics_verified": False,
            "independent_source_identity_verified": False,
            "guild_identity_verified": False,
            "ready_for_guild_filtering": False,
            "ready_for_full_guild_crawl": False,
            "ready_for_multi_report_character_graph": False,
            "ready_for_performance_model": False,
            "ready_for_bis25_scoring": False,
            "planner_scoring_allowed": False,
        },
        "summary": {
            "all_integrity_checks_passed": all(checks.values()),
            "integrity_check_count": len(checks),
            "attempt_count": len(public_attempts),
            "selected_access_profile": selected_profile,
            "access_profile_candidate_observed": access_candidate,
            "denial_category_count": len(denial_categories),
            "denial_categories": denial_categories,
            "contains_source_scalar_values": False,
            "contains_error_text": False,
        },
    }
    _write_json(receipt_output_path, receipt)
    return receipt


__all__ = ["capture_guild_identity_search_access_diagnostic"]
