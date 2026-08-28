from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping, Sequence
from urllib.parse import urlencode, urljoin, urlsplit

from .raw_archive import RawArchive, request_key_from_url, sanitize_url
from .source_registry import SourceRegistry

_PROBE_VERSION = "guild-identity-search-probe-v1"
_PROFILED_RECOVERY_VERSION = "guild-identity-asset-profiled-recovery-v1"
_PUBLIC_RECOVERY_KIND = "guild_identity_asset_profiled_recovery"
_PRIVATE_RECOVERY_KIND = "guild_identity_asset_profiled_recovery_private"
_SEARCH_ROUTE = "/api/guilds/search"
_SEARCH_ROUTE_SHAPE = "/api/guilds/search?q=<value>&limit=<value>"
_DEFAULT_LIMIT = 25
_DEFAULT_MAX_BYTES = 2 * 1024 * 1024

RunCommand = Callable[..., Any]


def _generated_at() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_json(value: object) -> str:
    return _sha256_bytes(_canonical_json(value).encode("utf-8"))


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
        raise ValueError(f"guild search probe field {field_name} must be an object")
    return value


def _required_list(value: object, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"guild search probe field {field_name} must be a list")
    return value


def _candidate_scalar(value: object, field_name: str) -> int | str:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError(f"guild search probe field {field_name} must be an integer or string")
    prepared = str(value).strip()
    if not prepared or len(prepared) > 160:
        raise ValueError(f"guild search probe field {field_name} is empty or too long")
    return value


