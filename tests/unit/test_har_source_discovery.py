from __future__ import annotations

import base64
import json
import os
from pathlib import Path

from coa_workbench.collector.har_source_discovery import (
    inventory_network_har,
    select_latest_relevant_har,
)


def test_inventory_network_har_is_same_origin_and_scalar_free(tmp_path: Path) -> None:
    private_scalar = "do-not-publish-me"
    payload = {
        "log": {
            "entries": [
                {
                    "startedDateTime": "2026-08-14T08:00:00.000Z",
                    "_resourceType": "xhr",
                    "request": {
                        "method": "GET",
                        "url": (
                            "https://coa.ascensionlogs.gg/api/guilds/42/reports"
                            f"?page={private_scalar}"
                        ),
                        "headers": [{"name": "Cookie", "value": private_scalar}],
                    },
                    "response": {
                        "status": 200,
                        "content": {
                            "mimeType": "application/json",
                            "text": json.dumps(
                                {"rows": [{"reportId": 123, "guildName": private_scalar}]}
                            ),
                        },
                    },
                },
                {
                    "startedDateTime": "2026-08-14T08:00:01.000Z",
                    "_resourceType": "xhr",
                    "request": {
                        "method": "GET",
                        "url": "https://coa.ascensionlogs.gg/api/phases",
                    },
                    "response": {
                        "status": 200,
                        "content": {
                            "mimeType": "application/json",
                            "encoding": "base64",
                            "text": base64.b64encode(
                                b'{"success":true,"phases":[{"phase_number":2}]}'
                            ).decode(),
                        },
                    },
                },
                {
                    "startedDateTime": "2026-08-14T08:00:02.000Z",
                    "_resourceType": "xhr",
                    "request": {
                        "method": "GET",
                        "url": f"https://third.example/api/leak?token={private_scalar}",
                    },
                    "response": {
                        "status": 200,
                        "content": {"mimeType": "application/json", "text": "{}"},
                    },
                },
            ]
        }
    }
    har = tmp_path / "capture.har"
    har.write_text(json.dumps(payload), encoding="utf-8")

    result = inventory_network_har(har, allowed_host="coa.ascensionlogs.gg")
    rendered = json.dumps(result, ensure_ascii=False, sort_keys=True)

    assert result["summary"]["same_origin_api_entry_count"] == 2
    assert result["summary"]["route_shape_count"] == 2
    assert result["summary"]["contains_query_values"] is False
    assert private_scalar not in rendered
    assert "third.example" not in rendered

    routes = {(row["method"], row["route_shape"]): row for row in result["routes"]}
    reports = routes[("GET", "/api/guilds/{integer}/reports?page=<value>")]
    assert reports["query_keys"] == ["page"]
    assert reports["json_response_count"] == 1
    assert reports["statuses"] == [200]

    phases = routes[("GET", "/api/phases")]
    assert phases["json_response_count"] == 1
    assert phases["content_type_families"] == ["json"]


def _write_single_request_har(path: Path, url: str) -> None:
    payload = {
        "log": {
            "entries": [
                {
                    "startedDateTime": "2026-08-14T09:00:00.000Z",
                    "_resourceType": "xhr",
                    "request": {"method": "GET", "url": url},
                    "response": {
                        "status": 200,
                        "content": {"mimeType": "application/json", "text": "{}"},
                    },
                }
            ]
        }
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_select_latest_relevant_har_skips_newer_unrelated_or_invalid_files(
    tmp_path: Path,
) -> None:
    relevant = tmp_path / "relevant.har"
    unrelated = tmp_path / "unrelated.har"
    invalid = tmp_path / "invalid.har"

    _write_single_request_har(relevant, "https://coa.ascensionlogs.gg/api/phases")
    _write_single_request_har(unrelated, "https://third.example/api/phases")
    invalid.write_text("not-json", encoding="utf-8")

    os.utime(relevant, ns=(1_000_000_000, 1_000_000_000))
    os.utime(unrelated, ns=(2_000_000_000, 2_000_000_000))
    os.utime(invalid, ns=(3_000_000_000, 3_000_000_000))

    selected = select_latest_relevant_har(
        tmp_path,
        allowed_host="coa.ascensionlogs.gg",
    )
    assert selected == relevant

    newer_relevant = tmp_path / "newer-relevant.HAR"
    _write_single_request_har(newer_relevant, "https://coa.ascensionlogs.gg/api/phases")
    os.utime(newer_relevant, ns=(4_000_000_000, 4_000_000_000))

    selected = select_latest_relevant_har(
        tmp_path,
        allowed_host="coa.ascensionlogs.gg",
    )
    assert selected == newer_relevant
