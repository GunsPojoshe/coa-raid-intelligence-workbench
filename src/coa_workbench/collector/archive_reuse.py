from __future__ import annotations

import gzip
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
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


def _read_exact_archived_payload(
    archive: RawArchive,
    *,
    source_code: str,
    request_key: str,
    max_bytes: int,
) -> tuple[ArchivedPayload | None, str | None]:
    """Load one unambiguous payload already captured for the exact request key."""
    matches: dict[str, dict[str, Any]] = {}
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
        payload_path = manifest.get("payload_path")
        if not isinstance(payload_hash, str) or not isinstance(payload_path, str):
            continue
        matches.setdefault(payload_hash, manifest)

    if not matches:
        return None, None
    if len(matches) > 1:
        return None, "archive contains multiple payloads for the exact asset request"

    payload_hash, manifest = next(iter(matches.items()))
    payload_path = archive.root / str(manifest["payload_path"])
    try:
        with gzip.open(payload_path, "rb") as stream:
            body = stream.read(max_bytes + 1)
    except (OSError, EOFError):
        return None, "archived asset payload could not be read"
    if len(body) > max_bytes:
        return None, f"archived asset exceeded {max_bytes} bytes"
    if hashlib.sha256(body).hexdigest() != payload_hash:
        return None, "archived asset payload hash did not match its manifest"

    content_type = manifest.get("content_type")
    return (
        ArchivedPayload(
            body=body,
            content_type=str(content_type) if content_type else None,
            payload_hash=payload_hash,
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
    """Capture a build asset live, then reuse an exact archived copy if live reading fails."""
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
            error = fallback_error or live_error
            return BuildAssetCapture(url, asset_kind, status, content_type, None, (), error)
        body = reused.body
        content_type = content_type or reused.content_type

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
            "live_read_error": live_error if reused else None,
        },
    )
    return BuildAssetCapture(
        url=url,
        asset_kind=asset_kind,
        status=status,
        content_type=content_type,
        capture=capture,
        api_route_candidates=discover_api_route_candidates(body),
        error=None,
    )
