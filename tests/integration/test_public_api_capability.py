from __future__ import annotations

import json
from pathlib import Path
from urllib.request import Request

from coa_workbench.collector import public_api_capability
from coa_workbench.collector.public_api_capability import (
    probe_public_api_capabilities,
    public_api_capability_probe_to_dict,
)
from coa_workbench.collector.source_registry import load_source_registry


def _registry():
    return load_source_registry(Path("config/coa_public_api_sources.yaml"))


def test_probe_uses_only_official_stats_and_events_routes(monkeypatch) -> None:
    responses = [
        (200, "application/json", b'{"success":true,"bosses":[]}', None),
        (
            200,
            "application/json",
            b'{"success":true,"reports":[{"id":987654,"title":"private"}],'
            b'"pagination":{"limit":1,"offset":0,"returned":1}}',
            None,
        ),
    ]
    requests: list[Request] = []

    def fake_read(request: Request, **_kwargs):
        requests.append(request)
        return responses.pop(0)

    monkeypatch.setattr(public_api_capability, "read_response_resilient", fake_read)
    result = probe_public_api_capabilities(_registry(), api_key="local-secret")
    receipt = public_api_capability_probe_to_dict(result)
    rendered = json.dumps(receipt, sort_keys=True)

    assert result.network_request_count == 2
    assert result.stats_read.outcome == "available"
    assert result.events_read.outcome == "available"
    assert result.events_read_available is True
    assert result.access_request_required is False
    assert requests[0].full_url == "https://coa.ascensionlogs.gg/api/public/v1/bosses"
    assert requests[1].full_url == "https://coa.ascensionlogs.gg/api/public/v1/reports?limit=1"
    assert all(request.get_header("Authorization") == "Bearer local-secret" for request in requests)
    assert "local-secret" not in rendered
    assert "987654" not in rendered
    assert "private" not in rendered
    assert receipt["summary"]["direct_official_public_api_only"] is True
    assert receipt["summary"]["browser_context_used"] is False
    assert receipt["summary"]["browser_har_used"] is False
    assert receipt["summary"]["raw_archive_written"] is False
    assert receipt["public_release_safe"] is True


def test_probe_classifies_valid_key_without_events_scope(monkeypatch) -> None:
    responses = [
        (200, "application/json", b'{"success":true,"bosses":[]}', None),
        (
            403,
            "application/json",
            b'{"success":false,"error":"insufficient_scope",'
            b'"message":"events:read required"}',
            "HTTP 403: Forbidden",
        ),
    ]

    def fake_read(_request: Request, **_kwargs):
        return responses.pop(0)

    monkeypatch.setattr(public_api_capability, "read_response_resilient", fake_read)
    result = probe_public_api_capabilities(_registry(), api_key="local-secret")
    receipt = public_api_capability_probe_to_dict(result)

    assert result.stats_read.outcome == "available"
    assert result.events_read.outcome == "insufficient_scope"
    assert result.events_read.error_code == "insufficient_scope"
    assert result.events_read.transport_error_present is False
    assert result.events_read_available is False
    assert result.access_request_required is True
    assert receipt["summary"]["events_read_access_request_required"] is True
    assert receipt["summary"]["ready_for_official_event_pipeline"] is False


def test_probe_does_not_promote_unexpected_success_shape(monkeypatch) -> None:
    responses = [
        (200, "application/json", b'{"success":true,"bosses":[]}', None),
        (200, "application/json", b'{"success":true,"rows":[]}', None),
    ]

    def fake_read(_request: Request, **_kwargs):
        return responses.pop(0)

    monkeypatch.setattr(public_api_capability, "read_response_resilient", fake_read)
    result = probe_public_api_capabilities(_registry(), api_key="local-secret")

    assert result.events_read.status == 200
    assert result.events_read.json_valid is True
    assert result.events_read.response_shape_valid is False
    assert result.events_read.outcome == "unexpected_response_shape"
    assert result.events_read_available is False
    assert result.access_request_required is False
