from __future__ import annotations

import gzip
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping

_REVIEW_VERSION = "guild-identity-search-capture-review-v1"
_PUBLIC_DIAGNOSTIC_KIND = "guild_identity_search_access_diagnostic"
_PRIVATE_DIAGNOSTIC_KIND = "guild_identity_search_access_diagnostic_private"
_DIAGNOSTIC_VERSION = "guild-identity-search-access-diagnostic-v1"
_PRIVATE_PROBE_KIND = "guild_identity_search_probe_private"
_PROBE_VERSION = "guild-identity-search-probe-v1"
_SELECTED_PROFILE = "spa_fetch_context"


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
    body = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(body)
    temporary.replace(path)
    return body


def _required_object(value: object, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"guild search capture review field {field_name} must be an object")
    return value


def _required_list(value: object, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"guild search capture review field {field_name} must be a list")
    return value


def _candidate_scalar(value: object, field_name: str) -> int | str:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError(f"guild search capture review field {field_name} must be scalar")
    prepared = str(value).strip()
    if not prepared or len(prepared) > 160:
        raise ValueError(f"guild search capture review field {field_name} is invalid")
    return value


def _selected_attempt(attempts: list[Any], *, private: bool) -> dict[str, Any]:
    matches = [
        _required_object(value, "attempt")
        for value in attempts
        if isinstance(value, dict) and value.get("profile") == _SELECTED_PROFILE
    ]
    if len(matches) != 1:
        scope = "private" if private else "public"
        raise ValueError(f"{scope} diagnostic must contain one selected access attempt")
    return matches[0]


