from __future__ import annotations

import base64
import json

from coa_workbench.collector.har_observation_source import load_har_network_observations


def test_har_adapter_filters_host_and_preserves_private_bodies(tmp_path) -> None:
    response_payload = b'{"success":true,"private":"value"}'
    har = {
        "log": {
            "entries": [
                {
                    "startedDateTime": "2026-08-19T00:00:01.000Z",
                    "_resourceType": "xhr",
                    "request": {
                        "method": "POST",
                        "url": "https://coa.ascensionlogs.gg/api/reports/123/query?difficulty=4",
                        "postData": {
                            "mimeType": "application/json",
                            "text": '{"encounterId":456,"mode":"summary"}',
                        },
                    },
                    "response": {
                        "status": 200,
                        "content": {
                            "mimeType": "application/json",
                            "encoding": "base64",
                            "text": base64.b64encode(response_payload).decode("ascii"),
                        },
                    },
                },
                {
                    "startedDateTime": "2026-08-19T00:00:02.000Z",
                    "request": {
                        "method": "GET",
                        "url": "https://example.invalid/api/private",
                    },
                    "response": {"status": 200, "content": {"text": "{}"}},
                },
            ]
        }
    }
    path = tmp_path / "capture.har"
    path.write_text(json.dumps(har), encoding="utf-8")

    observations = load_har_network_observations(
        path,
        allowed_host="coa.ascensionlogs.gg",
        api_prefix="/api/",
    )

    assert len(observations) == 1
    observation = observations[0]
    assert observation.ordinal == 0
    assert observation.source_kind == "har"
    assert observation.request_body == b'{"encounterId":456,"mode":"summary"}'
    assert observation.response_body == response_payload
    assert observation.query_keys == ("difficulty",)
    assert observation.request_body_keys == ("encounterId", "mode")

    rendered = json.dumps(observation.public_summary(), sort_keys=True)
    assert "summary" not in rendered
    assert "456" not in rendered
    assert "private" not in rendered
    assert "value" not in rendered


def test_har_adapter_rejects_non_array_entries(tmp_path) -> None:
    path = tmp_path / "bad.har"
    path.write_text('{"log":{"entries":{}}}', encoding="utf-8")

    try:
        load_har_network_observations(path)
    except ValueError as exc:
        assert str(exc) == "HAR log.entries must be an array"
    else:
        raise AssertionError("expected ValueError")
