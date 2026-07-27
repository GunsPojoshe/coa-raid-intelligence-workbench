from __future__ import annotations

import base64
import binascii
import gzip
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlsplit

from coa_workbench.normalizer import inspect_payload

from .raw_archive import RawArchive, request_key_from_url

INVENTORY_SCHEMA_VERSION = 1


def _generated_at() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_started_at(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _body(content: dict[str, Any]) -> bytes:
    text = content.get("text")
    if text is None:
        return b""
    if not isinstance(text, str):
        raise ValueError("response content text is not a string")
    encoding = content.get("encoding")
    if encoding in (None, ""):
        return text.encode("utf-8")
    if encoding == "base64":
        try:
            return base64.b64decode(text, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError("invalid base64 response body") from exc
    raise ValueError("unsupported response body encoding")


def _json_details(body: bytes, mime_type: str | None) -> tuple[str, dict[str, Any] | None]:
    if not body:
        return "empty_body", None
    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        if mime_type and "json" in mime_type.casefold():
            return "invalid_json", None
        if mime_type and ("html" in mime_type.casefold() or "xml" in mime_type.casefold()):
            return "html", None
        return "binary", None
    inspection = inspect_payload(payload)
    kind = "json_array" if isinstance(payload, list) else "json_object"
    if not isinstance(payload, (dict, list)):
        kind = "json_scalar"
    return kind, {
        "schema_fingerprint": inspection.schema_fingerprint,
        "top_level_kind": _json_kind(payload),
        "top_level_keys": sorted(str(key) for key in payload) if isinstance(payload, dict) else [],
        "candidate_collections": [asdict(candidate) for candidate in inspection.candidates],
    }


def _json_kind(payload: Any) -> str:
    if isinstance(payload, dict):
        return "object"
    if isinstance(payload, list):
        return "array"
    if payload is None:
        return "null"
    if isinstance(payload, bool):
        return "boolean"
    if isinstance(payload, (int, float)):
        return "number"
    return "string"


@dataclass(slots=True)
class HarInventoryEntry:
    ordinal: int
    method: str | None = None
    route_path: str | None = None
    query_keys: list[str] | None = None
    http_status: int | None = None
    content_type: str | None = None
    response_body_encoding: str | None = None
    bytes_uncompressed: int | None = None
    payload_hash: str | None = None
    schema_fingerprint: str | None = None
    top_level_kind: str | None = None
    top_level_keys: list[str] | None = None
    candidate_collections: list[dict[str, Any]] | None = None
    candidate_label: str | None = None
    raw_id: str | None = None
    observation_id: str | None = None
    duplicate_payload: bool | None = None
    skip_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def inventory_har(
    path: Path,
    *,
    archive: RawArchive,
    source_code: str,
    allowed_host: str,
) -> dict[str, Any]:
    """Inventory and archive safe HAR response data without assigning domain semantics."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries = payload.get("log", {}).get("entries", [])
    if not isinstance(entries, list):
        raise ValueError("HAR log.entries must be an array")
    inventory: list[HarInventoryEntry] = []
    seen_payload_hashes: set[str] = set()
    for ordinal, original in enumerate(entries):
        item = HarInventoryEntry(ordinal=ordinal)
        inventory.append(item)
        try:
            if not isinstance(original, dict):
                raise ValueError("entry is not an object")
            request = original.get("request")
            response = original.get("response")
            if not isinstance(request, dict) or not isinstance(response, dict):
                raise ValueError("entry request or response is not an object")
            method = request.get("method", "GET")
            url = request.get("url")
            if not isinstance(method, str) or not isinstance(url, str):
                raise ValueError("request method or URL is invalid")
            parts = urlsplit(url)
            item.method = method.upper()
            item.route_path = parts.path or "/"
            item.query_keys = sorted({key for key, _ in parse_qsl(parts.query, keep_blank_values=True)})
            if parts.hostname != allowed_host:
                item.skip_reason = "hostname_not_allowed"
                continue
            status = response.get("status")
            item.http_status = int(status) if status not in (None, "") else None
            content = response.get("content", {})
            if not isinstance(content, dict):
                raise ValueError("response content is not an object")
            mime_type = content.get("mimeType")
            item.content_type = str(mime_type) if mime_type else None
            encoding = content.get("encoding")
            item.response_body_encoding = str(encoding) if encoding else "plain"
            body = _body(content)
            item.bytes_uncompressed = len(body)
            item.payload_hash = hashlib.sha256(body).hexdigest()
            item.duplicate_payload = item.payload_hash in seen_payload_hashes
            seen_payload_hashes.add(item.payload_hash)
            label, details = _json_details(body, item.content_type)
            item.candidate_label = label
            if details:
                item.schema_fingerprint = details["schema_fingerprint"]
                item.top_level_kind = details["top_level_kind"]
                item.top_level_keys = details["top_level_keys"]
                item.candidate_collections = details["candidate_collections"]
            else:
                item.top_level_keys = []
                item.candidate_collections = []
            if not body:
                item.skip_reason = "empty_body"
                continue
            capture = archive.capture_bytes(
                body,
                source_code=source_code,
                endpoint_code="har_discovered",
                request_key=request_key_from_url(item.method, url),
                fetched_at=_parse_started_at(original.get("startedDateTime")),
                http_status=item.http_status,
                content_type=item.content_type,
                request_url=url,
                metadata={"har_entry_ordinal": ordinal, "import_mode": "har_inventory"},
            )
            item.raw_id = capture.raw_id
            item.observation_id = capture.observation_id
        except Exception as exc:  # each untrusted HAR entry is an independent failure boundary
            item.skip_reason = f"malformed_entry:{type(exc).__name__}"
    return {
        "schema_version": INVENTORY_SCHEMA_VERSION,
        "generated_at": _generated_at(),
        "allowed_host": allowed_host,
        "entries": [item.to_dict() for item in sorted(inventory, key=lambda value: value.ordinal)],
    }


def inspect_archived_payload(value: str, *, raw_root: Path) -> dict[str, Any]:
    root = raw_root.resolve()
    candidate = Path(value)
    if candidate.is_absolute():
        path = candidate.resolve()
    elif len(value) == 64 and all(char in "0123456789abcdefABCDEF" for char in value):
        matches = sorted(root.glob(f"**/{value.casefold()}.json.gz"))
        if not matches:
            raise FileNotFoundError("archived JSON payload hash not found")
        path = matches[0].resolve()
    else:
        path = (root / candidate).resolve()
    if not path.is_relative_to(root) or not path.is_file() or not path.name.endswith(".json.gz"):
        raise ValueError("payload must be a gzip JSON archive below raw-root")
    body = gzip.decompress(path.read_bytes())
    payload = json.loads(body)
    inspection = inspect_payload(payload)
    return {
        "payload_hash": hashlib.sha256(body).hexdigest(),
        "schema_fingerprint": inspection.schema_fingerprint,
        "top_level_kind": _json_kind(payload),
        "top_level_keys": sorted(str(key) for key in payload) if isinstance(payload, dict) else [],
        "candidate_collections": [asdict(candidate) for candidate in inspection.candidates],
        "bytes_uncompressed": len(body),
        "payload_path": path.relative_to(root).as_posix(),
    }
