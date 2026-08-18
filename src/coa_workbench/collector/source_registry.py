from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class UnverifiedSourceRouteError(ValueError):
    pass


_PATH_PARAMETER = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


@dataclass(frozen=True, slots=True)
class SourceRoute:
    endpoint_code: str
    route_template: str | None
    method: str
    auth_mode: str
    status: str
    use: str
    parameter_keys: tuple[str, ...] = ()
    dimension_keys: tuple[str, ...] = ()
    schema_profile_keys: tuple[str, ...] = ()
    scope_path_keys: tuple[str, ...] = ()
    discovery_source: str = "registry"
    review_state: str = "unreviewed"
    empty_params_observed: bool = False

    @property
    def production_ready(self) -> bool:
        return (
            bool(self.route_template)
            and self.status in {"active", "verified"}
            and self.auth_mode != "unknown"
        )

    @property
    def observatory_ready(self) -> bool:
        return (
            bool(self.route_template)
            and self.method.upper() == "GET"
            and self.status in {"reviewed", "verified"}
            and self.review_state in {"reviewed", "verified"}
            and self.auth_mode != "unknown"
        )


@dataclass(frozen=True, slots=True)
class SourceRegistry:
    schema_version: int
    source_code: str
    base_url: str
    status: str
    truth_role: str
    routes: tuple[SourceRoute, ...]
    principles: tuple[str, ...]
    prohibited_assumptions: tuple[str, ...]

    def route(self, endpoint_code: str, *, require_production: bool = False) -> SourceRoute:
        try:
            result = next(route for route in self.routes if route.endpoint_code == endpoint_code)
        except StopIteration as exc:
            raise KeyError(endpoint_code) from exc
        if require_production and not result.production_ready:
            raise UnverifiedSourceRouteError(
                f"source route {endpoint_code!r} is not production-ready: "
                f"status={result.status!r}, auth_mode={result.auth_mode!r}, "
                f"route_template={result.route_template!r}"
            )
        return result


def _source_route(payload: dict[str, Any]) -> SourceRoute:
    route = SourceRoute(
        endpoint_code=str(payload["endpoint_code"]),
        route_template=(
            str(payload["route_template"]) if payload.get("route_template") is not None else None
        ),
        method=str(payload.get("method", "GET")).upper(),
        auth_mode=str(payload.get("auth_mode", "unknown")),
        status=str(payload.get("status", "unverified")),
        use=str(payload.get("use", "unspecified")),
        parameter_keys=tuple(str(value) for value in payload.get("parameter_keys", [])),
        dimension_keys=tuple(str(value) for value in payload.get("dimension_keys", [])),
        schema_profile_keys=tuple(
            str(value) for value in payload.get("schema_profile_keys", [])
        ),
        scope_path_keys=tuple(str(value) for value in payload.get("scope_path_keys", [])),
        discovery_source=str(payload.get("discovery_source", "registry")),
        review_state=str(payload.get("review_state", "unreviewed")),
        empty_params_observed=bool(payload.get("empty_params_observed", False)),
    )
    unknown_profile_keys = sorted(set(route.schema_profile_keys) - set(route.parameter_keys))
    if unknown_profile_keys:
        raise ValueError(
            f"source route {route.endpoint_code!r} schema_profile_keys are not reviewed "
            f"parameter_keys: {unknown_profile_keys}"
        )
    if len(route.schema_profile_keys) != len(set(route.schema_profile_keys)):
        raise ValueError(
            f"source route {route.endpoint_code!r} schema_profile_keys must be unique"
        )
    if len(route.scope_path_keys) != len(set(route.scope_path_keys)):
        raise ValueError(f"source route {route.endpoint_code!r} scope_path_keys must be unique")
    if any(not key for key in route.scope_path_keys):
        raise ValueError(f"source route {route.endpoint_code!r} scope_path_keys cannot be empty")
    if route.scope_path_keys:
        if not route.route_template:
            raise ValueError(
                f"source route {route.endpoint_code!r} scope_path_keys require route_template"
            )
        placeholders = set(_PATH_PARAMETER.findall(route.route_template))
        unknown_scope_keys = sorted(set(route.scope_path_keys) - placeholders)
        if unknown_scope_keys:
            raise ValueError(
                f"source route {route.endpoint_code!r} scope_path_keys are not route path "
                f"parameters: {unknown_scope_keys}"
            )
    return route


def load_source_registry(path: Path) -> SourceRegistry:
    payload: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))
    routes = tuple(_source_route(route) for route in payload.get("routes", []))
    endpoint_codes = [route.endpoint_code for route in routes]
    if len(endpoint_codes) != len(set(endpoint_codes)):
        raise ValueError("source registry endpoint_code values must be unique")
    if not payload.get("base_url", "").startswith("https://"):
        raise ValueError("source registry base_url must use HTTPS")
    return SourceRegistry(
        schema_version=int(payload["schema_version"]),
        source_code=str(payload["source_code"]),
        base_url=str(payload["base_url"]).rstrip("/"),
        status=str(payload["status"]),
        truth_role=str(payload["truth_role"]),
        routes=routes,
        principles=tuple(str(value) for value in payload.get("principles", [])),
        prohibited_assumptions=tuple(
            str(value) for value in payload.get("prohibited_assumptions", [])
        ),
    )
