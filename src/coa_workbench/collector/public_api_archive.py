from __future__ import annotations

import gzip
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from coa_workbench.collector.raw_archive import RawCapture


@dataclass(frozen=True, slots=True)
class ArchivedPublicApiCapture:
    raw_id: str
    observation_id: str
    source_code: str
    endpoint_code: str
    fetched_at: str
    request_key: str
    payload_hash: str
    payload_path: str
    manifest_path: str
    bytes_uncompressed: int
    content_type: str | None
    schema_fingerprint: str | None
    http_status: int | None
    query_keys: tuple[str, ...]
    query_values: tuple[tuple[str, str], ...]
    payload_bytes: bytes
    payload: Mapping[str, Any]

    def query_value_mapping(self) -> dict[str, str]:
        return dict(self.query_values)

    def as_raw_capture(self, raw_root: Path) -> RawCapture:
        """Rebuild the immutable capture handle for local replay/observability work.

        Duplicate flags are acquisition-time facts and are not persisted in the manifests. They are
        deliberately reconstructed as False because Source Observatory does not use them as source
        semantics.
        """
        return RawCapture(
            raw_id=self.raw_id,
            observation_id=self.observation_id,
            source_code=self.source_code,
            endpoint_code=self.endpoint_code,
            request_key=self.request_key,
            payload_hash=self.payload_hash,
            payload_path=str(raw_root / self.payload_path),
            manifest_path=str(raw_root / self.manifest_path),
            duplicate_payload=False,
            duplicate_observation=False,
            bytes_uncompressed=self.bytes_uncompressed,
            content_type=self.content_type,
            schema_fingerprint=self.schema_fingerprint,
            fetched_at=self.fetched_at,
            http_status=self.http_status,
        )


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _required_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _optional_string(value: Any, label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be null or a non-empty string")
    return value


def _request_identity(
    manifest: Mapping[str, Any],
    content_manifest: Mapping[str, Any],
) -> tuple[str, str]:
    """Resolve request identity from the observation, with strict schema-v1 fallback.

    RawArchive schema-v2 content manifests are content-scoped and intentionally contain no
    request-specific values. Existing local schema-v1 content manifests remain readable: when the
    observation predates ``request_key`` storage, both legacy ``raw_id`` and ``request_key`` must
    agree with that same observation before the fallback is accepted.
    """
    raw_id = _required_string(manifest.get("raw_id"), "raw observation manifest raw_id")
    observation_request_key = manifest.get("request_key")
    if observation_request_key is not None:
        return raw_id, _required_string(
            observation_request_key,
            "raw observation manifest request_key",
        )

    legacy_raw_id = content_manifest.get("raw_id")
    legacy_request_key = content_manifest.get("request_key")
    if legacy_raw_id != raw_id:
        raise ValueError(
            "legacy raw content manifest raw_id does not match observation; request identity "
            "cannot be reconstructed safely"
        )
    return raw_id, _required_string(
        legacy_request_key,
        "legacy raw content manifest request_key",
    )


def load_latest_public_api_capture(
    raw_root: Path,
    *,
    source_code: str,
    endpoint_code: str,
) -> ArchivedPublicApiCapture:
    """Load one private archived capture together with request and raw-object provenance."""
    pattern = f"source={source_code}/year=*/month=*/endpoint={endpoint_code}/observations/*.json"
    candidates: list[tuple[str, str, Path, Path, Mapping[str, Any]]] = []
    for manifest_path in raw_root.glob(pattern):
        manifest = _mapping(
            json.loads(manifest_path.read_text(encoding="utf-8")),
            "raw observation manifest",
        )
        fetched_at = manifest.get("fetched_at")
        content_manifest_path = manifest.get("content_manifest_path")
        if not isinstance(fetched_at, str) or not fetched_at:
            continue
        if not isinstance(content_manifest_path, str) or not content_manifest_path:
            continue
        candidates.append(
            (
                fetched_at,
                manifest_path.as_posix(),
                manifest_path,
                Path(content_manifest_path),
                manifest,
            )
        )
    if not candidates:
        raise FileNotFoundError(
            f"no archived observation for source={source_code!r}, endpoint={endpoint_code!r}"
        )

    fetched_at, _manifest_name, manifest_path, content_manifest_relative, manifest = max(candidates)
    content_manifest = _mapping(
        json.loads((raw_root / content_manifest_relative).read_text(encoding="utf-8")),
        "raw content manifest",
    )
    raw_id, request_key = _request_identity(manifest, content_manifest)
    payload_path = _required_string(
        content_manifest.get("payload_path"),
        "raw content manifest payload_path",
    )
    payload_hash = _required_string(
        content_manifest.get("payload_hash"),
        "raw content manifest payload_hash",
    )
    if content_manifest.get("source_code") != source_code:
        raise ValueError("raw content manifest source_code does not match requested source")
    if content_manifest.get("endpoint_code") != endpoint_code:
        raise ValueError("raw content manifest endpoint_code does not match requested endpoint")

    bytes_uncompressed = content_manifest.get("bytes_uncompressed")
    if not isinstance(bytes_uncompressed, int) or isinstance(bytes_uncompressed, bool):
        raise ValueError("raw content manifest bytes_uncompressed must be an integer")
    content_type = _optional_string(
        content_manifest.get("content_type"),
        "raw content manifest content_type",
    )
    schema_fingerprint = _optional_string(
        content_manifest.get("schema_fingerprint"),
        "raw content manifest schema_fingerprint",
    )

    observation_id = _required_string(
        manifest.get("observation_id"),
        "raw observation manifest observation_id",
    )
    http_status = manifest.get("http_status")
    if http_status is not None and (
        not isinstance(http_status, int) or isinstance(http_status, bool)
    ):
        raise ValueError("raw observation http_status must be null or an integer")

    metadata = _mapping(manifest.get("metadata", {}), "raw observation metadata")
    raw_query_keys = metadata.get("query_keys", [])
    if not isinstance(raw_query_keys, list) or not all(
        isinstance(key, str) and key for key in raw_query_keys
    ):
        raise ValueError("raw observation query_keys must be an array of non-empty strings")
    private_query_values = metadata.get("private_query_values", {})
    if private_query_values is None:
        private_query_values = {}
    if not isinstance(private_query_values, dict):
        raise ValueError("raw observation private_query_values must be an object")
    query_values: list[tuple[str, str]] = []
    for key in raw_query_keys:
        if key not in private_query_values:
            continue
        value = private_query_values[key]
        if not isinstance(value, str) or not value:
            raise ValueError("raw observation private query values must be non-empty strings")
        query_values.append((key, value))

    with gzip.open(raw_root / payload_path, "rb") as stream:
        payload_bytes = stream.read()
    if len(payload_bytes) != bytes_uncompressed:
        raise ValueError("archived public API payload length does not match content manifest")
    payload = _mapping(json.loads(payload_bytes), "archived public API payload")

    return ArchivedPublicApiCapture(
        raw_id=raw_id,
        observation_id=observation_id,
        source_code=source_code,
        endpoint_code=endpoint_code,
        fetched_at=fetched_at,
        request_key=request_key,
        payload_hash=payload_hash,
        payload_path=payload_path,
        manifest_path=manifest_path.relative_to(raw_root).as_posix(),
        bytes_uncompressed=bytes_uncompressed,
        content_type=content_type,
        schema_fingerprint=schema_fingerprint,
        http_status=http_status,
        query_keys=tuple(raw_query_keys),
        query_values=tuple(query_values),
        payload_bytes=payload_bytes,
        payload=payload,
    )


__all__ = ["ArchivedPublicApiCapture", "load_latest_public_api_capture"]
