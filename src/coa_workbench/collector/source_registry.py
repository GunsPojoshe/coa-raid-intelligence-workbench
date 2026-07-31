from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class UnverifiedSourceRouteError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class SourceRoute:
    endpoint_code: str
    route_template: str | None
    method: str
    auth_mode: str
    status: str
    use: str

    @property
    def production_ready(self) -> bool:
        return (
            bool(self.route_template)
            and self.status in {"active", "verified"}
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


def load_source_registry(path: Path) -> SourceRegistry:
    payload: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))
    routes = tuple(SourceRoute(**route) for route in payload.get("routes", []))
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