def _resolve_curl(executable: str | None) -> str:
    if executable:
        return executable
    for candidate in ("curl.exe", "curl"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    raise ValueError("curl executable was not found")


def _validate_recovery(
    public: Mapping[str, Any],
    private: Mapping[str, Any],
    *,
    private_body: bytes,
    expected_guild_label: str,
) -> int | str:
    if public.get("schema_version") != 1:
        raise ValueError("public profiled recovery schema mismatch")
    if public.get("recovery_kind") != _PUBLIC_RECOVERY_KIND:
        raise ValueError("public profiled recovery kind mismatch")
    if public.get("recovery_version") != _PROFILED_RECOVERY_VERSION:
        raise ValueError("public profiled recovery version mismatch")

    target = _required_object(public.get("target"), "public.target")
    if target.get("guild_label") != expected_guild_label:
        raise ValueError("public profiled recovery guild label mismatch")
    if target.get("source_guild_id_published") is not False:
        raise ValueError("public profiled recovery publishes source guild ID")
    if target.get("asset_url_published") is not False:
        raise ValueError("public profiled recovery publishes asset URL")

    summary = _required_object(public.get("summary"), "public.summary")
    if summary.get("all_integrity_checks_passed") is not True:
        raise ValueError("public profiled recovery integrity checks did not pass")
    if summary.get("contains_source_scalar_values") is not False:
        raise ValueError("public profiled recovery is not scalar-free")
    if summary.get("asset_download_completed") is not True:
        raise ValueError("public profiled recovery did not complete the asset download")

    inventory = _required_object(public.get("route_inventory"), "public.route_inventory")
    shapes = [str(value) for value in _required_list(inventory.get("guild_api_route_shapes"), "public.route_inventory.guild_api_route_shapes")]
    if _SEARCH_ROUTE_SHAPE not in shapes:
        raise ValueError("bounded guild search route shape was not recovered")

    boundary = _required_object(public.get("decision_boundary"), "public.decision_boundary")
    if boundary.get("guild_api_route_candidates_observed") is not True:
        raise ValueError("guild route candidates were not observed")
    if boundary.get("ready_for_guild_api_route_review") is not True:
        raise ValueError("public profiled recovery is not ready for route review")
    for field_name in (
        "guild_api_route_semantics_verified",
        "independent_source_identity_verified",
        "guild_identity_verified",
        "ready_for_guild_filtering",
        "ready_for_full_guild_crawl",
        "planner_scoring_allowed",
    ):
        if boundary.get(field_name) is not False:
            raise ValueError(f"public profiled recovery boundary mismatch: {field_name}")

    expected_private_hash = public.get("source_private_recovery_sha256")
    if not isinstance(expected_private_hash, str) or len(expected_private_hash) != 64:
        raise ValueError("public profiled recovery private SHA-256 is missing")
    if _sha256_bytes(private_body) != expected_private_hash:
        raise ValueError("private profiled recovery SHA-256 mismatch")

    if private.get("schema_version") != 1:
        raise ValueError("private profiled recovery schema mismatch")
    if private.get("recovery_kind") != _PRIVATE_RECOVERY_KIND:
        raise ValueError("private profiled recovery kind mismatch")
    if private.get("recovery_version") != _PROFILED_RECOVERY_VERSION:
        raise ValueError("private profiled recovery version mismatch")
    if private.get("target_guild_label") != expected_guild_label:
        raise ValueError("private profiled recovery guild label mismatch")
    if private.get("selected_transport_profile") != "http1_1":
        raise ValueError("private profiled recovery transport profile mismatch")
    return _candidate_scalar(private.get("candidate_source_guild_id"), "candidate_source_guild_id")


def _is_scalar(value: object) -> bool:
    return value is None or isinstance(value, (bool, int, float, str))


def _walk_objects(value: object, path: str = "$") -> Iterator[tuple[str, dict[str, Any]]]:
    if isinstance(value, dict):
        yield path, value
        for key in sorted(value):
            yield from _walk_objects(value[key], f"{path}.{key}")
    elif isinstance(value, list):
        for child in value:
            yield from _walk_objects(child, f"{path}[]")


def _id_like(field_name: str) -> bool:
    normalized = "".join(char for char in field_name.casefold() if char.isalnum())
    return normalized in {"id", "guildid"}


def _matched_rows(
    payload: object,
    *,
    expected_guild_label: str,
    source_guild_id: int | str,
) -> list[dict[str, Any]]:
    source_text = str(source_guild_id)
    rows: list[dict[str, Any]] = []
    for object_path, candidate in _walk_objects(payload):
        scalars = {str(key): value for key, value in candidate.items() if _is_scalar(value)}
        label_fields = sorted(
            key for key, value in scalars.items() if isinstance(value, str) and value == expected_guild_label
        )
        if not label_fields:
            continue
        id_like_fields = sorted(key for key in scalars if _id_like(key))
        id_values = {key: scalars[key] for key in id_like_fields}
        matching_id_fields = sorted(
            key for key, value in id_values.items() if value is not None and str(value) == source_text
        )
        rows.append(
            {
                "object_path": object_path,
                "label_fields": label_fields,
                "scalar_fields": scalars,
                "id_like_fields": id_like_fields,
                "id_like_values": id_values,
                "matching_source_id_fields": matching_id_fields,
            }
        )
    return rows


def _safe_match_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    object_paths = sorted({str(row["object_path"]) for row in rows})
    label_fields = sorted({field for row in rows for field in row["label_fields"]})
    id_like_fields = sorted({field for row in rows for field in row["id_like_fields"]})
    matching_rows = [row for row in rows if row["matching_source_id_fields"]]
    id_values = [
        value
        for row in rows
        for value in row["id_like_values"].values()
        if value is not None
    ]
    id_value_hashes = sorted({_sha256_json(str(value)) for value in id_values})
    one_to_one = (
        len(rows) == 1
        and len(matching_rows) == 1
        and len(id_values) == 1
        and len(id_value_hashes) == 1
    )
    return {
        "exact_label_object_count": len(rows),
        "distinct_object_path_count": len(object_paths),
        "object_paths": object_paths,
        "exact_label_field_names": label_fields,
        "id_like_field_names": id_like_fields,
        "id_like_value_count": len(id_values),
        "distinct_id_like_value_count": len(id_value_hashes),
        "id_like_value_set_sha256": _sha256_json(id_value_hashes),
        "source_id_match_object_count": len(matching_rows),
        "exact_label_and_source_id_cooccur": bool(matching_rows),
        "one_to_one_identity_candidate": one_to_one,
        "contains_source_scalar_values": False,
    }


def capture_guild_identity_search_probe(
    registry: SourceRegistry,
    archive: RawArchive,
    *,
    public_profiled_recovery_path: Path,
    private_profiled_recovery_path: Path,
    private_output_path: Path,
    receipt_output_path: Path,
    expected_guild_label: str = "Argentum",
    limit: int = _DEFAULT_LIMIT,
    curl_executable: str | None = None,
    timeout_seconds: float = 60.0,
    max_bytes: int = _DEFAULT_MAX_BYTES,
    runner: RunCommand = subprocess.run,
) -> dict[str, Any]:
    """Capture one bounded guild search response without promoting route or identity semantics."""
    if limit < 1 or limit > 50:
        raise ValueError("guild search limit must be between 1 and 50")
    if timeout_seconds < 10 or timeout_seconds > 300:
        raise ValueError("timeout_seconds must be between 10 and 300")
    if max_bytes < 64 * 1024 or max_bytes > 8 * 1024 * 1024:
        raise ValueError("max_bytes must be between 64 KiB and 8 MiB")

    public_recovery, public_recovery_body = _load_object(
        public_profiled_recovery_path, "public profiled recovery"
    )
    private_recovery, private_recovery_body = _load_object(
        private_profiled_recovery_path, "private profiled recovery"
    )
    source_guild_id = _validate_recovery(
        public_recovery,
        private_recovery,
        private_body=private_recovery_body,
        expected_guild_label=expected_guild_label,
    )

    query = urlencode((("q", expected_guild_label), ("limit", str(limit))))
    url = urljoin(f"{registry.base_url.rstrip('/')}/", _SEARCH_ROUTE.lstrip("/"))
    url = f"{url}?{query}"
    source_parts = urlsplit(registry.base_url)
    target_parts = urlsplit(url)
    if target_parts.scheme != "https" or target_parts.hostname != source_parts.hostname:
        raise ValueError("guild search probe escaped the configured HTTPS source host")

    executable = _resolve_curl(curl_executable)
    private_output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_body = private_output_path.with_name(f".{private_output_path.stem}.{os.getpid()}.body.part")
    temporary_body.unlink(missing_ok=True)
    try:
        command: Sequence[str] = (
            executable,
            "--silent",
            "--show-error",
            "--fail",
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
            "1",
            "--retry-delay",
            "2",
            "--retry-all-errors",
            "--max-filesize",
            str(max_bytes),
            "--header",
            "Accept: application/json, text/plain, */*",
            "--user-agent",
            "CoA-Raid-Intelligence-Workbench/0.1 guild-search-probe",
            "--output",
            str(temporary_body),
            "--write-out",
            "%{http_code}\n%{content_type}",
            url,
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
            stdout_lines = str(completed.stdout or "").strip().splitlines()
        except subprocess.TimeoutExpired:
            process_timed_out = True
            return_code = None
            stdout_lines = []

        http_status = int(stdout_lines[0]) if stdout_lines and stdout_lines[0].isdigit() else None
        content_type = stdout_lines[1].strip() if len(stdout_lines) > 1 else None
        body = temporary_body.read_bytes() if return_code == 0 and temporary_body.is_file() else None
        failure_class: str | None = None
        if process_timed_out or return_code == 28:
            failure_class = "timeout"
        elif return_code in {5, 6, 7, 35, 52, 55, 60, 92}:
            failure_class = "network_or_tls_failure"
        elif return_code in {22}:
            failure_class = "http_status_failure"
        elif return_code in {23, 26, 63}:
            failure_class = "response_too_large_or_write_failure"
        elif return_code not in {None, 0}:
            failure_class = "curl_failure"
        if body is not None and not body:
            body = None
            failure_class = "empty_response"
        if body is not None and len(body) > max_bytes:
            body = None
            failure_class = "response_too_large_or_write_failure"
        if body is None and failure_class is None:
            failure_class = "missing_response"

        capture = None
        payload: object | None = None
        json_error = False
        if body is not None:
            capture = archive.capture_bytes(
                body,
                source_code=registry.source_code,
                endpoint_code="guild_identity_search_probe",
                request_key=request_key_from_url("GET", url),
                fetched_at=datetime.now(timezone.utc),
                http_status=http_status,
                content_type=content_type or "application/json",
                request_url=url,
                metadata={
                    "capture_mode": "bounded_guild_identity_search_probe",
                    "route_template": _SEARCH_ROUTE,
                    "query_keys": ["q", "limit"],
                    "search_limit": limit,
                    "transport_profile": "http1_1",
                    "redirects_allowed": False,
                    "credentials_supplied": False,
                    "source_public_profiled_recovery_sha256": _sha256_bytes(public_recovery_body),
                    "source_private_profiled_recovery_sha256": _sha256_bytes(private_recovery_body),
                },
            )
            try:
                payload = json.loads(body)
            except (UnicodeDecodeError, json.JSONDecodeError):
                json_error = True

        rows = (
            _matched_rows(
                payload,
                expected_guild_label=expected_guild_label,
                source_guild_id=source_guild_id,
            )
            if payload is not None
            else []
        )
        safe_matches = _safe_match_summary(rows)
        response_completed = (
            body is not None
            and capture is not None
            and not json_error
            and http_status is not None
            and 200 <= http_status <= 299
        )
        route_semantics_candidate = response_completed and bool(rows)
        identity_candidate = route_semantics_candidate and bool(
            safe_matches["one_to_one_identity_candidate"]
        )

        checks = {
            "public_profiled_recovery_verified": True,
            "private_profiled_recovery_sha256_verified": True,
            "guild_search_route_candidate_verified": True,
            "request_url_https": target_parts.scheme == "https",
            "request_url_same_origin": target_parts.hostname == source_parts.hostname,
            "http1_1_profile_selected": True,
            "redirects_disabled": True,
            "credentials_not_supplied": True,
            "download_size_bounded": body is None or len(body) <= max_bytes,
            "public_receipt_scalar_boundary_preserved": True,
            "source_guild_id_not_published": True,
            "error_text_not_published": True,
        }

        private_payload = {
            "schema_version": 1,
            "probe_kind": "guild_identity_search_probe_private",
            "probe_version": _PROBE_VERSION,
            "generated_at": _generated_at(),
            "source_public_profiled_recovery_name": public_profiled_recovery_path.name,
            "source_public_profiled_recovery_sha256": _sha256_bytes(public_recovery_body),
            "source_private_profiled_recovery_name": private_profiled_recovery_path.name,
            "source_private_profiled_recovery_sha256": _sha256_bytes(private_recovery_body),
            "target_guild_label": expected_guild_label,
            "candidate_source_guild_id": source_guild_id,
            "request_url": url,
            "request_limit": limit,
            "transport": {
                "profile": "http1_1",
                "return_code": return_code,
                "http_status": http_status,
                "content_type": content_type,
                "failure_class": failure_class,
                "timeout_seconds": timeout_seconds,
                "max_bytes": max_bytes,
            },
            "capture": (
                {
                    "raw_id": capture.raw_id,
                    "observation_id": capture.observation_id,
                    "payload_hash": capture.payload_hash,
                    "schema_fingerprint": capture.schema_fingerprint,
                    "bytes_uncompressed": capture.bytes_uncompressed,
                }
                if capture is not None
                else None
            ),
            "matched_objects": rows,
            "summary": {
                "response_completed": response_completed,
                "json_error": json_error,
                "exact_label_object_count": len(rows),
                "contains_source_scalar_values": True,
            },
        }
        private_body = _write_json(private_output_path, private_payload)

        receipt = {
            "schema_version": 1,
            "probe_kind": "guild_identity_search_probe",
            "probe_version": _PROBE_VERSION,
            "generated_at": _generated_at(),
            "source_public_profiled_recovery_name": public_profiled_recovery_path.name,
            "source_public_profiled_recovery_sha256": _sha256_bytes(public_recovery_body),
            "source_private_probe_name": private_output_path.name,
            "source_private_probe_sha256": _sha256_bytes(private_body),
            "target": {
                "guild_label": expected_guild_label,
                "source_guild_id_published": False,
                "request_url_published": False,
            },
            "request": {
                "route_template": _SEARCH_ROUTE,
                "route_shape": _SEARCH_ROUTE_SHAPE,
                "sanitized_route": sanitize_url(url),
                "query_keys": ["q", "limit"],
                "limit": limit,
                "transport_profile": "http1_1",
                "redirects_allowed": False,
                "credentials_supplied": False,
            },
            "response": {
                "completed": response_completed,
                "http_status": http_status,
                "content_type": content_type,
                "failure_class": failure_class,
                "capture": (
                    {
                        "raw_id": capture.raw_id,
                        "observation_id": capture.observation_id,
                        "payload_hash": capture.payload_hash,
                        "schema_fingerprint": capture.schema_fingerprint,
                        "bytes_uncompressed": capture.bytes_uncompressed,
                    }
                    if capture is not None
                    else None
                ),
                "json_valid": payload is not None,
            },
            "match_review": safe_matches,
            "integrity_checks": checks,
            "decision_boundary": {
                "status": (
                    "independent_identity_candidate_observed"
                    if identity_candidate
                    else "guild_search_route_response_captured"
                    if response_completed
                    else "guild_search_probe_incomplete"
                ),
                "guild_api_route_candidates_observed": True,
                "guild_search_route_response_captured": response_completed,
                "guild_search_route_semantics_candidate_observed": route_semantics_candidate,
                "independent_source_identity_candidate_observed": identity_candidate,
                "guild_api_route_semantics_verified": False,
                "independent_source_identity_verified": False,
                "guild_identity_verified": False,
                "ready_for_guild_search_mapping_review": route_semantics_candidate,
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
                "response_completed": response_completed,
                "exact_label_object_count": len(rows),
                "source_id_match_object_count": safe_matches["source_id_match_object_count"],
                "one_to_one_identity_candidate": identity_candidate,
                "contains_source_scalar_values": False,
                "contains_error_text": False,
            },
        }
        _write_json(receipt_output_path, receipt)
        return receipt
    finally:
        temporary_body.unlink(missing_ok=True)


__all__ = ["capture_guild_identity_search_probe"]
