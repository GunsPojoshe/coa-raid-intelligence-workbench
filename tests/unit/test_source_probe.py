from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from coa_workbench.collector.probe import probe_registry_route
from coa_workbench.collector.raw_archive import RawArchive
from coa_workbench.collector.source_registry import SourceRegistry, SourceRoute


class FakeHeaders:
    def get_content_type(self) -> str:
        return "text/html"


class FakeResponse:
    status = 200
    headers = FakeHeaders()

    def read(self) -> bytes:
        return b"<html>ok</html>"

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> bool:
        return False


def registry(route_template: str = "/") -> SourceRegistry:
    return SourceRegistry(
        schema_version=1,
        source_code="coa_ascension_logs",
        base_url="https://coa.ascensionlogs.gg",
        status="discovery",
        truth_role="primary_observation_source",
        routes=(
            SourceRoute(
                endpoint_code="public_home",
                route_template=route_template,
                method="GET",
                auth_mode="public",
                status="verified_html",
                use="availability_probe",
            ),
        ),
        principles=(),
        prohibited_assumptions=(),
    )


def test_probe_captures_response_without_promoting_route(tmp_path: Path) -> None:
    with patch("coa_workbench.collector.probe.urlopen", return_value=FakeResponse()):
        result = probe_registry_route(
            registry(),
            "public_home",
            RawArchive(tmp_path / "raw"),
        )

    assert result.status == 200
    assert result.content_type == "text/html"
    assert result.capture is not None
    assert Path(result.capture.payload_path).is_file()
    assert registry().route("public_home").production_ready is False


def test_probe_rejects_route_that_escapes_configured_host(tmp_path: Path) -> None:
    with patch("coa_workbench.collector.probe.urlopen") as mocked:
        with pytest.raises(ValueError, match="escaped"):
            probe_registry_route(
                registry("https://evil.invalid/"),
                "public_home",
                RawArchive(tmp_path / "raw"),
            )

    mocked.assert_not_called()


def test_probe_rejects_unknown_route_shape(tmp_path: Path) -> None:
    no_route = registry()
    no_route = SourceRegistry(
        schema_version=no_route.schema_version,
        source_code=no_route.source_code,
        base_url=no_route.base_url,
        status=no_route.status,
        truth_role=no_route.truth_role,
        routes=(
            SourceRoute(
                endpoint_code="aura_timeline",
                route_template=None,
                method="GET",
                auth_mode="unknown",
                status="unverified",
                use="state_reconstruction",
            ),
        ),
        principles=(),
        prohibited_assumptions=(),
    )

    with pytest.raises(ValueError, match="no discovered route_template"):
        probe_registry_route(
            no_route,
            "aura_timeline",
            RawArchive(tmp_path / "raw"),
        )
