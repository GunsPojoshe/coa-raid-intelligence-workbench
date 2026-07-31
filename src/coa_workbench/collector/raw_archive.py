from __future__ import annotations

import base64
import gzip
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qsl, urlsplit, urlunsplit

from coa_workbench.storage.migrations import apply_migrations

SENSITIVE_QUERY_KEYS = {
    "access_token",
    "api_key",
    "apikey",
    "authorization",
    "code",
    "key",
    "session",
    "signature",
    "sig",
    "token",
}


def _utc(value: datetime | None = None) -> datetime:
    current = value or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current.astimezone(timezone.utc)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _safe_segment(value: str) -> str:
    prepared = "".join(char if char.isalnum() or char in "-_" else "_" for char in value)
    prepared = prepared.strip("_")
    if not prepared:
        raise ValueError("archive path segment cannot be empty")
    return prepared[:120]


def sanitize_url(url: str) -> str:
    """Keep route shape and query keys without persisting credentials or identifiers."""
    parts = urlsplit(url)
    query = []
    for key, _value in parse_qsl(parts.query, keep_blank_values=True):
        replacement = "<redacted>" if key.casefold() in SENSITIVE_QUERY_KEYS else "<value>"
        query.append(f"{key}={replacement}")
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "&".join(query), ""))


def request_key_from_url(method: str, url: str) -> str:
    parts = urlsplit(url)
    query_keys = sorted(key for key, _ in parse_qsl(parts.query, keep_blank_values=True))
    identity_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    suffix = f"?keys={','.join(query_keys)}" if query_keys else ""
    return f"{method.upper()}:{parts.path or '/'}{suffix}#{identity_hash}"


