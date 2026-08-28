from __future__ import annotations

import gzip
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable
from urllib.request import Request

from .armory_capture import BuildAssetCapture
from .http_read import read_response_resilient
from .raw_archive import RawArchive, RawCapture, request_key_from_url
from .route_discovery import discover_api_route_candidates
from .source_registry import SourceRegistry

OpenUrl = Callable[..., Any]
_MAX_ASSET_BYTES = 16 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class ArchivedPayload:
    body: bytes
    content_type: str | None
    payload_hash: str
    route_candidates: tuple[str, ...]
    candidate_count: int
    selected_fetched_at: str | None
    selection_reason: str


@dataclass(frozen=True, slots=True)
class _ArchivedCandidate:
    body: bytes
    content_type: str | None
    payload_hash: str
    raw_id: str
    route_candidates: tuple[str, ...]
    fetched_at: str | None

    @property
    def score(self) -> tuple[str, int, int]:
        return (
            self.fetched_at or "",
            len(self.route_candidates),
            len(self.body),
        )


def _latest_observation_times(archive: RawArchive, raw_ids: set[str]) -> dict[str, str]:
    latest: dict[str, str] = {}
    if not raw_ids:
        return latest
    for observation_path in archive.root.rglob("observations/*.json"):
        try:
            observation = json.loads(observation_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        raw_id = observation.get("raw_id")
        fetched_at = observation.get("fetched_at")
        if raw_id not in raw_ids or not isinstance(fetched_at, str):
            continue
        previous = latest.get(raw_id)
        if previous is None or fetched_at > previous:
            latest[raw_id] = fetched_at
    return latest


def _read_candidate_body(
    archive: RawArchive,
    *,
    manifest: dict[str, Any],
    max_bytes: int,
) -> tuple[bytes | None, str | None]:
    payload_hash = manifest.get("payload_hash")
    payload_path = manifest.get("payload_path")
    if not isinstance(payload_hash, str) or not isinstance(payload_path, str):
        return None, None
    try:
        with gzip.open(archive.root / payload_path, "rb") as stream:
            body = stream.read(max_bytes + 1)
    except (OSError, EOFError):
        return None, "archived asset payload could not be read"
    if len(body) > max_bytes:
        return None, f"archived asset exceeded {max_bytes} bytes"
    if hashlib.sha256(body).hexdigest() != payload_hash:
        return None, "archived asset payload hash did not match its manifest"
    return body, None


def _read_exact_archived_payload(
    archive: RawArchive,
    *,
    source_code: str,
    request_key: str,
    max_bytes: int,
) -> tuple[ArchivedPayload | None, str | None]:
    """Select the latest verified route-bearing payload for one exact request key."""
    manifests: dict[str, dict[str, Any]] = {}
    for manifest_path in archive.root.rglob("*.content.json"):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if manifest.get("source_code") != source_code:
            continue
        if manifest.get("request_key") != request_key:
            continue
        size = manifest.get("bytes_uncompressed")
        if not isinstance(size, int) or size < 0 or size > max_bytes:
            continue
        payload_hash = manifest.get("payload_hash")
        raw_id = manifest.get("raw_id")
        if not isinstance(payload_hash, str) or not isinstance(raw_id, str):
            continue
        manifests.setdefault(payload_hash, manifest)

    if not manifests:
        return None, None

    latest_times = _latest_observation_times(
        archive,
        {
            str(manifest["raw_id"])
            for manifest in manifests.values()
            if isinstance(manifest.get("raw_id"), str)
        },
    )
    candidates: list[_ArchivedCandidate] = []
    read_errors: list[str] = []
    for payload_hash, manifest in manifests.items():
        body, error = _read_candidate_body(
            archive,
            manifest=manifest,
            max_bytes=max_bytes,
        )
        if body is None:
            if error:
                read_errors.append(error)
            continue
        content_type = manifest.get("content_type")
        prepared_content_type = str(content_type) if content_type else None
        routes = discover_api_route_candidates(body)
        if not routes:
            continue
        candidates.append(
            _ArchivedCandidate(
                body=body,
                content_type=prepared_content_type,
                payload_hash=payload_hash,
                raw_id=str(manifest["raw_id"]),
                route_candidates=routes,
                fetched_at=latest_times.get(str(manifest["raw_id"])),
            )
        )

    if not candidates:
        if read_errors:
            return None, sorted(read_errors)[0]
        return None, "archive has no verified route-bearing payload for the exact asset request"

    candidates.sort(key=lambda item: item.score, reverse=True)
    selected = candidates[0]
    if len(candidates) > 1 and candidates[1].score == selected.score:
        return None, "archive has multiple equally ranked verified payloads for the exact asset request"

    return (
        ArchivedPayload(
            body=selected.body,
            content_type=selected.content_type,
            payload_hash=selected.payload_hash,
            route_candidates=selected.route_candidates,
            candidate_count=len(candidates),
            selected_fetched_at=selected.fetched_at,
            selection_reason="latest_verified_route_bearing_payload",
        ),
        None,
    )


def capture_asset_with_archive_fallback(
    *,
    registry: SourceRegistry,
    archive: RawArchive,
    parent_capture: RawCapture,
    page_kind: str,
    asset_kind: str,
    url: str,
    timeout_seconds: float,
    opener: OpenUrl,
) -> BuildAssetCapture:
    """Capture a build asset live, then reuse verified archived evidence if live reading fails."""
    request = Request(
        url,
        headers={
            "Accept": "application/javascript,text/javascript,*/*;q=0.1",
            "User-Agent": "CoA-Raid-Intelligence-Workbench/0.1 armory-asset-capture",
        },
        method="GET",
    )
    request_key = request_key_from_url("GET", url)
    status, content_type, body, live_error = read_response_resilient(
        request,
        timeout_seconds=timeout_seconds,
        opener=opener,
        max_bytes=_MAX_ASSET_BYTES,
    )

    reused: ArchivedPayload | None = None
    fallback_error: str | None = None
    if body is None:
        reused, fallback_error = _read_exact_archived_payload(
            archive,
            source_code=registry.source_code,
            request_key=request_key,
            max_bytes=_MAX_ASSET_BYTES,
        )
        if reused is None:
            if live_error and fallback_error:
                error = (
                    f"live capture: {live_error}; "
                    f"archive fallback: {fallback_error}"
                )
            else:
                error = live_error or fallback_error or "asset capture failed"
            return BuildAssetCapture(
                url,
                asset_kind,
                status,
                content_type,
                None,
                (),
                error,
            )
        body = reused.body
        content_type = content_type or reused.content_type

    routes = reused.route_candidates if reused else discover_api_route_candidates(body)
    capture = archive.capture_bytes(
        body,
        source_code=registry.source_code,
        endpoint_code="build_page_asset",
        request_key=request_key,
        fetched_at=datetime.now(timezone.utc),
        http_status=status,
        content_type=content_type,
        request_url=url,
        metadata={
            "capture_mode": "autonomous_build_asset",
            "asset_kind": asset_kind,
            "discovered_from_page_kind": page_kind,
            "parent_payload_hash": parent_capture.payload_hash,
            "request_header_names": sorted(request.headers),
            "archive_reuse": reused is not None,
            "archive_reuse_payload_hash": reused.payload_hash if reused else None,
            "archive_reuse_candidate_count": reused.candidate_count if reused else 0,
            "archive_reuse_selected_fetched_at": reused.selected_fetched_at if reused else None,
            "archive_reuse_selection_reason": reused.selection_reason if reused else None,
            "live_read_error": live_error if reused else None,
        },
    )
    return BuildAssetCapture(
        url=url,
        asset_kind=asset_kind,
        status=status,
        content_type=content_type,
        capture=capture,
        api_route_candidates=routes,
        error=None,
    )
