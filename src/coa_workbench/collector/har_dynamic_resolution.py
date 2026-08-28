from __future__ import annotations

import json
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping
from urllib.parse import urlsplit

from coa_workbench.collector.raw_archive import RawArchive
from coa_workbench.collector.source_acquisition import (
    SourceAcquisitionObservation,
    observe_reviewed_har,
)
from coa_workbench.collector.source_observatory import ReviewedGetContract

_PLACEHOLDER_SEGMENT = re.compile(r"^\{([A-Za-z_][A-Za-z0-9_]*)\}$")


@dataclass(frozen=True, slots=True)
class ResolvedDynamicRoute:
    endpoint_code: str
    concrete_paths: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DynamicHarResolution:
    resolver_version: str
    routes: tuple[ResolvedDynamicRoute, ...]
    candidate_concrete_path_count: int
    rejected_static_collision_count: int
    rejected_uncorroborated_candidate_count: int

    @property
    def resolved_endpoint_codes(self) -> tuple[str, ...]:
        return tuple(route.endpoint_code for route in self.routes)

    @property
    def resolved_concrete_path_count(self) -> int:
        return sum(len(route.concrete_paths) for route in self.routes)

    def paths_for(self, endpoint_code: str) -> tuple[str, ...]:
        for route in self.routes:
            if route.endpoint_code == endpoint_code:
                return route.concrete_paths
        return ()

    def public_summary(self) -> dict[str, object]:
        return {
            "resolver_version": self.resolver_version,
            "strategy": "cross_contract_parameter_corroboration_plus_static_route_exclusion",
            "generic_dynamic_ingestion_allowed": False,
            "resolved_endpoint_codes": list(self.resolved_endpoint_codes),
            "resolved_route_count": len(self.routes),
            "resolved_concrete_path_count": self.resolved_concrete_path_count,
            "candidate_concrete_path_count": self.candidate_concrete_path_count,
            "rejected_static_collision_count": self.rejected_static_collision_count,
            "rejected_uncorroborated_candidate_count": (
                self.rejected_uncorroborated_candidate_count
            ),
            "concrete_path_values_included": False,
            "path_parameter_values_included": False,
        }


@dataclass(frozen=True, slots=True)
class _DynamicCandidate:
    endpoint_code: str
    concrete_path: str
    bindings: tuple[tuple[str, str], ...]


def _template_bindings(route_template: str, concrete_path: str) -> dict[str, str] | None:
    template_segments = route_template.split("/")
    concrete_segments = concrete_path.split("/")
    if len(template_segments) != len(concrete_segments):
        return None

    bindings: dict[str, str] = {}
    for template_segment, concrete_segment in zip(
        template_segments,
        concrete_segments,
        strict=True,
    ):
        placeholder = _PLACEHOLDER_SEGMENT.fullmatch(template_segment)
        if placeholder:
            if not concrete_segment:
                return None
            name = placeholder.group(1)
            if name in bindings and bindings[name] != concrete_segment:
                return None
            bindings[name] = concrete_segment
            continue
        if "{" in template_segment or "}" in template_segment:
            return None
        if template_segment != concrete_segment:
            return None
    return bindings if bindings else None