def schema_fingerprint(payload: bytes, content_type: str | None) -> str | None:
    if not content_type or "json" not in content_type.casefold():
        return None
    try:
        value = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None

    def shape(item: Any) -> Any:
        if isinstance(item, dict):
            return {key: shape(item[key]) for key in sorted(item)}
        if isinstance(item, list):
            unique = []
            for child in item[:25]:
                candidate = shape(child)
                if candidate not in unique:
                    unique.append(candidate)
            return {"list": unique}
        if item is None:
            return "null"
        if isinstance(item, bool):
            return "bool"
        if isinstance(item, int):
            return "int"
        if isinstance(item, float):
            return "float"
        return "str"

    encoded = json.dumps(shape(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class RawCapture:
    raw_id: str
    observation_id: str
    source_code: str
    endpoint_code: str
    request_key: str
    payload_hash: str
    payload_path: str
    manifest_path: str
    duplicate_payload: bool
    duplicate_observation: bool
    bytes_uncompressed: int
    content_type: str | None
    schema_fingerprint: str | None
    fetched_at: str
    http_status: int | None


class RawArchive:
    def __init__(
        self,
        root: Path,
        *,
        database_path: Path | None = None,
        migrations_dir: Path | None = None,
    ) -> None:
        self.root = root
        self.database_path = database_path
        self.migrations_dir = migrations_dir

    def capture_bytes(
        self,
        payload: bytes,
        *,
        source_code: str,
        endpoint_code: str,
        request_key: str,
        fetched_at: datetime | None = None,
        http_status: int | None = None,
        content_type: str | None = None,
        request_url: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RawCapture:
        observed_at = _utc(fetched_at)
        observed_at_text = observed_at.isoformat().replace("+00:00", "Z")
        payload_hash = _sha256_bytes(payload)
        raw_id = hashlib.sha256(
            f"{source_code}\0{endpoint_code}\0{request_key}\0{payload_hash}".encode("utf-8")
        ).hexdigest()
        sanitized_url = sanitize_url(request_url) if request_url else None
        observation_seed = json.dumps(
            {
                "raw_id": raw_id,
                "fetched_at": observed_at_text,
                "http_status": http_status,
                "request_url": sanitized_url,
                "metadata": metadata or {},
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        observation_id = hashlib.sha256(observation_seed.encode("utf-8")).hexdigest()
        folder = (
            self.root
            / f"source={_safe_segment(source_code)}"
            / f"year={observed_at:%Y}"
            / f"month={observed_at:%m}"
            / f"endpoint={_safe_segment(endpoint_code)}"
        )
        folder.mkdir(parents=True, exist_ok=True)
        extension = "json.gz" if content_type and "json" in content_type.casefold() else "bin.gz"
        payload_path = folder / f"{payload_hash}.{extension}"
        content_manifest_path = folder / f"{payload_hash}.content.json"
        observation_dir = folder / "observations"
        observation_dir.mkdir(exist_ok=True)
        observation_path = observation_dir / f"{observed_at:%Y%m%dT%H%M%S}_{observation_id[:16]}.json"
        duplicate_payload = payload_path.exists()
        duplicate_observation = observation_path.exists()
        if not payload_path.exists():
            with payload_path.open("wb") as stream:
                with gzip.GzipFile(fileobj=stream, mode="wb", mtime=0) as compressed:
                    compressed.write(payload)
        fingerprint = schema_fingerprint(payload, content_type)
        content_manifest = {
            "schema_version": 1,
            "raw_id": raw_id,
            "source_code": source_code,
            "endpoint_code": endpoint_code,
            "request_key": request_key,
            "payload_hash": payload_hash,
            "payload_path": payload_path.relative_to(self.root).as_posix(),
            "compression": "gzip",
            "bytes_uncompressed": len(payload),
            "content_type": content_type,
            "schema_fingerprint": fingerprint,
        }
        if content_manifest_path.exists():
            existing = json.loads(content_manifest_path.read_text(encoding="utf-8"))
            if existing != content_manifest:
                raise RuntimeError(f"raw content manifest collision: {content_manifest_path}")
        else:
            content_manifest_path.write_text(
                json.dumps(content_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        observation_manifest = {
            "schema_version": 1,
            "observation_id": observation_id,
            "raw_id": raw_id,
            "fetched_at": observed_at_text,
            "http_status": http_status,
            "request_url": sanitized_url,
            "metadata": metadata or {},
            "content_manifest_path": content_manifest_path.relative_to(self.root).as_posix(),
        }
        if observation_path.exists():
            existing = json.loads(observation_path.read_text(encoding="utf-8"))
            if existing != observation_manifest:
                raise RuntimeError(f"raw observation manifest collision: {observation_path}")
        else:
            observation_path.write_text(
                json.dumps(observation_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        capture = RawCapture(
            raw_id=raw_id,
            observation_id=observation_id,
            source_code=source_code,
            endpoint_code=endpoint_code,
            request_key=request_key,
            payload_hash=payload_hash,
            payload_path=str(payload_path),
            manifest_path=str(observation_path),
            duplicate_payload=duplicate_payload,
            duplicate_observation=duplicate_observation,
            bytes_uncompressed=len(payload),
            content_type=content_type,
            schema_fingerprint=fingerprint,
            fetched_at=observed_at_text,
            http_status=http_status,
        )
        self._register(capture, content_manifest, observation_manifest)
        return capture

    def capture_file(
        self,
        path: Path,
        *,
        source_code: str,
        endpoint_code: str,
        request_key: str | None = None,
        content_type: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RawCapture:
        if not path.is_file():
            raise FileNotFoundError(path)
        guessed = content_type or (
            "application/json" if path.suffix.casefold() == ".json" else "application/octet-stream"
        )
        return self.capture_bytes(
            path.read_bytes(),
            source_code=source_code,
            endpoint_code=endpoint_code,
            request_key=request_key or f"file:{path.name}",
            content_type=guessed,
            metadata={"import_path": str(path), **(metadata or {})},
        )

    def import_har(
        self,
        path: Path,
        *,
        source_code: str,
        allowed_host: str,
        endpoint_code: str = "har_discovered",
    ) -> list[RawCapture]:
        payload = json.loads(path.read_text(encoding="utf-8"))
        entries: Iterable[dict[str, Any]] = payload.get("log", {}).get("entries", [])
        captures: list[RawCapture] = []
        for entry in entries:
            request = entry.get("request", {})
            response = entry.get("response", {})
            url = str(request.get("url", ""))
            if urlsplit(url).hostname != allowed_host:
                continue
            content = response.get("content", {})
            text = content.get("text")
            if text is None:
                continue
            body = (
                base64.b64decode(text)
                if content.get("encoding") == "base64"
                else str(text).encode("utf-8")
            )
            captures.append(
                self.capture_bytes(
                    body,
                    source_code=source_code,
                    endpoint_code=endpoint_code,
                    request_key=request_key_from_url(str(request.get("method", "GET")), url),
                    http_status=int(response.get("status") or 0),
                    content_type=content.get("mimeType") or None,
                    request_url=url,
                    metadata={
                        "har_file": str(path),
                        "startedDateTime": entry.get("startedDateTime"),
                        "response_header_names": sorted(
                            header.get("name")
                            for header in response.get("headers", [])
                            if header.get("name")
                        ),
                    },
                )
            )
        return captures

    def _register(
        self,
        capture: RawCapture,
        content_manifest: dict[str, Any],
        observation_manifest: dict[str, Any],
    ) -> None:
        if not self.database_path:
            return
        if self.migrations_dir:
            apply_migrations(self.database_path, self.migrations_dir)
        import duckdb

        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with duckdb.connect(str(self.database_path)) as connection:
            connection.execute(
                """
                INSERT INTO raw_object (
                    raw_id, endpoint_id, request_key, payload_hash, storage_path,
                    fetched_at, http_status, normalizer_status, metadata_json
                ) SELECT ?, NULL, ?, ?, ?, ?, ?, 'pending', ?
                WHERE NOT EXISTS (
                    SELECT 1 FROM raw_object WHERE request_key = ? AND payload_hash = ?
                )
                """,
                [
                    capture.raw_id,
                    capture.request_key,
                    capture.payload_hash,
                    content_manifest["payload_path"],
                    capture.fetched_at,
                    capture.http_status,
                    json.dumps(content_manifest, ensure_ascii=False, sort_keys=True),
                    capture.request_key,
                    capture.payload_hash,
                ],
            )
            connection.execute(
                """
                INSERT INTO raw_fetch_observation (
                    observation_id, raw_id, fetched_at, http_status,
                    request_url_sanitized, metadata_json
                ) SELECT ?, ?, ?, ?, ?, ?
                WHERE NOT EXISTS (
                    SELECT 1 FROM raw_fetch_observation WHERE observation_id = ?
                )
                """,
                [
                    capture.observation_id,
                    capture.raw_id,
                    capture.fetched_at,
                    capture.http_status,
                    observation_manifest["request_url"],
                    json.dumps(observation_manifest, ensure_ascii=False, sort_keys=True),
                    capture.observation_id,
                ],
            )


def capture_to_dict(capture: RawCapture) -> dict[str, Any]:
    return asdict(capture)