def _validate_sources(
    public_diagnostic: Mapping[str, Any],
    private_diagnostic: Mapping[str, Any],
    private_probe: Mapping[str, Any],
    *,
    private_diagnostic_body: bytes,
    private_probe_body: bytes,
    expected_guild_label: str,
) -> tuple[dict[str, Any], dict[str, Any], int | str]:
    if public_diagnostic.get("schema_version") != 1:
        raise ValueError("public access diagnostic schema mismatch")
    if public_diagnostic.get("diagnostic_kind") != _PUBLIC_DIAGNOSTIC_KIND:
        raise ValueError("public access diagnostic kind mismatch")
    if public_diagnostic.get("diagnostic_version") != _DIAGNOSTIC_VERSION:
        raise ValueError("public access diagnostic version mismatch")

    target = _required_object(public_diagnostic.get("target"), "public.target")
    if target.get("guild_label") != expected_guild_label:
        raise ValueError("public access diagnostic guild label mismatch")
    if target.get("request_url_published") is not False:
        raise ValueError("public access diagnostic publishes request URL")
    if target.get("source_guild_id_published") is not False:
        raise ValueError("public access diagnostic publishes source guild ID")

    summary = _required_object(public_diagnostic.get("summary"), "public.summary")
    if summary.get("all_integrity_checks_passed") is not True:
        raise ValueError("public access diagnostic integrity checks failed")
    if summary.get("contains_source_scalar_values") is not False:
        raise ValueError("public access diagnostic is not scalar-free")
    if summary.get("contains_error_text") is not False:
        raise ValueError("public access diagnostic publishes error text")
    if summary.get("selected_access_profile") != _SELECTED_PROFILE:
        raise ValueError("public access diagnostic selected profile mismatch")

    boundary = _required_object(
        public_diagnostic.get("decision_boundary"),
        "public.decision_boundary",
    )
    if boundary.get("ready_for_profiled_guild_search_probe") is not True:
        raise ValueError("public access diagnostic is not ready for capture review")
    if boundary.get("selected_access_profile") != _SELECTED_PROFILE:
        raise ValueError("public access diagnostic boundary profile mismatch")
    for field_name in (
        "guild_api_route_semantics_verified",
        "independent_source_identity_verified",
        "guild_identity_verified",
        "ready_for_guild_filtering",
        "ready_for_full_guild_crawl",
        "planner_scoring_allowed",
    ):
        if boundary.get(field_name) is not False:
            raise ValueError(f"public access diagnostic boundary mismatch: {field_name}")

    expected_private_hash = public_diagnostic.get("source_private_diagnostic_sha256")
    if not isinstance(expected_private_hash, str) or len(expected_private_hash) != 64:
        raise ValueError("public access diagnostic private SHA-256 is missing")
    if _sha256_bytes(private_diagnostic_body) != expected_private_hash:
        raise ValueError("private access diagnostic SHA-256 mismatch")

    if private_diagnostic.get("schema_version") != 1:
        raise ValueError("private access diagnostic schema mismatch")
    if private_diagnostic.get("diagnostic_kind") != _PRIVATE_DIAGNOSTIC_KIND:
        raise ValueError("private access diagnostic kind mismatch")
    if private_diagnostic.get("diagnostic_version") != _DIAGNOSTIC_VERSION:
        raise ValueError("private access diagnostic version mismatch")
    if private_diagnostic.get("target_guild_label") != expected_guild_label:
        raise ValueError("private access diagnostic guild label mismatch")
    if private_diagnostic.get("selected_profile") != _SELECTED_PROFILE:
        raise ValueError("private access diagnostic selected profile mismatch")

    expected_probe_hash = private_diagnostic.get("source_private_probe_sha256")
    if not isinstance(expected_probe_hash, str) or len(expected_probe_hash) != 64:
        raise ValueError("private access diagnostic probe SHA-256 is missing")
    if _sha256_bytes(private_probe_body) != expected_probe_hash:
        raise ValueError("private guild search probe SHA-256 mismatch")

    if private_probe.get("schema_version") != 1:
        raise ValueError("private guild search probe schema mismatch")
    if private_probe.get("probe_kind") != _PRIVATE_PROBE_KIND:
        raise ValueError("private guild search probe kind mismatch")
    if private_probe.get("probe_version") != _PROBE_VERSION:
        raise ValueError("private guild search probe version mismatch")
    if private_probe.get("target_guild_label") != expected_guild_label:
        raise ValueError("private guild search probe guild label mismatch")
    source_guild_id = _candidate_scalar(
        private_probe.get("candidate_source_guild_id"),
        "candidate_source_guild_id",
    )

    public_attempt = _selected_attempt(
        _required_list(public_diagnostic.get("attempts"), "public.attempts"),
        private=False,
    )
    private_attempt = _selected_attempt(
        _required_list(private_diagnostic.get("attempts"), "private.attempts"),
        private=True,
    )
    for attempt, scope in ((public_attempt, "public"), (private_attempt, "private")):
        if attempt.get("return_code") != 0:
            raise ValueError(f"{scope} selected attempt curl return code mismatch")
        if attempt.get("http_status") != 200:
            raise ValueError(f"{scope} selected attempt HTTP status mismatch")
        if attempt.get("response_candidate") is not True:
            raise ValueError(f"{scope} selected attempt is not a response candidate")
        capture = _required_object(attempt.get("capture"), f"{scope}.attempt.capture")
        if not isinstance(capture.get("payload_hash"), str):
            raise ValueError(f"{scope} selected attempt payload hash is missing")

    public_capture = _required_object(public_attempt.get("capture"), "public.capture")
    private_capture = _required_object(private_attempt.get("capture"), "private.capture")
    if public_capture != private_capture:
        raise ValueError("public/private selected capture metadata mismatch")
    if not isinstance(private_attempt.get("body"), dict):
        raise ValueError("private selected attempt body must be a JSON object")
    return public_capture, private_attempt, source_guild_id


