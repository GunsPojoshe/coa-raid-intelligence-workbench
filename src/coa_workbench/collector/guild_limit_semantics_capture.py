from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import urlencode, urljoin, urlsplit

from .raw_archive import RawArchive, RawCapture, request_key_from_url
from .source_registry import SourceRegistry

_CAPTURE_KIND = "guild_limit_semantics_capture"
_CAPTURE_PRIVATE_KIND = "guild_limit_semantics_capture_private"
_CAPTURE_VERSION = "guild-limit-semantics-capture-v1"
_REVIEW_KIND = "guild_route_semantics_review"
_REVIEW_VERSION = "guild-route-semantics-review-v1"
_SEARCH_ROUTE = "/api/guilds/search"
_SELECTED_PROFILE = "spa_fetch_context"
_DEFAULT_MAX_BYTES = 256 * 1024

RunCommand = Callable[..., Any]


def _generated_at() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_json(value: object) -> str:
    body = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _sha256_bytes(body)


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


def _required_object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _required_list(value: object, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")
    return value


def _write_json(path: Path, payload: Mapping[str, Any]) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode()
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(body)
    temporary.replace(path)
    return body


def _resolve_curl(executable: str | None) -> str:
    if executable:
        return executable
    for candidate in ("curl.exe", "curl"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    raise ValueError("curl executable was not found")


def _profile_headers(base_url: str) -> tuple[tuple[str, str], ...]:
    return (
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


def _validate_route_review(receipt: Mapping[str, Any]) -> None:
    expected_root = {
        "schema_version": 1,
        "review_kind": _REVIEW_KIND,
        "review_version": _REVIEW_VERSION,
    }
    for field_name, expected in expected_root.items():
        if receipt.get(field_name) != expected:
            raise ValueError(f"route review mismatch: {field_name}")

    checks = _required_object(receipt.get("integrity_checks"), "route review checks")
    if len(checks) != 22 or not all(value is True for value in checks.values()):
        raise ValueError("route review integrity checks failed")

    summary = _required_object(receipt.get("summary"), "route review summary")
    expected_summary = {
        "all_integrity_checks_passed": True,
        "contains_raw_payload": False,
        "contains_source_scalar_values": False,
        "route_shape_and_response_schema_reviewed": True,
        "limit_parameter_accepted": True,
        "ready_for_bounded_limit_semantics_capture": True,
        "limit_truncation_semantics_verified": False,
        "pagination_semantics_verified": False,
        "termination_semantics_verified": False,
        "completeness_verified": False,
        "guild_api_route_semantics_verified": False,
        "ready_for_full_guild_crawl": False,
        "planner_scoring_allowed": False,
    }
    for field_name, expected in expected_summary.items():
        if summary.get(field_name) != expected:
            raise ValueError(f"route review summary mismatch: {field_name}")

    route_review = _required_object(receipt.get("route_review"), "route review")
    if route_review.get("route_template") != _SEARCH_ROUTE:
        raise ValueError("route review template mismatch")
    expected_route = {
        "contains_query_values": False,
        "query_parameter_q_observed": True,
        "query_shape_with_limit_verified": True,
        "limit_parameter_accepted": True,
        "limit_truncation_semantics_verified": False,
    }
    for field_name, expected in expected_route.items():
        if route_review.get(field_name) != expected:
            raise ValueError(f"route review route mismatch: {field_name}")

    schema = _required_object(
        receipt.get("response_schema_review"),
        "route review response schema",
    )
    if schema.get("contains_source_scalar_values") is not False:
        raise ValueError("route review response schema leaks source values")
    if schema.get("guild_collection_field") != "guilds":
        raise ValueError("route review guild collection mismatch")
    if schema.get("top_level_kind") != "object":
        raise ValueError("route review top-level kind mismatch")
    if schema.get("top_level_keys") != ["guilds", "success"]:
        raise ValueError("route review top-level keys mismatch")
    if schema.get("guild_record_schema_verified") is not True:
        raise ValueError("route review guild record schema is not verified")

    fields = _required_list(schema.get("guild_record_fields"), "guild record fields")
    expected_fields = {
        "id": ["integer"],
        "name": ["string"],
        "realm": ["string"],
        "report_count": ["string"],
    }
    observed_fields: dict[str, object] = {}
    for field in fields:
        value = _required_object(field, "guild record field")
        name = value.get("field")
        if isinstance(name, str):
            observed_fields[name] = value.get("types")
    if observed_fields != expected_fields:
        raise ValueError("route review guild record fields changed")

    boundary = _required_object(
        receipt.get("decision_boundary"),
        "route review decision boundary",
    )
    expected_boundary = {
        "guild_route_template_verified": True,
        "guild_query_shapes_verified": True,
        "guild_response_schema_verified": True,
        "limit_parameter_accepted": True,
        "ready_for_bounded_limit_semantics_capture": True,
        "limit_truncation_semantics_verified": False,
        "pagination_semantics_verified": False,
        "termination_semantics_verified": False,
        "completeness_verified": False,
        "guild_api_route_semantics_verified": False,
        "automatic_full_guild_crawl_allowed": False,
        "ready_for_full_guild_crawl": False,
        "ready_for_multi_report_character_graph": False,
        "ready_for_performance_model": False,
        "ready_for_bis25_scoring": False,
        "planner_scoring_allowed": False,
    }
    for field_name, expected in expected_boundary.items():
        if boundary.get(field_name) != expected:
            raise ValueError(f"route review boundary mismatch: {field_name}")

    target = _required_object(receipt.get("target"), "route review target")
    for field_name in (
        "raw_payload_published",
        "report_ids_published",
        "request_urls_published",
        "source_guild_id_published",
    ):
        if target.get(field_name) is not False:
            raise ValueError(f"route review privacy mismatch: {field_name}")


def _value_type(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "unknown"


def _safe_payload_summary(payload: object | None) -> dict[str, Any]:
    top_level_kind = _value_type(payload)
    top_level_keys = sorted(str(key) for key in payload) if isinstance(payload, dict) else []
    guilds = payload.get("guilds") if isinstance(payload, dict) else None
    rows = guilds if isinstance(guilds, list) else []
    objects = [row for row in rows if isinstance(row, dict)]

    field_types: dict[str, set[str]] = {}
    ordered_id_hashes: list[str] = []
    for row in objects:
        for key, value in row.items():
            field_types.setdefault(str(key), set()).add(_value_type(value))
        source_id = row.get("id")
        if isinstance(source_id, (int, str)) and not isinstance(source_id, bool):
            ordered_id_hashes.append(_sha256_json(str(source_id)))

    field_inventory = [
        {"field": key, "types": sorted(types)}
        for key, types in sorted(field_types.items())
    ]
    return {
        "top_level_kind": top_level_kind,
        "top_level_keys": top_level_keys,
        "guild_collection_observed": isinstance(guilds, list),
        "guild_result_count": len(rows),
        "guild_object_count": len(objects),
        "guild_field_inventory": field_inventory,
        "guild_field_inventory_sha256": _sha256_json(field_inventory),
        "ordered_record_set_sha256": _sha256_json(rows),
        "ordered_source_id_hashes_sha256": _sha256_json(ordered_id_hashes),
        "distinct_non_null_id_count": len(set(ordered_id_hashes)),
        "all_records_have_supported_id": len(ordered_id_hashes) == len(objects),
        "contains_source_scalar_values": False,
    }


def _ordered_id_hashes(payload: object | None) -> list[str]:
    guilds = payload.get("guilds") if isinstance(payload, dict) else None
    if not isinstance(guilds, list):
        return []
    result: list[str] = []
    for row in guilds:
        if not isinstance(row, dict):
            return []
        source_id = row.get("id")
        if not isinstance(source_id, (int, str)) or isinstance(source_id, bool):
            return []
        result.append(_sha256_json(str(source_id)))
    return result


def _failure_class(
    return_code: int | None,
    timed_out: bool,
    http_status: int | None,
) -> str | None:
    if timed_out or return_code == 28:
        return "timeout"
    if return_code in {5, 6, 7, 35, 52, 55, 60, 92}:
        return "network_or_tls_failure"
    if return_code in {23, 26, 63}:
        return "response_too_large_or_write_failure"
    if return_code not in {None, 0}:
        return "curl_failure"
    if http_status is not None and not 200 <= http_status <= 299:
        return "http_status_failure"
    return None


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


def _request_url(base_url: str, query: str, limit: int) -> str:
    route_url = urljoin(f"{base_url.rstrip('/')}/", _SEARCH_ROUTE.lstrip("/"))
    return f"{route_url}?{urlencode([('q', query), ('limit', str(limit))])}"


def capture_guild_limit_semantics(
    registry: SourceRegistry,
    archive: RawArchive,
    *,
    route_review_path: Path,
    query: str,
    low_limit: int,
    high_limit: int,
    private_output_path: Path,
    receipt_output_path: Path,
    curl_executable: str | None = None,
    timeout_seconds: float = 60.0,
    max_bytes: int = _DEFAULT_MAX_BYTES,
    runner: RunCommand = subprocess.run,
) -> dict[str, Any]:
    """Capture bounded multi-result evidence without promoting limit semantics."""
    normalized_query = query.strip()
    if not normalized_query or len(normalized_query) > 64:
        raise ValueError("query must contain between 1 and 64 non-space characters")
    if any(ord(character) < 32 for character in normalized_query):
        raise ValueError("query must not contain control characters")
    if low_limit < 1 or high_limit > 100 or low_limit >= high_limit:
        raise ValueError("limits must satisfy 1 <= low_limit < high_limit <= 100")
    if timeout_seconds < 10 or timeout_seconds > 300:
        raise ValueError("timeout_seconds must be between 10 and 300")
    if max_bytes < 64 * 1024 or max_bytes > 1024 * 1024:
        raise ValueError("max_bytes must be between 64 KiB and 1 MiB")

    route_review, route_review_body = _load_object(
        route_review_path,
        "guild route-semantics review",
    )
    _validate_route_review(route_review)

    cases = (
        ("low_limit", low_limit),
        ("high_limit", high_limit),
        ("high_limit_repeat", high_limit),
    )
    executable = _resolve_curl(curl_executable)
    headers = _profile_headers(registry.base_url)
    forbidden_headers = {
        "authorization",
        "cookie",
        "proxy-authorization",
        "x-api-key",
    }
    if any(name.casefold() in forbidden_headers for name, _value in headers):
        raise ValueError("limit semantics profile contains credentials")

    source_parts = urlsplit(registry.base_url)
    private_output_path.parent.mkdir(parents=True, exist_ok=True)
    private_attempts: list[dict[str, Any]] = []
    public_attempts: list[dict[str, Any]] = []
    payloads: dict[str, object | None] = {}

    for case_name, limit in cases:
        request_url = _request_url(registry.base_url, normalized_query, limit)
        target_parts = urlsplit(request_url)
        if target_parts.scheme != "https" or target_parts.hostname != source_parts.hostname:
            raise ValueError("limit semantics request escaped the configured HTTPS host")
        if target_parts.path != _SEARCH_ROUTE:
            raise ValueError("limit semantics request path mismatch")

        temporary_body = private_output_path.with_name(
            f".{private_output_path.stem}.{os.getpid()}.{case_name}.body.part"
        )
        temporary_body.unlink(missing_ok=True)
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
        failure_class = _failure_class(return_code, timed_out, http_status)
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
        payloads[case_name] = payload if json_valid else None

        capture = None
        if body is not None:
            capture = archive.capture_bytes(
                body,
                source_code=registry.source_code,
                endpoint_code=f"guild_limit_semantics_{case_name}",
                request_key=request_key_from_url("GET", request_url),
                fetched_at=datetime.now(timezone.utc),
                http_status=http_status,
                content_type=content_type or "application/octet-stream",
                request_url=request_url,
                metadata={
                    "capture_mode": "bounded_guild_limit_semantics",
                    "case": case_name,
                    "profile": _SELECTED_PROFILE,
                    "query_keys": ["q", "limit"],
                    "redirects_allowed": False,
                    "credentials_supplied": False,
                    "timeout_seconds": timeout_seconds,
                    "max_bytes": max_bytes,
                    "source_route_review_sha256": _sha256_bytes(route_review_body),
                },
            )

        response_candidate = (
            return_code == 0
            and body is not None
            and json_valid
            and http_status is not None
            and 200 <= http_status <= 299
        )
        capture_summary = _capture_summary(capture)
        safe_summary = _safe_payload_summary(payload)

        private_attempts.append(
            {
                "case": case_name,
                "request_url": request_url,
                "query": normalized_query,
                "limit": limit,
                "header_names": [name for name, _value in headers],
                "return_code": return_code,
                "http_status": http_status,
                "content_type": content_type,
                "failure_class": failure_class,
                "stderr": stderr,
                "payload": payload if json_valid else None,
                "body_text": (
                    body.decode("utf-8", errors="replace")
                    if body is not None and not json_valid
                    else None
                ),
                "capture": capture_summary,
                "response_candidate": response_candidate,
            }
        )
        public_attempts.append(
            {
                "case": case_name,
                "route_template": _SEARCH_ROUTE,
                "query_keys": ["q", "limit"],
                "limit": limit,
                "return_code": return_code,
                "http_status": http_status,
                "content_type": content_type,
                "failure_class": failure_class,
                "body_captured": body is not None,
                "body_bytes": len(body) if body is not None else 0,
                "json_valid": json_valid,
                "capture": capture_summary,
                "response_candidate": response_candidate,
                "shape_summary": safe_summary,
                "contains_error_text": False,
                "contains_source_scalar_values": False,
            }
        )
        temporary_body.unlink(missing_ok=True)

    all_completed = all(row["response_candidate"] for row in public_attempts)
    result_counts = {
        str(row["case"]): int(row["shape_summary"]["guild_result_count"])
        for row in public_attempts
        if row["response_candidate"]
    }
    field_hashes = {
        str(row["shape_summary"]["guild_field_inventory_sha256"])
        for row in public_attempts
        if row["response_candidate"]
    }
    schema_consistent = all_completed and len(field_hashes) == 1

    high_rows_hash = next(
        (
            str(row["shape_summary"]["ordered_record_set_sha256"])
            for row in public_attempts
            if row["case"] == "high_limit"
        ),
        "",
    )
    repeat_rows_hash = next(
        (
            str(row["shape_summary"]["ordered_record_set_sha256"])
            for row in public_attempts
            if row["case"] == "high_limit_repeat"
        ),
        "",
    )
    high_repeat_stable = all_completed and high_rows_hash == repeat_rows_hash

    low_ids = _ordered_id_hashes(payloads.get("low_limit"))
    high_ids = _ordered_id_hashes(payloads.get("high_limit"))
    repeat_ids = _ordered_id_hashes(payloads.get("high_limit_repeat"))
    high_id_order_stable = all_completed and high_ids == repeat_ids and bool(high_ids)
    low_is_high_prefix = bool(low_ids) and low_ids == high_ids[: len(low_ids)]
    low_limit_saturated = result_counts.get("low_limit") == low_limit
    multi_result_observed = result_counts.get("high_limit", 0) > low_limit
    high_limit_respected = result_counts.get("high_limit", high_limit + 1) <= high_limit
    limit_truncation_evidence_observed = (
        all_completed
        and schema_consistent
        and high_repeat_stable
        and high_id_order_stable
        and low_is_high_prefix
        and low_limit_saturated
        and multi_result_observed
        and high_limit_respected
    )
    ready_for_review = limit_truncation_evidence_observed

    checks = {
        "route_schema_review_verified": True,
        "request_case_count_bounded": len(public_attempts) == 3,
        "limits_bounded_and_distinct": 1 <= low_limit < high_limit <= 100,
        "reviewed_route_only": all(
            row["route_template"] == _SEARCH_ROUTE for row in public_attempts
        ),
        "requests_same_origin_https": True,
        "redirects_disabled": True,
        "credentials_not_supplied": True,
        "response_size_bounded": all(
            int(row["body_bytes"]) <= max_bytes for row in public_attempts
        ),
        "captured_bodies_archived": all(
            not row["body_captured"] or row["capture"] is not None
            for row in public_attempts
        ),
        "query_value_not_published": True,
        "request_urls_not_published": True,
        "error_text_not_published": True,
        "public_receipt_scalar_boundary_preserved": True,
        "full_crawl_remains_disabled": True,
        "planner_scoring_remains_disabled": True,
    }

    private_payload = {
        "schema_version": 1,
        "capture_kind": _CAPTURE_PRIVATE_KIND,
        "capture_version": _CAPTURE_VERSION,
        "generated_at": _generated_at(),
        "source_route_review_name": route_review_path.name,
        "source_route_review_sha256": _sha256_bytes(route_review_body),
        "query": normalized_query,
        "low_limit": low_limit,
        "high_limit": high_limit,
        "selected_profile": _SELECTED_PROFILE,
        "attempts": private_attempts,
        "summary": {
            "attempt_count": len(private_attempts),
            "all_responses_completed": all_completed,
            "limit_truncation_evidence_observed": limit_truncation_evidence_observed,
            "ready_for_limit_semantics_review": ready_for_review,
            "contains_source_scalar_values": True,
        },
    }
    private_body = _write_json(private_output_path, private_payload)

    status = (
        "guild_limit_semantics_capture_review_ready"
        if ready_for_review
        else "guild_limit_semantics_capture_incomplete"
    )
    receipt = {
        "schema_version": 1,
        "capture_kind": _CAPTURE_KIND,
        "capture_version": _CAPTURE_VERSION,
        "generated_at": _generated_at(),
        "source_route_review_name": route_review_path.name,
        "source_route_review_sha256": _sha256_bytes(route_review_body),
        "source_private_capture_name": private_output_path.name,
        "source_private_capture_sha256": _sha256_bytes(private_body),
        "target": {
            "query_value_published": False,
            "request_urls_published": False,
            "source_guild_ids_published": False,
            "raw_records_published": False,
        },
        "request_contract": {
            "route_template": _SEARCH_ROUTE,
            "query_keys": ["q", "limit"],
            "case_count": len(cases),
            "low_limit": low_limit,
            "high_limit": high_limit,
            "high_limit_repeat_count": 1,
            "selected_profile": _SELECTED_PROFILE,
            "transport": "curl_http1_1",
            "redirects_allowed": False,
            "credentials_supplied": False,
            "timeout_seconds_per_case": timeout_seconds,
            "max_bytes_per_case": max_bytes,
        },
        "attempts": public_attempts,
        "cross_case_evidence": {
            "all_responses_completed": all_completed,
            "response_schema_consistent": schema_consistent,
            "observed_result_counts": sorted(set(result_counts.values())),
            "low_limit_saturated": low_limit_saturated,
            "multi_result_observed": multi_result_observed,
            "high_limit_respected": high_limit_respected,
            "high_limit_repeat_stable": high_repeat_stable,
            "high_limit_source_id_order_stable_by_hash": high_id_order_stable,
            "low_result_is_high_result_prefix_by_id_hash": low_is_high_prefix,
            "limit_truncation_evidence_observed": limit_truncation_evidence_observed,
            "contains_source_scalar_values": False,
        },
        "integrity_checks": checks,
        "decision_boundary": {
            "status": status,
            "guild_route_shape_and_schema_reviewed": True,
            "bounded_limit_semantics_capture_completed": all_completed,
            "multi_result_observed": multi_result_observed,
            "limit_truncation_evidence_observed": limit_truncation_evidence_observed,
            "ready_for_limit_semantics_review": ready_for_review,
            "limit_truncation_semantics_verified": False,
            "pagination_semantics_verified": False,
            "termination_semantics_verified": False,
            "completeness_verified": False,
            "guild_api_route_semantics_verified": False,
            "automatic_full_guild_crawl_allowed": False,
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
            "completed_attempt_count": sum(
                1 for row in public_attempts if row["response_candidate"]
            ),
            "all_responses_completed": all_completed,
            "multi_result_observed": multi_result_observed,
            "limit_truncation_evidence_observed": limit_truncation_evidence_observed,
            "ready_for_limit_semantics_review": ready_for_review,
            "contains_raw_payload": False,
            "contains_source_scalar_values": False,
            "limit_truncation_semantics_verified": False,
            "pagination_semantics_verified": False,
            "termination_semantics_verified": False,
            "completeness_verified": False,
            "guild_api_route_semantics_verified": False,
            "ready_for_full_guild_crawl": False,
            "planner_scoring_allowed": False,
        },
    }
    _write_json(receipt_output_path, receipt)
    return receipt


__all__ = ["capture_guild_limit_semantics"]
