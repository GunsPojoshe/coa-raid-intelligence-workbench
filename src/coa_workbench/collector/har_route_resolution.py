from __future__ import annotations

import re

_PATH_PARAMETER = re.compile(r"\{[A-Za-z_][A-Za-z0-9_]*\}")


def route_requires_explicit_dynamic_resolution(route_template: str | None) -> bool:
    """Return whether a reviewed route contains dynamic path segments.

    Generic HAR ingestion deliberately handles only exact static paths. Dynamic templates need
    an explicit resolver that validates segment semantics before a browser request can be bound
    to the reviewed contract. This prevents a template such as ``/api/reports/{reportId}`` from
    claiming an unrelated static path such as ``/api/reports/queue-status``.
    """
    return bool(route_template and _PATH_PARAMETER.search(route_template))


def generic_har_ingest_ready(route_template: str | None) -> bool:
    """Return whether an exact reviewed route may be ingested by the generic HAR cycle."""
    return bool(route_template) and not route_requires_explicit_dynamic_resolution(route_template)


__all__ = [
    "generic_har_ingest_ready",
    "route_requires_explicit_dynamic_resolution",
]
