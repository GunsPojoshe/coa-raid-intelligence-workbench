from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit

from .raw_archive import RawArchive, RawCapture, request_key_from_url
from .source_registry import SourceRegistry

_CAPTURE_VERSION = "guild-route-semantics-capture-v1"
_CONTRACT_KIND = "guild_full_crawl_collection_contract"
_CONTRACT_VERSION = "guild-full-crawl-contract-v1"
_ACCESS_KIND = "guild_identity_search_access_diagnostic"
_ACCESS_PRIVATE_KIND = "guild_identity_search_access_diagnostic_private"
_ACCESS_VERSION = "guild-identity-search-access-diagnostic-v1"
_SELECTED_PROFILE = "spa_fetch_context"
_SEARCH_ROUTE = "/api/guilds/search"
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


def _write_json(path: Path, payload: Mapping[str, Any]) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(body)
    temporary.replace(path)
    return body


def _required_object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _required_list(value: object, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")
    return value


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


def _validate_contract(
    receipt: Mapping[str, Any],
    *,
    expected_guild_label: str,
) -> None:
    if receipt.get("schema_version") != 1:
        raise ValueError("full-crawl contract schema mismatch")
    if receipt.get("contract_kind") != _CONTRACT_KIND:
        raise ValueError("full-crawl contract kind mismatch")
    if receipt.get("contract_version") != _CONTRACT_VERSION:
        raise ValueError("full-crawl contract version mismatch")

    target = _required_object(receipt.get("target"), "full-crawl contract target")
    if target.get("guild_label") != expected_guild_label:
        raise ValueError("full-crawl contract guild label mismatch")
    if target.get("source_guild_id_published") is not False:
        raise ValueError("full-crawl contract publishes source guild ID")
    if target.get("report_ids_published") is not False:
        raise ValueError("full-crawl contract publishes report IDs")

    summary = _required_object(receipt.get("summary"), "full-crawl contract summary")
    if summary.get("all_integrity_checks_passed") is not True:
        raise ValueError("full-crawl contract integrity checks failed")
    if summary.get("contains_source_scalar_values") is not False:
        raise ValueError("full-crawl contract contains source scalar values")
    if summary.get("full_crawl_collection_contract_reviewed") is not True:
        raise ValueError("full-crawl contract is not reviewed")
    if summary.get("ready_for_bounded_route_semantics_capture") is not True:
        raise ValueError("full-crawl contract does not allow bounded capture")
    if summary.get("guild_api_route_semantics_verified") is not False:
        raise ValueError("full-crawl contract overclaims route semantics")
    if summary.get("ready_for_full_guild_crawl") is not False:
        raise ValueError("full-crawl contract enables full crawl")
    if summary.get("planner_scoring_allowed") is not False:
        raise ValueError("full-crawl contract enables planner scoring")

    boundary = _required_object(
        receipt.get("decision_boundary"),
        "full-crawl contract decision boundary",
    )
    if boundary.get("full_crawl_collection_contract_reviewed") is not True:
        raise ValueError("full-crawl contract boundary is not reviewed")
    if boundary.get("ready_for_bounded_route_semantics_capture") is not True:
        raise ValueError("full-crawl contract boundary blocks bounded capture")
    for field_name in (
        "guild_api_route_semantics_verified",
        "automatic_full_guild_crawl_allowed",
        "ready_for_full_guild_crawl",
        "ready_for_multi_report_character_graph",
        "ready_for_performance_model",
        "ready_for_bis25_scoring",
        "planner_scoring_allowed",
    ):
        if boundary.get(field_name) is not False:
            raise ValueError(f"full-crawl contract boundary mismatch: {field_name}")


def _selected_attempt(attempts: list[Any]) -> dict[str, Any]:
    matches = [
        _required_object(value, "private access attempt")
        for value in attempts
        if isinstance(value, dict) and value.get("profile") == _SELECTED_PROFILE
    ]
    if len(matches) != 1:
        raise ValueError("private access diagnostic must contain one selected profile")
    return matches[0]


def _validate_access_diagnostic(
    public: Mapping[str, Any],
    private: Mapping[str, Any],
    *,
    private_body: bytes,
    expected_guild_label: str,
    registry: SourceRegistry,
) -> tuple[str, int]:
    if public.get("schema_version") != 1:
        raise ValueError("public access diagnostic schema mismatch")
    if public.get("diagnostic_kind") != _ACCESS_KIND:
        raise ValueError("public access diagnostic kind mismatch")
    if public.get("diagnostic_version") != _ACCESS_VERSION:
        raise ValueError("public access diagnostic version mismatch")

    target = _required_object(public.get("target"), "public access target")
    if target.get("guild_label") != expected_guild_label:
        raise ValueError("public access diagnostic guild label mismatch")
    if target.get("request_url_published") is not False:
        raise ValueError("public access diagnostic publishes request URL")
    if target.get("source_guild_id_published") is not False:
        raise ValueError("public access diagnostic publishes source guild ID")

    summary = _required_object(public.get("summary"), "public access summary")
    if summary.get("all_integrity_checks_passed") is not True:
        raise ValueError("public access diagnostic integrity checks failed")
    if summary.get("selected_access_profile") != _SELECTED_PROFILE:
        raise ValueError("public access diagnostic selected profile mismatch")
    if summary.get("contains_source_scalar_values") is not False:
        raise ValueError("public access diagnostic contains source scalar values")

    boundary = _required_object(
        public.get("decision_boundary"),
        "public access decision boundary",
    )
    if boundary.get("ready_for_profiled_guild_search_probe") is not True:
        raise ValueError("public access diagnostic is not ready for profiled capture")
    if boundary.get("selected_access_profile") != _SELECTED_PROFILE:
        raise ValueError("public access diagnostic boundary profile mismatch")
    for field_name in (
        "guild_api_route_semantics_verified",
        "ready_for_full_guild_crawl",
        "planner_scoring_allowed",
    ):
        if boundary.get(field_name) is not False:
            raise ValueError(f"public access diagnostic boundary mismatch: {field_name}")

    expected_private_hash = public.get("source_private_diagnostic_sha256")
    if not isinstance(expected_private_hash, str) or len(expected_private_hash) != 64:
        raise ValueError("public access diagnostic private SHA-256 is missing")
    if _sha256_bytes(private_body) != expected_private_hash:
        raise ValueError("private access diagnostic SHA-256 mismatch")

    if private.get("schema_version") != 1:
        raise ValueError("private access diagnostic schema mismatch")
    if private.get("diagnostic_kind") != _ACCESS_PRIVATE_KIND:
        raise ValueError("private access diagnostic kind mismatch")
    if private.get("diagnostic_version") != _ACCESS_VERSION:
        raise ValueError("private access diagnostic version mismatch")
    if private.get("target_guild_label") != expected_guild_label:
        raise ValueError("private access diagnostic guild label mismatch")
    if private.get("selected_profile") != _SELECTED_PROFILE:
        raise ValueError("private access diagnostic selected profile mismatch")

    attempt = _selected_attempt(
        _required_list(private.get("attempts"), "private access attempts")
    )
    if attempt.get("return_code") != 0:
        raise ValueError("selected access attempt return code mismatch")
    if attempt.get("http_status") != 200:
        raise ValueError("selected access attempt HTTP status mismatch")
    if attempt.get("response_candidate") is not True:
        raise ValueError("selected access attempt is not a response candidate")
    if not isinstance(attempt.get("body"), dict):
        raise ValueError("selected access attempt body must be a JSON object")

    request_url = private.get("request_url")
    if not isinstance(request_url, str) or not request_url:
        raise ValueError("private access diagnostic request URL is missing")
    source_parts = urlsplit(registry.base_url)
    target_parts = urlsplit(request_url)
    if target_parts.scheme != "https" or target_parts.hostname != source_parts.hostname:
        raise ValueError("private access diagnostic escaped the configured HTTPS host")
    if target_parts.path != _SEARCH_ROUTE:
        raise ValueError("private access diagnostic route mismatch")

    query = dict(parse_qsl(target_parts.query, keep_blank_values=True))
    if sorted(query) != ["limit", "q"]:
        raise ValueError("private access diagnostic query keys changed")
    if query.get("q") != expected_guild_label:
        raise ValueError("private access diagnostic query label mismatch")
    limit_text = query.get("limit", "")
    if not limit_text.isdigit() or int(limit_text) != 25:
        raise ValueError("private access diagnostic reviewed limit mismatch")
    return query["q"], int(limit_text)


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


def _safe_payload_summary(
    payload: object | None,
    *,
    expected_guild_label: str,
) -> dict[str, Any]:
    top_level_kind = _value_type(payload)
    top_level_keys = sorted(str(key) for key in payload) if isinstance(payload, dict) else []
    guilds = payload.get("guilds") if isinstance(payload, dict) else None
    collection_observed = isinstance(guilds, list)
    rows = guilds if isinstance(guilds, list) else []
    objects = [row for row in rows if isinstance(row, dict)]

    field_types: dict[str, set[str]] = {}
    exact_label_count = 0
    id_values: list[str] = []
    for row in objects:
        for key, value in row.items():
            field_types.setdefault(str(key), set()).add(_value_type(value))
        if row.get("name") == expected_guild_label:
            exact_label_count += 1
        value = row.get("id")
        if isinstance(value, (int, str)) and not isinstance(value, bool):
            id_values.append(str(value))

    field_inventory = [
        {"field": key, "types": sorted(types)}
        for key, types in sorted(field_types.items())
    ]
    id_hashes = sorted({_sha256_json(value) for value in id_values})
    pagination = payload.get("pagination") if isinstance(payload, dict) else None
    pagination_observed = isinstance(pagination, dict)
    pagination_keys = sorted(str(key) for key in pagination) if pagination_observed else []
    pagination_field_types = (
        [
            {"field": str(key), "type": _value_type(value)}
            for key, value in sorted(pagination.items())
        ]
        if isinstance(pagination, dict)
        else []
    )

    return {
        "top_level_kind": top_level_kind,
        "top_level_keys": top_level_keys,
        "guild_collection_observed": collection_observed,
        "guild_result_count": len(rows),
        "guild_object_count": len(objects),
        "guild_field_inventory": field_inventory,
        "guild_field_inventory_sha256": _sha256_json(field_inventory),
        "exact_label_match_count": exact_label_count,
        "distinct_non_null_id_count": len(id_hashes),
        "id_value_set_sha256": _sha256_json(id_hashes),
        "ordered_guild_records_sha256": _sha256_json(rows),
        "pagination_object_observed": pagination_observed,
        "pagination_keys": pagination_keys,
        "pagination_field_types": pagination_field_types,
        "contains_source_scalar_values": False,
    }


def _case_url(base_url: str, label: str, limit: int | None) -> str:
    pairs: list[tuple[str, str]] = [("q", label)]
    if limit is not None:
        pairs.append(("limit", str(limit)))
    route_url = urljoin(f"{base_url.rstrip('/')}/", _SEARCH_ROUTE.lstrip("/"))
    return f"{route_url}?{urlencode(pairs)}"


def capture_guild_route_semantics(
    registry: SourceRegistry,
    archive: RawArchive,
    *,
    full_crawl_contract_path: Path,
    public_access_diagnostic_path: Path,
    private_access_diagnostic_path: Path,
    private_output_path: Path,
    receipt_output_path: Path,
    expected_guild_label: str = "Argentum",
    curl_executable: str | None = None,
    timeout_seconds: float = 60.0,
    max_bytes: int = _DEFAULT_MAX_BYTES,
    runner: RunCommand = subprocess.run,
) -> dict[str, Any]:
    """Capture three bounded search-route variants without promoting semantics."""
    if timeout_seconds < 10 or timeout_seconds > 300:
        raise ValueError("timeout_seconds must be between 10 and 300")
    if max_bytes < 64 * 1024 or max_bytes > 1024 * 1024:
        raise ValueError("max_bytes must be between 64 KiB and 1 MiB")

    contract, contract_body = _load_object(
        full_crawl_contract_path,
        "full-crawl collection contract",
    )
    public_access, public_access_body = _load_object(
        public_access_diagnostic_path,
        "public access diagnostic",
    )
    private_access, private_access_body = _load_object(
        private_access_diagnostic_path,
        "private access diagnostic",
    )
    _validate_contract(contract, expected_guild_label=expected_guild_label)
    query_label, reviewed_limit = _validate_access_diagnostic(
        public_access,
        private_access,
        private_body=private_access_body,
        expected_guild_label=expected_guild_label,
        registry=registry,
    )

    cases = (
        ("exact_label_limit_1", 1),
        ("exact_label_limit_reviewed", reviewed_limit),
        ("exact_label_without_limit", None),
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
        raise ValueError("route semantics profile contains credentials")

    private_output_path.parent.mkdir(parents=True, exist_ok=True)
    private_attempts: list[dict[str, Any]] = []
    public_attempts: list[dict[str, Any]] = []

    for case_name, limit in cases:
        request_url = _case_url(registry.base_url, query_label, limit)
        target_parts = urlsplit(request_url)
        source_parts = urlsplit(registry.base_url)
        if target_parts.scheme != "https" or target_parts.hostname != source_parts.hostname:
            raise ValueError("route semantics request escaped the configured HTTPS host")
        if target_parts.path != _SEARCH_ROUTE:
            raise ValueError("route semantics request path mismatch")

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
                endpoint_code="guild_route_semantics_capture",
                request_key=request_key_from_url("GET", request_url),
                fetched_at=datetime.now(timezone.utc),
                http_status=http_status,
                content_type=content_type or "application/octet-stream",
                request_url=request_url,
                metadata={
                    "capture_mode": "bounded_guild_route_semantics",
                    "case": case_name,
                    "profile": _SELECTED_PROFILE,
                    "query_keys": ["q", "limit"] if limit is not None else ["q"],
                    "redirects_allowed": False,
                    "credentials_supplied": False,
                    "timeout_seconds": timeout_seconds,
                    "max_bytes": max_bytes,
                    "source_contract_sha256": _sha256_bytes(contract_body),
                    "source_public_access_sha256": _sha256_bytes(public_access_body),
                    "source_private_access_sha256": _sha256_bytes(private_access_body),
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
        safe_summary = _safe_payload_summary(
            payload,
            expected_guild_label=expected_guild_label,
        )
        query_keys = ["q", "limit"] if limit is not None else ["q"]

        private_attempts.append(
            {
                "case": case_name,
                "request_url": request_url,
                "query_label": query_label,
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
                "query_keys": query_keys,
                "query_value_published": False,
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
    shape_hashes = {
        _sha256_json(
            {
                "top_level_kind": row["shape_summary"]["top_level_kind"],
                "top_level_keys": row["shape_summary"]["top_level_keys"],
                "guild_field_inventory": row["shape_summary"]["guild_field_inventory"],
            }
        )
        for row in public_attempts
        if row["response_candidate"]
    }
    shape_consistent = all_completed and len(shape_hashes) == 1
    collection_observed = all(
        row["shape_summary"]["guild_collection_observed"]
        for row in public_attempts
    )
    exact_label_counts = {
        int(row["shape_summary"]["exact_label_match_count"])
        for row in public_attempts
        if row["response_candidate"]
    }
    exact_label_stable = all_completed and exact_label_counts == {1}
    id_set_hashes = {
        str(row["shape_summary"]["id_value_set_sha256"])
        for row in public_attempts
        if row["response_candidate"]
    }
    id_set_stable = all_completed and len(id_set_hashes) == 1
    result_counts = {
        str(row["case"]): int(row["shape_summary"]["guild_result_count"])
        for row in public_attempts
        if row["response_candidate"]
    }
    limit_truncation_verified = (
        all_completed
        and result_counts.get("exact_label_limit_1", 0)
        < result_counts.get("exact_label_limit_reviewed", 0)
    )
    pagination_observed = any(
        row["shape_summary"]["pagination_object_observed"]
        for row in public_attempts
    )
    route_shapes_observed = (
        all_completed
        and {tuple(row["query_keys"]) for row in public_attempts}
        == {("q",), ("q", "limit")}
    )
    ready_for_review = (
        all_completed
        and route_shapes_observed
        and shape_consistent
        and collection_observed
        and exact_label_stable
        and id_set_stable
    )

    checks = {
        "full_crawl_contract_verified": True,
        "public_access_diagnostic_verified": True,
        "private_access_diagnostic_sha256_verified": True,
        "selected_spa_fetch_profile_verified": True,
        "request_case_count_bounded": len(public_attempts) == 3,
        "observed_route_shapes_only": route_shapes_observed,
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
        "public_receipt_scalar_boundary_preserved": True,
        "error_text_not_published": True,
    }

    private_payload = {
        "schema_version": 1,
        "capture_kind": "guild_route_semantics_capture_private",
        "capture_version": _CAPTURE_VERSION,
        "generated_at": _generated_at(),
        "source_contract_name": full_crawl_contract_path.name,
        "source_contract_sha256": _sha256_bytes(contract_body),
        "source_public_access_name": public_access_diagnostic_path.name,
        "source_public_access_sha256": _sha256_bytes(public_access_body),
        "source_private_access_name": private_access_diagnostic_path.name,
        "source_private_access_sha256": _sha256_bytes(private_access_body),
        "target_guild_label": expected_guild_label,
        "selected_profile": _SELECTED_PROFILE,
        "attempts": private_attempts,
        "summary": {
            "attempt_count": len(private_attempts),
            "all_responses_completed": all_completed,
            "ready_for_route_semantics_review": ready_for_review,
            "contains_source_scalar_values": True,
        },
    }
    private_body = _write_json(private_output_path, private_payload)

    status = (
        "guild_route_semantics_capture_review_ready"
        if ready_for_review
        else "guild_route_semantics_capture_incomplete"
    )
    receipt = {
        "schema_version": 1,
        "capture_kind": "guild_route_semantics_capture",
        "capture_version": _CAPTURE_VERSION,
        "generated_at": _generated_at(),
        "source_contract_name": full_crawl_contract_path.name,
        "source_contract_sha256": _sha256_bytes(contract_body),
        "source_public_access_name": public_access_diagnostic_path.name,
        "source_public_access_sha256": _sha256_bytes(public_access_body),
        "source_private_capture_name": private_output_path.name,
        "source_private_capture_sha256": _sha256_bytes(private_body),
        "target": {
            "guild_label": expected_guild_label,
            "query_values_published": False,
            "source_guild_id_published": False,
            "report_ids_published": False,
        },
        "request_contract": {
            "route_template": _SEARCH_ROUTE,
            "observed_query_shapes": [
                ["q", "limit"],
                ["q"],
            ],
            "case_count": len(cases),
            "selected_profile": _SELECTED_PROFILE,
            "transport": "curl_http1_1",
            "redirects_allowed": False,
            "credentials_supplied": False,
            "timeout_seconds_per_case": timeout_seconds,
            "max_bytes_per_case": max_bytes,
        },
        "attempts": public_attempts,
        "cross_case_review": {
            "all_responses_completed": all_completed,
            "route_shapes_observed": route_shapes_observed,
            "response_shape_consistent": shape_consistent,
            "guild_collection_observed_on_all_cases": collection_observed,
            "exact_label_result_stable": exact_label_stable,
            "source_id_set_stable_by_hash": id_set_stable,
            "limit_parameter_accepted": all_completed,
            "limit_truncation_semantics_verified": limit_truncation_verified,
            "pagination_object_observed": pagination_observed,
            "pagination_semantics_verified": False,
            "contains_source_scalar_values": False,
        },
        "integrity_checks": checks,
        "decision_boundary": {
            "status": status,
            "full_crawl_collection_contract_reviewed": True,
            "bounded_route_semantics_capture_completed": all_completed,
            "route_shapes_observed": route_shapes_observed,
            "route_response_schema_review_ready": ready_for_review,
            "limit_parameter_accepted": all_completed,
            "limit_truncation_semantics_verified": limit_truncation_verified,
            "pagination_object_observed": pagination_observed,
            "pagination_semantics_verified": False,
            "guild_api_route_semantics_verified": False,
            "ready_for_route_semantics_review": ready_for_review,
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
            "response_shape_consistent": shape_consistent,
            "ready_for_route_semantics_review": ready_for_review,
            "contains_raw_payload": False,
            "contains_source_scalar_values": False,
            "guild_api_route_semantics_verified": False,
            "ready_for_full_guild_crawl": False,
            "planner_scoring_allowed": False,
        },
    }
    _write_json(receipt_output_path, receipt)
    return receipt


__all__ = ["capture_guild_route_semantics"]
