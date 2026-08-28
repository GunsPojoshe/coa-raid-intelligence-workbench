from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qsl, urlsplit

from coa_workbench.collector.json_structure import json_structure_fingerprint
from coa_workbench.collector.spa_route_inventory import normalize_api_route_shape

NETWORK_OBSERVATION_VERSION = "network-observation-v1"


def _json_request_keys(body: bytes | None) -> tuple[str, ...]:
    if body is None:
        return ()
    try:
        value = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return ()
    if not isinstance(value, dict):
        return ()
    return tuple(sorted(str(key) for key in value))


def _response_structure_fingerprint(body: bytes | None) -> str | None:
    if body is None:
        return None
    try:
        value: Any = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return json_structure_fingerprint(value)


@dataclass(frozen=True, slots=True)
class NetworkObservation:
    """Provider-neutral private network observation.

    Concrete URLs and bodies are intentionally retained only in the private in-memory/local model.
    Callers that need a public artifact must use ``public_summary``.
    """

    ordinal: int
    observed_at: str
    method: str
    url: str
    status: int | None
    request_content_type: str | None = None
    response_content_type: str | None = None
    request_body: bytes | None = None
    response_body: bytes | None = None
    resource_type: str | None = None
    source_kind: str = "unknown"

    @property
    def path(self) -> str:
        return urlsplit(self.url).path

    @property
    def query_keys(self) -> tuple[str, ...]:
        return tuple(
            sorted({key for key, _ in parse_qsl(urlsplit(self.url).query, keep_blank_values=True)})
        )

    @property
    def request_body_keys(self) -> tuple[str, ...]:
        return _json_request_keys(self.request_body)

    @property
    def route_shape(self) -> str:
        path = normalize_api_route_shape(self.path)
        if not self.query_keys:
            return path
        query = "&".join(f"{key}=<value>" for key in self.query_keys)
        return f"{path}?{query}"

    @property
    def response_structure_fingerprint(self) -> str | None:
        return _response_structure_fingerprint(self.response_body)

    def public_summary(self) -> dict[str, object]:
        return {
            "observation_version": NETWORK_OBSERVATION_VERSION,
            "ordinal": self.ordinal,
            "observed_at": self.observed_at,
            "method": self.method,
            "route_shape": self.route_shape,
            "query_keys": list(self.query_keys),
            "request_body_keys": list(self.request_body_keys),
            "status": self.status,
            "request_content_type": self.request_content_type,
            "response_content_type": self.response_content_type,
            "resource_type": self.resource_type,
            "source_kind": self.source_kind,
            "response_structure_fingerprint": self.response_structure_fingerprint,
            "privacy": {
                "url_included": False,
                "query_values_included": False,
                "request_body_included": False,
                "response_body_included": False,
                "headers_included": False,
                "cookies_included": False,
            },
        }


__all__ = ["NETWORK_OBSERVATION_VERSION", "NetworkObservation"]
