from __future__ import annotations

import gzip
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qsl, urlsplit

from .route_discovery import discover_api_route_candidates

_INVENTORY_SCHEMA_VERSION = 1
_DEFAULT_ENDPOINT_CODE = "build_page_asset"
_DEFAULT_MAX_ARCHIVES = 64
_DEFAULT_MAX_UNCOMPRESSED_BYTES = 16 * 1024 * 1024
_DEFAULT_HINT_KEYWORDS = (
    "report",
    "encounter",
    "roster",
    "participant",
    "actor",
    "event",
    "aura",
)

_TEMPLATE_EXPRESSION = re.compile(r"\$\{[^{}]*\}")
_INTEGER_SEGMENT = re.compile(r"\d+")
_UUID_SEGMENT = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-"
    r"[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}"
)
_LONG_HEX_SEGMENT = re.compile(r"[0-9a-fA-F]{24,}")
_NAMED_PARAMETER_SEGMENT = re.compile(r"(?::[^/]+|\[[^/]+\])")


def _load_object(path: Path, description: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{description} must contain a JSON object")
    return payload


def _required_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"SPA route inventory field {name} must be a non-empty string")
    return value


def _required_integer(value: object, name: str, *, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise ValueError(
            f"SPA route inventory field {name} must be an integer greater than or equal to "
            f"{minimum}"
        )
    return value


def _safe_archive_path(raw_root: Path, relative_path: str) -> Path:
    root = raw_root.resolve()
    candidate = (root / relative_path).resolve()
    if not candidate.is_relative_to(root):
        raise ValueError("SPA asset archive escaped raw-root")
    if not candidate.is_file() or not candidate.name.endswith(".gz"):
        raise ValueError("SPA asset archive must be a gzip file below raw-root")
    return candidate


def _normalize_segment(segment: str) -> str:
    replaced = _TEMPLATE_EXPRESSION.sub("{template}", segment)
    if _INTEGER_SEGMENT.fullmatch(replaced):
        return "{integer}"
    if _UUID_SEGMENT.fullmatch(replaced):
        return "{uuid}"
    if _LONG_HEX_SEGMENT.fullmatch(replaced):
        return "{token}"
    if _NAMED_PARAMETER_SEGMENT.fullmatch(replaced):
        return "{parameter}"
    return replaced


def normalize_api_route_shape(candidate: str) -> str:
    """Create a stable privacy-safe route shape from one discovered SPA literal."""
    parts = urlsplit(candidate)
    normalized_path = "/".join(_normalize_segment(part) for part in parts.path.split("/"))
    query_keys = [key for key, _value in parse_qsl(parts.query, keep_blank_values=True)]
    query = "&".join(f"{key}=<value>" for key in query_keys)
    return normalized_path + (f"?{query}" if query else "")


def _iter_content_manifests(raw_root: Path, endpoint_code: str) -> Iterable[Path]:
    pattern = f"**/endpoint={endpoint_code}/*.content.json"
    yield from sorted(raw_root.glob(pattern), key=lambda path: path.as_posix())


def build_spa_route_inventory(
    raw_root: Path,
    *,
    endpoint_code: str = _DEFAULT_ENDPOINT_CODE,
    max_archives: int = _DEFAULT_MAX_ARCHIVES,
    max_uncompressed_bytes: int = _DEFAULT_MAX_UNCOMPRESSED_BYTES,
    hint_keywords: tuple[str, ...] = _DEFAULT_HINT_KEYWORDS,
) -> dict[str, Any]:
    """Verify archived SPA assets and emit route shapes without response-record scalars."""
    if max_archives < 1:
        raise ValueError("max_archives must be at least 1")
    if max_uncompressed_bytes < 1:
        raise ValueError("max_uncompressed_bytes must be at least 1")

    manifests = list(_iter_content_manifests(raw_root, endpoint_code))
    if not manifests:
        raise FileNotFoundError(
            f"no archived SPA asset content manifests found for endpoint {endpoint_code!r}"
        )
    if len(manifests) > max_archives:
        raise ValueError(
            f"SPA asset archive count {len(manifests)} exceeds bounded maximum {max_archives}"
        )

    archive_rows: list[dict[str, Any]] = []
    route_sources: dict[str, set[str]] = {}
    seen_hashes: set[str] = set()

    for manifest_path in manifests:
        manifest = _load_object(manifest_path, "SPA asset content manifest")
        if manifest.get("schema_version") != 1:
            raise ValueError("unsupported SPA asset content-manifest schema version")
        if manifest.get("endpoint_code") not in {None, endpoint_code}:
            raise ValueError("SPA asset content manifest endpoint mismatch")

        payload_hash = _required_string(manifest.get("payload_hash"), "payload_hash").casefold()
        if len(payload_hash) != 64 or any(char not in "0123456789abcdef" for char in payload_hash):
            raise ValueError("SPA asset payload_hash must be a SHA-256 hex digest")
        if payload_hash in seen_hashes:
            continue
        seen_hashes.add(payload_hash)

        bytes_uncompressed = _required_integer(
            manifest.get("bytes_uncompressed"),
            "bytes_uncompressed",
            minimum=1,
        )
        if bytes_uncompressed > max_uncompressed_bytes:
            raise ValueError(
                f"SPA asset {payload_hash} exceeds bounded maximum {max_uncompressed_bytes} bytes"
            )

        relative_payload_path = _required_string(manifest.get("payload_path"), "payload_path")
        archive_path = _safe_archive_path(raw_root, relative_payload_path)
        body = gzip.decompress(archive_path.read_bytes())
        calculated_hash = hashlib.sha256(body).hexdigest()
        if calculated_hash != payload_hash:
            raise ValueError(f"SPA asset payload hash mismatch for {payload_hash}")
        if len(body) != bytes_uncompressed:
            raise ValueError(f"SPA asset uncompressed byte count mismatch for {payload_hash}")

        candidates = tuple(
            sorted(
                {
                    normalize_api_route_shape(candidate)
                    for candidate in discover_api_route_candidates(body)
                }
            )
        )
        for route in candidates:
            route_sources.setdefault(route, set()).add(payload_hash)

        archive_rows.append(
            {
                "payload_hash": payload_hash,
                "bytes_uncompressed": bytes_uncompressed,
                "content_type": manifest.get("content_type"),
                "route_candidate_count": len(candidates),
                "archive_verified": True,
            }
        )

    normalized_keywords = tuple(
        sorted({keyword.strip().casefold() for keyword in hint_keywords if keyword.strip()})
    )
    route_rows: list[dict[str, Any]] = []
    relevant_count = 0
    for route in sorted(route_sources):
        lowered = route.casefold()
        lexical_hints = [keyword for keyword in normalized_keywords if keyword in lowered]
        if lexical_hints:
            relevant_count += 1
        route_rows.append(
            {
                "route_shape": route,
                "archive_count": len(route_sources[route]),
                "payload_hashes": sorted(route_sources[route]),
                "lexical_hints": lexical_hints,
                "semantic_status": "unverified_candidate",
            }
        )

    return {
        "schema_version": _INVENTORY_SCHEMA_VERSION,
        "inventory_kind": "archived_spa_api_route_inventory",
        "endpoint_code": endpoint_code,
        "archives": archive_rows,
        "routes": route_rows,
        "summary": {
            "archive_count": len(archive_rows),
            "route_candidate_count": len(route_rows),
            "lexically_relevant_candidate_count": relevant_count,
            "all_archives_verified": True,
            "contains_source_record_scalar_values": False,
            "semantic_verification_required": True,
            "network_requests_performed": False,
        },
    }
