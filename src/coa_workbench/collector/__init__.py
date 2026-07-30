from . import armory_capture as _armory_capture
from .archive_reuse import capture_asset_with_archive_fallback
from .armory_api_capture import (
    ArmoryApiCaptureResult,
    ArmoryApiObservation,
    armory_api_capture_to_dict,
    capture_armory_api,
)
from .armory_capture import (
    BuildPageCapture,
    EmbeddedJsonCapture,
    build_armory_url,
    build_character_url,
    build_page_capture_to_dict,
    capture_character_build_pages,
)
from .armory_endpoint_capture import (
    ARMORY_ENDPOINT_KINDS,
    ArmoryEndpointCaptureResult,
    capture_armory_endpoint,
    capture_armory_endpoints_progressively,
)
from .combatants_candidate_extraction import extract_observed_combatants_info_candidates
from .combatants_candidate_promotion import promote_observed_combatants_info_candidates
from .combatants_info_field_selection import select_observed_combatants_info_fields
from .combatants_mapping_design import design_observed_combatants_info_mappings
from .combatants_scope_review import build_observed_combatants_info_deep_scope_review
from .guild_report_collection_contract import build_guild_report_collection_contract
from .har_inventory import inspect_archived_payload, inventory_har
from .http_profile import (
    COA_FETCH_CONTEXT_V1,
    FETCH_CONTEXT_PROFILE_VERSION,
    HttpRequestProfile,
    SameOriginHttpSession,
)
from .http_read import read_response_resilient
from .probe import ProbeResult, probe_registry_route, probe_result_to_dict
from .public_report_manifest import capture_public_report_manifest
from .raw_archive import (
    RawArchive,
    RawCapture,
    capture_to_dict,
    request_key_from_url,
    sanitize_url,
    schema_fingerprint,
)
from .report_discovery import (
    REPORT_DISCOVERY_DEFAULT_LIMIT,
    REPORT_DISCOVERY_MAX_LIMIT,
    REPORTS_PUBLIC_ROUTE,
    ReportDiscoveryCapture,
    capture_public_report_discovery,
    report_discovery_capture_to_dict,
)
from .report_discovery_mapping_review import build_report_discovery_mapping_review
from .report_discovery_mapping_summary import summarize_report_discovery_mapping_review
from .report_discovery_mapping_text import render_report_discovery_mapping_summary_text
from .report_discovery_review import review_report_discovery_capture
from .report_pagination_boundary_probe import capture_report_pagination_boundary_probe
from .report_pagination_evidence import capture_bounded_report_pagination_evidence
from .report_pagination_semantic_review import review_report_pagination_semantics
from .report_pagination_terminal_search import capture_report_pagination_terminal_search
from .report_slice_capture import (
    COMBATANTS_INFO_ROUTE_SHAPE,
    ENCOUNTER_DETAIL_ROUTE_SHAPE,
    OBSERVED_REPORT_SLICE_ROUTE_SHAPES,
    REPORT_DETAIL_ROUTE_SHAPE,
    ObservedReportSliceCaptureResult,
    ReportSliceEndpointCapture,
    capture_observed_report_slice,
    observed_report_slice_capture_to_dict,
)
from .report_slice_field_selection import select_observed_report_slice_fields
from .report_slice_mapping_promotion import promote_observed_report_slice_candidate_mappings
from .report_slice_mapping_publication import publish_observed_report_slice_mappings
from .report_slice_mapping_review import build_observed_report_slice_mapping_review
from .report_slice_mapping_summary import summarize_observed_report_slice_mapping_review
from .report_slice_mapping_validation import (
    validate_observed_report_slice_candidate_mappings,
)
from .report_slice_normalization import normalize_observed_report_slice_selected_parser_mappings
from .report_slice_reconstruction import reconstruct_observed_report_slice
from .report_slice_review import review_observed_report_slice_capture
from .report_slice_scope_review import build_observed_report_slice_scope_review
from .route_discovery import discover_api_route_candidates
from .source_registry import (
    SourceRegistry,
    SourceRoute,
    UnverifiedSourceRouteError,
    load_source_registry,
)
from .spa_route_inventory import build_spa_route_inventory, normalize_api_route_shape

_armory_capture._api_route_candidates = discover_api_route_candidates
_armory_capture._read_response = read_response_resilient
_armory_capture._capture_asset = capture_asset_with_archive_fallback

__all__ = [
    "ARMORY_ENDPOINT_KINDS",
    "ArmoryApiCaptureResult",
    "ArmoryApiObservation",
    "ArmoryEndpointCaptureResult",
    "BuildPageCapture",
    "COA_FETCH_CONTEXT_V1",
    "COMBATANTS_INFO_ROUTE_SHAPE",
    "ENCOUNTER_DETAIL_ROUTE_SHAPE",
    "EmbeddedJsonCapture",
    "FETCH_CONTEXT_PROFILE_VERSION",
    "HttpRequestProfile",
    "OBSERVED_REPORT_SLICE_ROUTE_SHAPES",
    "ObservedReportSliceCaptureResult",
    "ProbeResult",
    "REPORTS_PUBLIC_ROUTE",
    "REPORT_DETAIL_ROUTE_SHAPE",
    "REPORT_DISCOVERY_DEFAULT_LIMIT",
    "REPORT_DISCOVERY_MAX_LIMIT",
    "RawArchive",
    "RawCapture",
    "ReportDiscoveryCapture",
    "ReportSliceEndpointCapture",
    "SameOriginHttpSession",
    "SourceRegistry",
    "SourceRoute",
    "UnverifiedSourceRouteError",
    "armory_api_capture_to_dict",
    "build_armory_url",
    "build_character_url",
    "build_guild_report_collection_contract",
    "build_observed_combatants_info_deep_scope_review",
    "build_observed_report_slice_mapping_review",
    "build_observed_report_slice_scope_review",
    "build_page_capture_to_dict",
    "build_report_discovery_mapping_review",
    "build_spa_route_inventory",
    "capture_armory_api",
    "capture_armory_endpoint",
    "capture_armory_endpoints_progressively",
    "capture_asset_with_archive_fallback",
    "capture_bounded_report_pagination_evidence",
    "capture_character_build_pages",
    "capture_observed_report_slice",
    "capture_public_report_discovery",
    "capture_public_report_manifest",
    "capture_report_pagination_boundary_probe",
    "capture_report_pagination_terminal_search",
    "capture_to_dict",
    "design_observed_combatants_info_mappings",
    "discover_api_route_candidates",
    "extract_observed_combatants_info_candidates",
    "inspect_archived_payload",
    "inventory_har",
    "load_source_registry",
    "normalize_api_route_shape",
    "normalize_observed_report_slice_selected_parser_mappings",
    "observed_report_slice_capture_to_dict",
    "probe_registry_route",
    "probe_result_to_dict",
    "promote_observed_combatants_info_candidates",
    "promote_observed_report_slice_candidate_mappings",
    "publish_observed_report_slice_mappings",
    "read_response_resilient",
    "reconstruct_observed_report_slice",
    "render_report_discovery_mapping_summary_text",
    "report_discovery_capture_to_dict",
    "request_key_from_url",
    "review_observed_report_slice_capture",
    "review_report_discovery_capture",
    "review_report_pagination_semantics",
    "sanitize_url",
    "schema_fingerprint",
    "select_observed_combatants_info_fields",
    "select_observed_report_slice_fields",
    "summarize_observed_report_slice_mapping_review",
    "summarize_report_discovery_mapping_summary_text",
    "validate_observed_report_slice_candidate_mappings",
]
