from __future__ import annotations

import json

from coa_workbench.collector.network_observation import NetworkObservation


def test_network_observation_public_summary_is_scalar_safe() -> None:
    observation = NetworkObservation(
        ordinal=3,
        observed_at="2026-08-19T00:00:01+00:00",
        method="POST",
        url="https://coa.ascensionlogs.gg/api/reports/123/thing?difficulty=heroic&boss=999",
        status=200,
        request_content_type="application/json",
        response_content_type="application/json",
        request_body=b'{"reportId":123,"difficulty":"heroic","secret":"value"}',
        response_body=b'{"success":true,"report":{"id":123,"name":"Private"}}',
        resource_type="fetch",
        source_kind="har",
    )

    summary = observation.public_summary()
    rendered = json.dumps(summary, sort_keys=True)

    assert observation.query_keys == ("boss", "difficulty")
    assert observation.request_body_keys == ("difficulty", "reportId", "secret")
    assert summary["query_keys"] == ["boss", "difficulty"]
    assert summary["request_body_keys"] == ["difficulty", "reportId", "secret"]
    assert summary["response_structure_fingerprint"]
    assert summary["route_shape"] == (
        "/api/reports/{integer}/thing?boss=<value>&difficulty=<value>"
    )
    assert "heroic" not in rendered
    assert "999" not in rendered
    assert "Private" not in rendered
    assert '"reportId": 123' not in rendered
    assert summary["privacy"]["response_body_included"] is False


def test_network_observation_handles_non_json_bodies() -> None:
    observation = NetworkObservation(
        ordinal=0,
        observed_at="2026-08-19T00:00:00Z",
        method="POST",
        url="https://coa.ascensionlogs.gg/api/example",
        status=204,
        request_body=b"opaque=value",
        response_body=b"not-json",
    )

    assert observation.request_body_keys == ()
    assert observation.response_structure_fingerprint is None
