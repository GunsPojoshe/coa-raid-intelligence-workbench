from __future__ import annotations

import gzip
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.parse import quote, urljoin

from .armory_api_capture import ArmoryApiObservation
from .http_profile import SameOriginHttpSession
from .http_read import read_response_resilient
from .raw_archive import (
    RawArchive,
    RawCapture,
    request_key_from_url,
    sanitize_url,
    schema_fingerprint,
)
from .source_registry import SourceRegistry

OpenUrl = Callable[..., Any]
ARMORY_ENDPOINT_KINDS = ("character", "talent_grid")
_MAX_JSON_BYTES = 32 * 1024 * 1024
_PROGRESS_SCHEMA_VERSION = 1
_SUCCESS_STATES = {"captured", "reused"}


@dataclass(frozen=True, slots=True)
class ArmoryEndpointCaptureResult:
    endpoint_kind: str
    http_profile_version: str
    observation: ArmoryApiObservation


def _utc_now_text() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _prepared_subject(character_id: int | str, class_slug: str) -> tuple[str, str]:
    if isinstance(character_id, bool):
        raise ValueError("character_id must be an integer or non-empty string")
    prepared_character_id = str(character_id).strip()
    prepared_class_slug = class_slug.strip().casefold()
    if not prepared_character_id:
        raise ValueError("character_id cannot be empty")
    if not prepared_class_slug:
        raise ValueError("class_slug cannot be empty")
    return prepared_character_id, prepared_class_slug


def _prepared_endpoint_kinds(endpoint_kinds: Iterable[str]) -> tuple[str, ...]:
    prepared = tuple(str(item).strip().casefold().replace("-", "_") for item in endpoint_kinds)
    if not prepared:
        raise ValueError("at least one endpoint kind is required")
    unknown = sorted(set(prepared) - set(ARMORY_ENDPOINT_KINDS))
    if unknown:
        raise ValueError(f"unsupported Armory endpoint kind(s): {', '.join(unknown)}")
    if len(set(prepared)) != len(prepared):
        raise ValueError("endpoint kinds must not contain duplicates")
    return prepared


def _endpoint_url(
    base_url: str,
    endpoint_kind: str,
    *,
    character_id: str,
    class_slug: str,
) -> str:
    if endpoint_kind == "character":
        path = f"/api/armory/character/{quote(character_id, safe='')}"
    elif endpoint_kind == "talent_grid":
        path = f"/api/armory/talent-grid/{quote(class_slug, safe='')}"
    else:
        raise ValueError(f"unsupported Armory endpoint kind: {endpoint_kind}")
    return urljoin(f"{base_url.rstrip('/')}/", path.lstrip("/"))


def _relative_archive_path(path: str, *, archive_root: Path) -> str:
    root = archive_root.resolve()
    candidate = Path(path).resolve()
    try:
        return candidate.relative_to(root).as_posix()
    except ValueError as exc:
        raise RuntimeError("capture path escaped the configured raw archive root") from exc


def _safe_capture_to_dict(capture: RawCapture, *, archive_root: Path) -> dict[str, Any]:
    return {
        "raw_id": capture.raw_id,
        "observation_id": capture.observation_id,
        "source_code": capture.source_code,
        "endpoint_code": capture.endpoint_code,
        "request_key": capture.request_key,
        "payload_hash": capture.payload_hash,
        "payload_path": _relative_archive_path(capture.payload_path, archive_root=archive_root),
        "observation_manifest_path": _relative_archive_path(
            capture.manifest_path,
            archive_root=archive_root,
        ),
        "duplicate_payload": capture.duplicate_payload,
        "duplicate_observation": capture.duplicate_observation,
        "bytes_uncompressed": capture.bytes_uncompressed,
        "content_type": capture.content_type,
        "schema_fingerprint": capture.schema_fingerprint,
        "fetched_at": capture.fetched_at,
        "http_status": capture.http_status,
    }


