from __future__ import annotations

import re

from .raw_archive import sanitize_url

_API_ROUTE_PATTERN = re.compile(
    r"(?:https://coa\.ascensionlogs\.gg)?"
    r"(/api/[A-Za-z0-9_./?=&%${}:+\-]+)"
)


def discover_api_route_candidates(body: bytes) -> tuple[str, ...]:
    """Extract sanitized route candidates without damaging JavaScript templates."""
    text = body.decode("utf-8", errors="ignore").replace("\\/", "/")
    candidates: set[str] = set()
    for match in _API_ROUTE_PATTERN.finditer(text):
        # A closing brace can belong to a ${placeholder}; do not strip it as punctuation.
        candidate = match.group(1).rstrip(".,;:)]")
        if len(candidate) > 240:
            continue
        candidates.add(sanitize_url(candidate))
        if len(candidates) >= 200:
            break
    return tuple(sorted(candidates))
