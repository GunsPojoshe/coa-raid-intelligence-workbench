from . import armory_capture as _armory_capture
from .archive_reuse import capture_asset_with_archive_fallback
from .armory_capture import (
    BuildPageCapture,
    EmbeddedJsonCapture,
    build_armory_url,
    build_character_url,
    build_page_capture_to_dict,
    capture_character_build_pages,
)
from .har_inventory import inspect_archived_payload, inventory_har
from .http_read import read_response_resilient
from .probe import ProbeResult, probe_registry_route, probe_result_to_dict
from .raw_archive import (
    RawArchive,
    RawCapture,
    capture_to_dict,
    request_key_from_url,
    sanitize_url,
    schema_fingerprint,
)
from .route_discovery import discover_api_route_candidates
from .source_registry import (
    SourceRegistry,
    SourceRoute,
    UnverifiedSourceRouteError,
    load_source_registry,
)

_armory_capture._api_route_candidates = discover_api_route_candidates
_armory_capture._read_response = read_response_resilient
_armory_capture._capture_asset = capture_asset_with_archive_fallback

__all__ = [
    "BuildPageCapture",
    "EmbeddedJsonCapture",
    "ProbeResult",
    "RawArchive",
    "RawCapture",
    "SourceRegistry",
    "SourceRoute",
    "UnverifiedSourceRouteError",
    "build_armory_url",
    "build_character_url",
    "build_page_capture_to_dict",
    "capture_asset_with_archive_fallback",
    "capture_character_build_pages",
    "capture_to_dict",
    "discover_api_route_candidates",
    "inspect_archived_payload",
    "inventory_har",
    "load_source_registry",
    "probe_registry_route",
    "probe_result_to_dict",
    "read_response_resilient",
    "request_key_from_url",
    "sanitize_url",
    "schema_fingerprint",
]