def _archive_path(archive_root: Path, relative_path: object) -> Path | None:
    if not isinstance(relative_path, str) or not relative_path:
        return None
    candidate_relative = Path(relative_path)
    if candidate_relative.is_absolute():
        return None
    root = archive_root.resolve()
    candidate = (root / candidate_relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate


def _entry_has_reusable_capture(entry: object, *, archive: RawArchive) -> bool:
    if not isinstance(entry, dict) or entry.get("state") not in _SUCCESS_STATES:
        return False
    capture = entry.get("capture")
    if not isinstance(capture, dict):
        return False

    payload_hash = capture.get("payload_hash")
    content_type = capture.get("content_type")
    expected_fingerprint = capture.get("schema_fingerprint")
    expected_size = capture.get("bytes_uncompressed")
    if not isinstance(payload_hash, str) or len(payload_hash) != 64:
        return False
    if not isinstance(expected_fingerprint, str) or len(expected_fingerprint) != 64:
        return False
    if not isinstance(expected_size, int) or expected_size < 0 or expected_size > _MAX_JSON_BYTES:
        return False

    payload_path = _archive_path(archive.root, capture.get("payload_path"))
    observation_path = _archive_path(archive.root, capture.get("observation_manifest_path"))
    if payload_path is None or observation_path is None:
        return False
    if not payload_path.is_file() or not observation_path.is_file():
        return False

    try:
        with gzip.open(payload_path, "rb") as stream:
            body = stream.read(_MAX_JSON_BYTES + 1)
    except (OSError, EOFError):
        return False
    if len(body) != expected_size or len(body) > _MAX_JSON_BYTES:
        return False
    if hashlib.sha256(body).hexdigest() != payload_hash:
        return False
    prepared_content_type = str(content_type) if content_type else None
    return schema_fingerprint(body, prepared_content_type) == expected_fingerprint


def _write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    states = [
        entry.get("state")
        for entry in manifest.get("endpoints", {}).values()
        if isinstance(entry, dict)
    ]
    manifest["summary"] = {
        "endpoint_count": len(states),
        "captured": states.count("captured"),
        "reused": states.count("reused"),
        "failed": states.count("failed"),
        "pending": states.count("pending"),
        "complete": bool(states) and all(state in _SUCCESS_STATES for state in states),
    }
    manifest["updated_at"] = _utc_now_text()
    rendered = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(path)


def _load_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Armory progress manifest must contain a JSON object")
    if payload.get("schema_version") != _PROGRESS_SCHEMA_VERSION:
        raise ValueError("unsupported Armory progress manifest schema version")
    if not isinstance(payload.get("endpoints"), dict):
        raise ValueError("Armory progress manifest endpoints must be an object")
    return payload


def capture_armory_endpoint(
    registry: SourceRegistry,
    archive: RawArchive,
    *,
    endpoint_kind: str,
    character_id: int | str,
    class_slug: str,
    timeout_seconds: float = 20.0,
    retry_count: int = 0,
    opener: OpenUrl | Any | None = None,
    session: SameOriginHttpSession | None = None,
) -> ArmoryEndpointCaptureResult:
    """Capture one verified Armory route template without assigning game semantics."""
    prepared_character_id, prepared_class_slug = _prepared_subject(character_id, class_slug)
    prepared_kind = _prepared_endpoint_kinds((endpoint_kind,))[0]
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than zero")
    if retry_count < 0 or retry_count > 1:
        raise ValueError("retry_count must be between 0 and 1")
    if session is not None and opener is not None:
        raise ValueError("pass either session or opener, not both")

    active_session = session or SameOriginHttpSession(registry.base_url, opener=opener)
    url = _endpoint_url(
        registry.base_url,
        prepared_kind,
        character_id=prepared_character_id,
        class_slug=prepared_class_slug,
    )
    request = active_session.build_request(url)
    status, content_type, body, transport_error = read_response_resilient(
        request,
        timeout_seconds=timeout_seconds,
        opener=active_session.open,
        max_bytes=_MAX_JSON_BYTES,
        retry_count=retry_count,
    )

    if body is None or transport_error is not None:
        observation = ArmoryApiObservation(
            observation_kind=prepared_kind,
            url=sanitize_url(url),
            status=status,
            content_type=content_type,
            capture=None,
            top_level_keys=(),
            error=transport_error or "response body was unavailable",
        )
        return ArmoryEndpointCaptureResult(
            endpoint_kind=prepared_kind,
            http_profile_version=active_session.profile.version,
            observation=observation,
        )

    capture = archive.capture_bytes(
        body,
        source_code=registry.source_code,
        endpoint_code=f"armory_api_{prepared_kind}",
        request_key=request_key_from_url("GET", url),
        fetched_at=datetime.now(timezone.utc),
        http_status=status,
        content_type=content_type,
        request_url=url,
        metadata={
            "capture_mode": "endpoint_isolated_armory_api",
            "observation_kind": prepared_kind,
            **active_session.safe_request_metadata(request),
        },
    )

    parsed: Any | None = None
    parse_error: str | None = None
    try:
        parsed = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        parse_error = "response was not valid JSON"
    if parse_error is None and capture.schema_fingerprint is None:
        parse_error = "valid JSON response had no schema fingerprint"

    top_level_keys = (
        tuple(sorted(str(key) for key in parsed)) if isinstance(parsed, dict) else ()
    )
    observation = ArmoryApiObservation(
        observation_kind=prepared_kind,
        url=sanitize_url(url),
        status=status,
        content_type=content_type,
        capture=capture,
        top_level_keys=top_level_keys,
        error=parse_error,
    )
    return ArmoryEndpointCaptureResult(
        endpoint_kind=prepared_kind,
        http_profile_version=active_session.profile.version,
        observation=observation,
    )


def capture_armory_endpoints_progressively(
    registry: SourceRegistry,
    archive: RawArchive,
    *,
    character_id: int | str,
    class_slug: str,
    output_path: Path,
    endpoint_kinds: Iterable[str] = ARMORY_ENDPOINT_KINDS,
    timeout_seconds: float = 20.0,
    retry_count: int = 0,
    resume: bool = True,
    opener: OpenUrl | Any | None = None,
) -> dict[str, Any]:
    """Capture selected Armory endpoints and atomically persist state around every attempt."""
    prepared_character_id, prepared_class_slug = _prepared_subject(character_id, class_slug)
    prepared_kinds = _prepared_endpoint_kinds(endpoint_kinds)
    session = SameOriginHttpSession(registry.base_url, opener=opener)

    if resume and output_path.is_file():
        manifest = _load_manifest(output_path)
        subject = manifest.get("subject")
        expected_subject = {
            "character_id": prepared_character_id,
            "class_slug": prepared_class_slug,
        }
        if subject != expected_subject:
            raise ValueError("Armory progress manifest subject does not match this capture")
        if manifest.get("http_profile_version") != session.profile.version:
            raise ValueError("Armory progress manifest HTTP profile version does not match")
    else:
        now = _utc_now_text()
        manifest = {
            "schema_version": _PROGRESS_SCHEMA_VERSION,
            "capture_mode": "endpoint_isolated_armory_api",
            "http_profile_version": session.profile.version,
            "subject": {
                "character_id": prepared_character_id,
                "class_slug": prepared_class_slug,
            },
            "endpoint_order": [],
            "endpoints": {},
            "created_at": now,
            "updated_at": now,
        }

    endpoint_order = manifest["endpoint_order"]
    endpoints = manifest["endpoints"]
    for endpoint_kind in prepared_kinds:
        if endpoint_kind not in endpoint_order:
            endpoint_order.append(endpoint_kind)

        existing = endpoints.get(endpoint_kind)
        if resume and _entry_has_reusable_capture(existing, archive=archive):
            reused_at = _utc_now_text()
            endpoints[endpoint_kind] = {
                **existing,
                "state": "reused",
                "reuse_count": int(existing.get("reuse_count") or 0) + 1,
                "last_reused_at": reused_at,
            }
            _write_manifest(output_path, manifest)
            continue

        attempt_started_at = _utc_now_text()
        previous_attempts = int(existing.get("attempt_count") or 0) if isinstance(existing, dict) else 0
        endpoints[endpoint_kind] = {
            "endpoint_kind": endpoint_kind,
            "state": "pending",
            "attempt_count": previous_attempts + 1,
            "last_attempt_started_at": attempt_started_at,
            "status": None,
            "content_type": None,
            "top_level_keys": [],
            "error": None,
            "capture": None,
        }
        _write_manifest(output_path, manifest)

        result = capture_armory_endpoint(
            registry,
            archive,
            endpoint_kind=endpoint_kind,
            character_id=prepared_character_id,
            class_slug=prepared_class_slug,
            timeout_seconds=timeout_seconds,
            retry_count=retry_count,
            session=session,
        )
        observation = result.observation
        success = (
            observation.capture is not None
            and observation.error is None
            and observation.status is not None
            and 200 <= observation.status < 300
        )
        endpoints[endpoint_kind] = {
            "endpoint_kind": endpoint_kind,
            "route": observation.url,
            "state": "captured" if success else "failed",
            "attempt_count": previous_attempts + 1,
            "last_attempt_started_at": attempt_started_at,
            "last_attempt_completed_at": _utc_now_text(),
            "status": observation.status,
            "content_type": observation.content_type,
            "top_level_keys": list(observation.top_level_keys),
            "error": observation.error,
            "capture": (
                _safe_capture_to_dict(observation.capture, archive_root=archive.root)
                if observation.capture is not None
                else None
            ),
        }
        _write_manifest(output_path, manifest)

    return manifest