def _har_get_paths(path: Path, *, allowed_host: str) -> tuple[str, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    log = payload.get("log", {})
    if not isinstance(log, dict):
        raise ValueError("HAR log must be an object")
    entries = log.get("entries", [])
    if not isinstance(entries, list):
        raise ValueError("HAR log.entries must be an array")

    paths: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        request = entry.get("request", {})
        if not isinstance(request, dict):
            continue
        if str(request.get("method", "")).upper() != "GET":
            continue
        parts = urlsplit(str(request.get("url", "")))
        if parts.scheme != "https" or parts.hostname != allowed_host:
            continue
        paths.add(parts.path)
    return tuple(sorted(paths))


def resolve_correlated_dynamic_har_routes(
    path: Path,
    *,
    allowed_host: str,
    dynamic_route_templates: Mapping[str, str],
    static_paths: Iterable[str],
    min_endpoint_corroboration: int = 2,
) -> DynamicHarResolution:
    """Resolve dynamic HAR paths without guessing identifier formats.

    A dynamic candidate is eligible only when at least one placeholder binding is observed under
    multiple reviewed endpoint contracts. Exact known static paths are always excluded first.
    Concrete path and identifier values remain local-only and are omitted from public summaries.
    """
    if min_endpoint_corroboration < 2:
        raise ValueError("min_endpoint_corroboration must be at least 2")

    templates = {
        str(endpoint_code): str(route_template)
        for endpoint_code, route_template in dynamic_route_templates.items()
        if str(endpoint_code) and str(route_template)
    }
    if len(set(templates.values())) != len(templates):
        raise ValueError("dynamic route templates must be structurally unique")

    known_static_paths = {str(value) for value in static_paths if str(value)}
    candidates: list[_DynamicCandidate] = []
    rejected_static = 0

    for concrete_path in _har_get_paths(path, allowed_host=allowed_host):
        if concrete_path in known_static_paths:
            for route_template in templates.values():
                if _template_bindings(route_template, concrete_path) is not None:
                    rejected_static += 1
            continue
        for endpoint_code, route_template in templates.items():
            bindings = _template_bindings(route_template, concrete_path)
            if bindings is None:
                continue
            candidates.append(
                _DynamicCandidate(
                    endpoint_code=endpoint_code,
                    concrete_path=concrete_path,
                    bindings=tuple(sorted(bindings.items())),
                )
            )

    binding_endpoints: dict[tuple[str, str], set[str]] = {}
    for candidate in candidates:
        for binding in candidate.bindings:
            binding_endpoints.setdefault(binding, set()).add(candidate.endpoint_code)

    accepted: dict[str, set[str]] = {}
    rejected_uncorroborated = 0
    for candidate in candidates:
        corroborated = any(
            len(binding_endpoints[binding]) >= min_endpoint_corroboration
            for binding in candidate.bindings
        )
        if not corroborated:
            rejected_uncorroborated += 1
            continue
        accepted.setdefault(candidate.endpoint_code, set()).add(candidate.concrete_path)

    routes = tuple(
        ResolvedDynamicRoute(
            endpoint_code=endpoint_code,
            concrete_paths=tuple(sorted(concrete_paths)),
        )
        for endpoint_code, concrete_paths in sorted(accepted.items())
    )
    return DynamicHarResolution(
        resolver_version="correlated-dynamic-har-v1",
        routes=routes,
        candidate_concrete_path_count=len(candidates),
        rejected_static_collision_count=rejected_static,
        rejected_uncorroborated_candidate_count=rejected_uncorroborated,
    )


def observe_resolved_dynamic_har(
    path: Path,
    *,
    allowed_host: str,
    concrete_paths: Iterable[str],
    archive: RawArchive,
    database_path: Path,
    migrations_dir: Path,
    contract: ReviewedGetContract,
    dimension_keys: Iterable[str] = (),
) -> tuple[SourceAcquisitionObservation, ...]:
    """Ingest only pre-resolved concrete paths while preserving the reviewed template contract."""
    allowed_paths = {str(value) for value in concrete_paths if str(value)}
    if not allowed_paths:
        return ()

    payload = json.loads(path.read_text(encoding="utf-8"))
    log = payload.get("log", {})
    if not isinstance(log, dict):
        raise ValueError("HAR log must be an object")
    entries = log.get("entries", [])
    if not isinstance(entries, list):
        raise ValueError("HAR log.entries must be an array")

    filtered_entries: list[dict[str, object]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        request = entry.get("request", {})
        if not isinstance(request, dict):
            continue
        if str(request.get("method", "")).upper() != "GET":
            continue
        parts = urlsplit(str(request.get("url", "")))
        if (
            parts.scheme == "https"
            and parts.hostname == allowed_host
            and parts.path in allowed_paths
        ):
            filtered_entries.append(entry)

    if not filtered_entries:
        return ()

    filtered_payload = {"log": {**log, "entries": filtered_entries}}
    with tempfile.TemporaryDirectory(prefix="coa-dynamic-har-") as temp_dir:
        filtered_path = Path(temp_dir) / "resolved.har"
        filtered_path.write_text(
            json.dumps(filtered_payload, ensure_ascii=False),
            encoding="utf-8",
        )
        return observe_reviewed_har(
            filtered_path,
            archive=archive,
            database_path=database_path,
            migrations_dir=migrations_dir,
            contract=contract,
            dimension_keys=dimension_keys,
        )


__all__ = [
    "DynamicHarResolution",
    "ResolvedDynamicRoute",
    "observe_resolved_dynamic_har",
    "resolve_correlated_dynamic_har_routes",
]
