from __future__ import annotations

import gzip
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class ArchivedPublicApiCapture:
    raw_id: str
    observation_id: str
    source_code: str
    endpoint_code: str
    fetched_at: str
    query_keys: tuple[str, ...]
    query_values: tuple[tuple[str, str], ...]
    payload: Mapping[str, Any]

    def query_value_mapping(self) -> dict[str, str]:
        return dict(self.query_values)


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def load_latest_public_api_capture(
    raw_root: Path,
    *,
    source_code: str,
    endpoint_code: str,
) -> ArchivedPublicApiCapture:
    """Load one private archived capture together with its request provenance."""
    pattern = (
        f"source={source_code}/year=*/month=*/endpoint={endpoint_code}/observations/*.json"
    )
    candidates: list[tuple[str, str, Path, Mapping[str, Any]]] = []
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
            (fetched_at, manifest_path.as_posix(), Path(content_manifest_path), manifest)
        )
    if not candidates:
        raise FileNotFoundError(
            f"no archived observation for source={source_code!r}, endpoint={endpoint_code!r}"
        )

    fetched_at, _manifest_name, content_manifest_relative, manifest = max(candidates)
    content_manifest = _mapping(
        json.loads((raw_root / content_manifest_relative).read_text(encoding="utf-8")),
        "raw content manifest",
    )
    raw_id = content_manifest.get("raw_id")
    payload_path = content_manifest.get("payload_path")
    if not isinstance(raw_id, str) or not raw_id:
        raise ValueError("raw content manifest is missing raw_id")
    if not isinstance(payload_path, str) or not payload_path:
        raise ValueError("raw content manifest is missing payload_path")
    if content_manifest.get("source_code") != source_code:
        raise ValueError("raw content manifest source_code does not match requested source")
    if content_manifest.get("endpoint_code") != endpoint_code:
        raise ValueError("raw content manifest endpoint_code does not match requested endpoint")

    observation_id = manifest.get("observation_id")
    if not isinstance(observation_id, str) or not observation_id:
        raise ValueError("raw observation manifest is missing observation_id")
    if manifest.get("raw_id") != raw_id:
        raise ValueError("raw observation manifest raw_id does not match content manifest")

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
        payload = _mapping(json.loads(stream.read()), "archived public API payload")

    return ArchivedPublicApiCapture(
        raw_id=raw_id,
        observation_id=observation_id,
        source_code=source_code,
        endpoint_code=endpoint_code,
        fetched_at=fetched_at,
        query_keys=tuple(raw_query_keys),
        query_values=tuple(query_values),
        payload=payload,
    )


__all__ = ["ArchivedPublicApiCapture", "load_latest_public_api_capture"]
