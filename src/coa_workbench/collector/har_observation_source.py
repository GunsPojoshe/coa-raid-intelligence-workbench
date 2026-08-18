from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit

from coa_workbench.collector.network_observation import NetworkObservation

HAR_OBSERVATION_SOURCE_VERSION = "har-observation-source-v1"


def _body_from_content(content: Mapping[str, Any]) -> bytes | None:
    text = content.get("text")
    if text is None:
        return None
    if content.get("encoding") == "base64":
        try:
            return base64.b64decode(str(text), validate=True)
        except ValueError:
            return None
    return str(text).encode("utf-8")


def _request_body(request: Mapping[str, Any]) -> tuple[str | None, bytes | None]:
    post_data = request.get("postData")
    if not isinstance(post_data, dict):
        return None, None
    mime_type = str(post_data.get("mimeType") or "") or None
    text = post_data.get("text")
    if text is None:
        return mime_type, None
    return mime_type, str(text).encode("utf-8")


def load_har_network_observations(
    path: Path,
    *,
    allowed_host: str | None = None,
    api_prefix: str | None = None,
) -> tuple[NetworkObservation, ...]:
    """Convert a HAR into provider-neutral observations without mutating the HAR."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    entries = payload.get("log", {}).get("entries", [])
    if not isinstance(entries, list):
        raise ValueError("HAR log.entries must be an array")

    observations: list[NetworkObservation] = []
    for ordinal, raw_entry in enumerate(entries):
        if not isinstance(raw_entry, dict):
            continue
        request = raw_entry.get("request")
        response = raw_entry.get("response")
        if not isinstance(request, dict) or not isinstance(response, dict):
            continue

        url = str(request.get("url") or "")
        parts = urlsplit(url)
        if not parts.scheme or not parts.hostname:
            continue
        if allowed_host is not None and parts.hostname != allowed_host:
            continue
        if api_prefix is not None and not parts.path.startswith(api_prefix):
            continue

        observed_at = str(raw_entry.get("startedDateTime") or "")
        if not observed_at:
            continue

        method = str(request.get("method") or "UNKNOWN").upper()
        try:
            status = int(response.get("status"))
        except (TypeError, ValueError):
            status = None

        request_content_type, request_body = _request_body(request)
        content = response.get("content")
        if not isinstance(content, dict):
            content = {}
        response_content_type = str(content.get("mimeType") or "") or None
        response_body = _body_from_content(content)
        resource_type = str(raw_entry.get("_resourceType") or "") or None

        observations.append(
            NetworkObservation(
                ordinal=ordinal,
                observed_at=observed_at,
                method=method,
                url=url,
                status=status,
                request_content_type=request_content_type,
                response_content_type=response_content_type,
                request_body=request_body,
                response_body=response_body,
                resource_type=resource_type,
                source_kind="har",
            )
        )

    return tuple(observations)


__all__ = ["HAR_OBSERVATION_SOURCE_VERSION", "load_har_network_observations"]
