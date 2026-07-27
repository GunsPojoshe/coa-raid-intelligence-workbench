from __future__ import annotations

import ssl
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen

from .raw_archive import RawArchive, RawCapture, request_key_from_url
from .source_registry import SourceRegistry


@dataclass(frozen=True, slots=True)
class ProbeResult:
    endpoint_code: str
    url: str
    status: int | None
    content_type: str | None
    capture: RawCapture | None
    error: str | None


def probe_registry_route(
    registry: SourceRegistry,
    endpoint_code: str,
    archive: RawArchive,
    *,
    timeout_seconds: float = 20.0,
) -> ProbeResult:
    route = registry.route(endpoint_code)
    if not route.route_template:
        raise ValueError(f"route {endpoint_code!r} has no discovered route_template")
    if route.method.upper() != "GET":
        raise ValueError("discovery probe currently supports GET only")

    url = urljoin(f"{registry.base_url}/", route.route_template.lstrip("/"))
    if urlsplit(url).hostname != urlsplit(registry.base_url).hostname:
        raise ValueError("route escaped the configured source host")

    request = Request(
        url,
        headers={
            "Accept": "application/json, text/html;q=0.9, */*;q=0.1",
            "User-Agent": "CoA-Raid-Intelligence-Workbench/0.1 route-probe",
        },
        method="GET",
    )
    status: int | None = None
    content_type: str | None = None
    body: bytes | None = None
    error: str | None = None
    try:
        with urlopen(
            request,
            timeout=timeout_seconds,
            context=ssl.create_default_context(),
        ) as response:
            status = response.status
            content_type = response.headers.get_content_type()
            body = response.read()
    except HTTPError as exc:
        status = exc.code
        content_type = exc.headers.get_content_type() if exc.headers else None
        body = exc.read()
        error = f"HTTP {exc.code}: {exc.reason}"
    except URLError as exc:
        error = f"network error: {exc.reason}"

    capture = None
    if body is not None:
        capture = archive.capture_bytes(
            body,
            source_code=registry.source_code,
            endpoint_code=endpoint_code,
            request_key=request_key_from_url("GET", url),
            fetched_at=datetime.now(timezone.utc),
            http_status=status,
            content_type=content_type,
            request_url=url,
            metadata={
                "probe": True,
                "route_status_before_probe": route.status,
            },
        )
    return ProbeResult(
        endpoint_code=endpoint_code,
        url=url,
        status=status,
        content_type=content_type,
        capture=capture,
        error=error,
    )


def probe_result_to_dict(result: ProbeResult) -> dict[str, object]:
    return asdict(result)