def _read_bound_payload(
    raw_root: Path,
    capture: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], bytes]:
    payload_hash = str(capture["payload_hash"])
    manifests = list(raw_root.rglob(f"{payload_hash}.content.json"))
    if len(manifests) != 1:
        raise ValueError("raw archive must contain exactly one bound content manifest")
    manifest_path = manifests[0]
    manifest = _required_object(
        json.loads(manifest_path.read_text(encoding="utf-8")),
        "raw.content_manifest",
    )
    if manifest.get("schema_version") != 1:
        raise ValueError("raw content manifest schema mismatch")
    if manifest.get("raw_id") != capture.get("raw_id"):
        raise ValueError("raw content manifest raw ID mismatch")
    if manifest.get("payload_hash") != payload_hash:
        raise ValueError("raw content manifest payload hash mismatch")
    if manifest.get("endpoint_code") != "guild_identity_search_access_diagnostic":
        raise ValueError("raw content manifest endpoint mismatch")
    if manifest.get("bytes_uncompressed") != capture.get("bytes_uncompressed"):
        raise ValueError("raw content manifest byte count mismatch")
    if manifest.get("schema_fingerprint") != capture.get("schema_fingerprint"):
        raise ValueError("raw content manifest schema fingerprint mismatch")

    relative_payload_path = manifest.get("payload_path")
    if not isinstance(relative_payload_path, str) or not relative_payload_path:
        raise ValueError("raw content manifest payload path is missing")
    root_resolved = raw_root.resolve()
    payload_path = (raw_root / relative_payload_path).resolve()
    if root_resolved not in payload_path.parents:
        raise ValueError("raw content payload path escaped raw archive root")
    if not payload_path.is_file():
        raise ValueError("raw content payload file is missing")
    try:
        with gzip.open(payload_path, "rb") as stream:
            body = stream.read()
    except OSError as exc:
        raise ValueError("unable to read bound gzip payload") from exc
    if _sha256_bytes(body) != payload_hash:
        raise ValueError("bound gzip payload SHA-256 mismatch")
    if len(body) != capture.get("bytes_uncompressed"):
        raise ValueError("bound gzip payload byte count mismatch")
    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("bound gzip payload is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("bound guild search payload must be a JSON object")
    return manifest, payload, body


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


def _match_rows(
    payload: Mapping[str, Any],
    *,
    expected_guild_label: str,
    source_guild_id: int | str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    source_text = str(source_guild_id)
    guilds = payload.get("guilds")
    if not isinstance(guilds, list):
        return rows
    for index, candidate in enumerate(guilds):
        if not isinstance(candidate, dict):
            continue
        scalars = {str(key): value for key, value in candidate.items() if _is_scalar(value)}
        label_fields = sorted(
            key
            for key, value in scalars.items()
            if isinstance(value, str) and value == expected_guild_label
        )
        if not label_fields:
            continue
        id_fields = sorted(key for key in scalars if _id_like(key))
        id_values = {key: scalars[key] for key in id_fields}
        matching_fields = sorted(
            key
            for key, value in id_values.items()
            if value is not None and str(value) == source_text
        )
        rows.append(
            {
                "object_path": f"$.guilds[{index}]",
                "label_fields": label_fields,
                "id_like_fields": id_fields,
                "id_like_values": id_values,
                "matching_source_id_fields": matching_fields,
                "scalar_fields": scalars,
            }
        )
    return rows


def _safe_match_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    object_paths = sorted({str(row["object_path"]) for row in rows})
    label_fields = sorted({field for row in rows for field in row["label_fields"]})
    id_fields = sorted({field for row in rows for field in row["id_like_fields"]})
    matching_rows = [row for row in rows if row["matching_source_id_fields"]]
    id_value_hashes = sorted(
        {
            _sha256_json(str(value))
            for row in rows
            for value in row["id_like_values"].values()
            if value is not None
        }
    )
    one_to_one = (
        len(rows) == 1
        and len(matching_rows) == 1
        and len(rows[0]["id_like_values"]) == 1
        and len(id_value_hashes) == 1
    )
    return {
        "exact_label_object_count": len(rows),
        "source_id_match_object_count": len(matching_rows),
        "distinct_object_path_count": len(object_paths),
        "object_paths": object_paths,
        "exact_label_field_names": label_fields,
        "id_like_field_names": id_fields,
        "distinct_id_like_value_count": len(id_value_hashes),
        "id_like_value_set_sha256": _sha256_json(id_value_hashes),
        "exact_label_and_source_id_cooccur": bool(matching_rows),
        "one_to_one_identity_candidate": one_to_one,
        "contains_source_scalar_values": False,
    }


def review_guild_identity_search_capture(
    *,
    public_access_diagnostic_path: Path,
    private_access_diagnostic_path: Path,
    private_search_probe_path: Path,
    raw_root: Path,
    private_output_path: Path,
    receipt_output_path: Path,
    expected_guild_label: str = "Argentum",
) -> dict[str, Any]:
    """Review one already archived guild-search response without network access."""
    public_diagnostic, public_body = _load_object(
        public_access_diagnostic_path,
        "public guild search access diagnostic",
    )
    private_diagnostic, private_diagnostic_body = _load_object(
        private_access_diagnostic_path,
        "private guild search access diagnostic",
    )
    private_probe, private_probe_body = _load_object(
        private_search_probe_path,
        "private guild search probe",
    )
    capture, private_attempt, source_guild_id = _validate_sources(
        public_diagnostic,
        private_diagnostic,
        private_probe,
        private_diagnostic_body=private_diagnostic_body,
        private_probe_body=private_probe_body,
        expected_guild_label=expected_guild_label,
    )
    manifest, payload, payload_body = _read_bound_payload(raw_root, capture)
    if payload != private_attempt.get("body"):
        raise ValueError("private diagnostic body does not match archived payload")

    guilds = payload.get("guilds")
    success = payload.get("success")
    route_shape_candidate = success is True and isinstance(guilds, list)
    rows = _match_rows(
        payload,
        expected_guild_label=expected_guild_label,
        source_guild_id=source_guild_id,
    )
    matches = _safe_match_summary(rows)
    identity_candidate = route_shape_candidate and bool(
        matches["one_to_one_identity_candidate"]
    )

    private_payload = {
        "schema_version": 1,
        "review_kind": "guild_identity_search_capture_review_private",
        "review_version": _REVIEW_VERSION,
        "generated_at": _generated_at(),
        "source_public_diagnostic_name": public_access_diagnostic_path.name,
        "source_public_diagnostic_sha256": _sha256_bytes(public_body),
        "source_private_diagnostic_name": private_access_diagnostic_path.name,
        "source_private_diagnostic_sha256": _sha256_bytes(private_diagnostic_body),
        "source_private_search_probe_name": private_search_probe_path.name,
        "source_private_search_probe_sha256": _sha256_bytes(private_probe_body),
        "target_guild_label": expected_guild_label,
        "candidate_source_guild_id": source_guild_id,
        "selected_access_profile": _SELECTED_PROFILE,
        "capture": dict(capture),
        "raw_content_manifest": manifest,
        "payload": payload,
        "payload_sha256": _sha256_bytes(payload_body),
        "matched_objects": rows,
        "summary": {
            "route_shape_candidate": route_shape_candidate,
            "one_to_one_identity_candidate": identity_candidate,
            "contains_source_scalar_values": True,
        },
    }
    private_review_body = _write_json(private_output_path, private_payload)

    checks = {
        "public_access_diagnostic_verified": True,
        "private_access_diagnostic_sha256_verified": True,
        "private_search_probe_sha256_verified": True,
        "selected_access_profile_verified": True,
        "public_private_capture_binding_verified": True,
        "raw_content_manifest_unique": True,
        "raw_content_manifest_binding_verified": True,
        "raw_payload_sha256_verified": True,
        "raw_payload_matches_private_diagnostic": True,
        "public_receipt_scalar_boundary_preserved": True,
        "source_guild_id_not_published": True,
        "raw_payload_not_published": True,
    }
    status = (
        "independent_identity_candidate_observed"
        if identity_candidate
        else "guild_search_route_semantics_candidate_observed"
        if route_shape_candidate
        else "guild_search_capture_review_incomplete"
    )
    receipt = {
        "schema_version": 1,
        "review_kind": "guild_identity_search_capture_review",
        "review_version": _REVIEW_VERSION,
        "generated_at": _generated_at(),
        "source_public_diagnostic_name": public_access_diagnostic_path.name,
        "source_public_diagnostic_sha256": _sha256_bytes(public_body),
        "source_private_review_name": private_output_path.name,
        "source_private_review_sha256": _sha256_bytes(private_review_body),
        "target": {
            "guild_label": expected_guild_label,
            "source_guild_id_published": False,
            "raw_payload_published": False,
        },
        "capture_binding": {
            "selected_access_profile": _SELECTED_PROFILE,
            "http_status": 200,
            "content_type": private_attempt.get("content_type"),
            "bytes_uncompressed": capture.get("bytes_uncompressed"),
            "payload_hash": capture.get("payload_hash"),
            "schema_fingerprint": capture.get("schema_fingerprint"),
            "raw_id": capture.get("raw_id"),
            "observation_id": capture.get("observation_id"),
        },
        "payload_shape": {
            "top_level_kind": "object",
            "top_level_keys": sorted(str(key) for key in payload),
            "success_boolean_true": success is True,
            "guilds_is_array": isinstance(guilds, list),
            "guild_object_count": (
                sum(isinstance(value, dict) for value in guilds)
                if isinstance(guilds, list)
                else 0
            ),
            "contains_source_scalar_values": False,
        },
        "match_review": matches,
        "integrity_checks": checks,
        "decision_boundary": {
            "status": status,
            "guild_api_route_candidates_observed": True,
            "guild_search_access_profile_candidate_observed": True,
            "guild_search_route_response_captured": True,
            "guild_search_route_semantics_candidate_observed": route_shape_candidate,
            "independent_source_identity_candidate_observed": identity_candidate,
            "ready_for_guild_identity_decision_review": identity_candidate,
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
            "route_shape_candidate": route_shape_candidate,
            "exact_label_object_count": matches["exact_label_object_count"],
            "source_id_match_object_count": matches["source_id_match_object_count"],
            "one_to_one_identity_candidate": identity_candidate,
            "contains_source_scalar_values": False,
            "contains_raw_payload": False,
        },
    }
    _write_json(receipt_output_path, receipt)
    return receipt


__all__ = ["review_guild_identity_search_capture"]
