from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import parse_qsl, urlsplit

from coa_workbench.collector.spa_route_inventory import normalize_api_route_shape

_DISCOVERY_VERSION = "har-network-discovery-v1"
_JSON_MIME = "json"
_ALLOWED_RESOURCE_TYPES = {"fetch", "xhr"}


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _content_type_family(content_type: str | None) -> str:
    folded = (content_type or "").casefold()
    if "json" in folded:
        return "json"
    if "html" in folded:
        return "html"
    if folded.startswith("text/"):
        return "text"
    if not folded:
        return "unknown"
    return "binary_or_other"


def _response_body(content: Mapping[str, Any]) -> bytes | None:
    text = content.get("text")
    if text is None:
        return None
    if content.get("encoding") == "base64":
        try:
            return base64.b64decode(str(text), validate=True)
        except ValueError:
            return None
    return str(text).encode("utf-8")


def _json_shape(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_shape(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        unique: list[Any] = []
        for child in value[:100]:
            candidate = _json_shape(child)
            if candidate not in unique:
                unique.append(candidate)
        return {"list": unique}
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    return "str"


def _json_schema_fingerprint(body: bytes | None) -> str | None:
    if body is None:
        return None
    try:
        value = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return _sha256_text(_json(_json_shape(value)))


def _route_shape(url: str) -> tuple[str, tuple[str, ...]]:
    parts = urlsplit(url)
    normalized_path = normalize_api_route_shape(parts.path)
    query_keys = tuple(sorted({key for key, _ in parse_qsl(parts.query, keep_blank_values=True)}))
    if not query_keys:
        return normalized_path, ()
    query = "&".join(f"{key}=<value>" for key in query_keys)
    return f"{normalized_path}?{query}", query_keys


def _lexical_role_hint(path: str) -> str:
    folded = path.casefold()
    if folded.startswith("/api/analytics/"):
        return "telemetry"
    if folded.startswith("/api/auth/") or folded.startswith("/api/guilds-management/"):
        return "session_or_control"
    return "data_candidate"


def inventory_network_har(
    path: Path,
    *,
    allowed_host: str,
    api_prefix: str = "/api/",
) -> dict[str, Any]:
    """Inventory same-origin API traffic without retaining request/response scalar values."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries = payload.get("log", {}).get("entries", [])
    if not isinstance(entries, list):
        raise ValueError("HAR log.entries must be an array")

    groups: dict[tuple[str, str], dict[str, Any]] = {}
    observed_times: list[str] = []
    same_origin_api_entry_count = 0

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        request = entry.get("request", {})
        response = entry.get("response", {})
        if not isinstance(request, dict) or not isinstance(response, dict):
            continue

        url = str(request.get("url", ""))
        parts = urlsplit(url)
        if parts.scheme != "https" or parts.hostname != allowed_host:
            continue
        if not parts.path.startswith(api_prefix):
            continue

        content = response.get("content", {})
        if not isinstance(content, dict):
            content = {}
        content_type = str(content.get("mimeType") or "") or None
        resource_type = str(entry.get("_resourceType") or "").casefold()
        if resource_type not in _ALLOWED_RESOURCE_TYPES and _JSON_MIME not in (
            content_type or ""
        ).casefold():
            continue

        same_origin_api_entry_count += 1
        method = str(request.get("method", "")).upper() or "UNKNOWN"
        route_shape, query_keys = _route_shape(url)
        key = (method, route_shape)
        row = groups.setdefault(
            key,
            {
                "method": method,
                "route_shape": route_shape,
                "query_keys": list(query_keys),
                "lexical_role_hint": _lexical_role_hint(parts.path),
                "occurrence_count": 0,
                "statuses": set(),
                "resource_types": set(),
                "content_type_families": set(),
                "json_schema_fingerprints": set(),
                "json_response_count": 0,
                "response_body_missing_count": 0,
            },
        )
        row["occurrence_count"] += 1
        try:
            status = int(response.get("status"))
        except (TypeError, ValueError):
            status = None
        if status is not None:
            row["statuses"].add(status)
        if resource_type:
            row["resource_types"].add(resource_type)
        row["content_type_families"].add(_content_type_family(content_type))

        body = _response_body(content)
        if body is None:
            row["response_body_missing_count"] += 1
        fingerprint = _json_schema_fingerprint(body)
        if fingerprint is not None:
            row["json_response_count"] += 1
            row["json_schema_fingerprints"].add(fingerprint)

        started = entry.get("startedDateTime")
        if started:
            observed_times.append(str(started))

    routes: list[dict[str, Any]] = []
    for key in sorted(groups):
        row = groups[key]
        routes.append(
            {
                "method": row["method"],
                "route_shape": row["route_shape"],
                "query_keys": row["query_keys"],
                "lexical_role_hint": row["lexical_role_hint"],
                "occurrence_count": row["occurrence_count"],
                "statuses": sorted(row["statuses"]),
                "resource_types": sorted(row["resource_types"]),
                "content_type_families": sorted(row["content_type_families"]),
                "json_response_count": row["json_response_count"],
                "json_schema_fingerprints": sorted(row["json_schema_fingerprints"]),
                "response_body_missing_count": row["response_body_missing_count"],
                "semantic_status": "network_observed_candidate",
            }
        )

    sanitized_fingerprint = _sha256_text(_json(routes))
    return {
        "schema_version": 1,
        "inventory_kind": "same_origin_har_api_inventory",
        "inventory_version": _DISCOVERY_VERSION,
        "allowed_host": allowed_host,
        "api_prefix": api_prefix,
        "observed_at_min": min(observed_times) if observed_times else None,
        "observed_at_max": max(observed_times) if observed_times else None,
        "routes": routes,
        "summary": {
            "same_origin_api_entry_count": same_origin_api_entry_count,
            "route_shape_count": len(routes),
            "data_candidate_route_count": sum(
                row["lexical_role_hint"] == "data_candidate" for row in routes
            ),
            "sanitized_inventory_fingerprint": sanitized_fingerprint,
            "contains_query_values": False,
            "contains_request_headers": False,
            "contains_cookies": False,
            "contains_response_bodies": False,
            "contains_response_scalar_values": False,
            "semantic_review_required": True,
            "network_requests_performed": False,
        },
    }


__all__ = ["inventory_network_har"]
