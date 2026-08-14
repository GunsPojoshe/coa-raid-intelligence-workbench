from __future__ import annotations

import json
from pathlib import Path

from coa_workbench.collector.har_dynamic_resolution import (
    resolve_correlated_dynamic_har_routes,
)


def _write_har(path: Path, urls: list[str]) -> None:
    path.write_text(
        json.dumps(
            {
                "log": {
                    "entries": [
                        {
                            "request": {"method": "GET", "url": url},
                            "response": {
                                "status": 200,
                                "content": {
                                    "mimeType": "application/json",
                                    "text": "{}",
                                },
                            },
                        }
                        for url in urls
                    ]
                }
            }
        ),
        encoding="utf-8",
    )


def _templates() -> dict[str, str]:
    return {
        "report_detail_api": "/api/reports/{reportId}",
        "report_encounter_detail_api": (
            "/api/reports/{reportId}/encounters/{encounterId}"
        ),
        "report_encounter_combatants_info_api": (
            "/api/reports/{reportId}/encounters/{encounterId}/combatants-info"
        ),
    }


def test_dynamic_resolution_excludes_static_collision_and_accepts_correlated_chain(
    tmp_path: Path,
) -> None:
    har = tmp_path / "report.har"
    _write_har(
        har,
        [
            "https://coa.ascensionlogs.gg/api/reports/public",
            "https://coa.ascensionlogs.gg/api/reports/queue-status",
            "https://coa.ascensionlogs.gg/api/reports/report-opaque",
            (
                "https://coa.ascensionlogs.gg/api/reports/report-opaque/"
                "encounters/encounter-opaque"
            ),
            (
                "https://coa.ascensionlogs.gg/api/reports/report-opaque/"
                "encounters/encounter-opaque/combatants-info"
            ),
        ],
    )

    result = resolve_correlated_dynamic_har_routes(
        har,
        allowed_host="coa.ascensionlogs.gg",
        dynamic_route_templates=_templates(),
        static_paths=[
            "/api/reports/public",
            "/api/reports/queue-status",
        ],
    )

    assert result.resolved_endpoint_codes == (
        "report_detail_api",
        "report_encounter_combatants_info_api",
        "report_encounter_detail_api",
    )
    assert result.paths_for("report_detail_api") == (
        "/api/reports/report-opaque",
    )
    assert result.paths_for("report_encounter_detail_api") == (
        "/api/reports/report-opaque/encounters/encounter-opaque",
    )
    assert result.paths_for("report_encounter_combatants_info_api") == (
        "/api/reports/report-opaque/encounters/encounter-opaque/combatants-info",
    )
    assert result.rejected_static_collision_count == 2
    assert result.rejected_uncorroborated_candidate_count == 0

    public = result.public_summary()
    assert public["concrete_path_values_included"] is False
    assert public["path_parameter_values_included"] is False
    assert "report-opaque" not in json.dumps(public)


def test_dynamic_resolution_rejects_uncorroborated_single_dynamic_candidate(
    tmp_path: Path,
) -> None:
    har = tmp_path / "single.har"
    _write_har(
        har,
        ["https://coa.ascensionlogs.gg/api/reports/one-off-token"],
    )

    result = resolve_correlated_dynamic_har_routes(
        har,
        allowed_host="coa.ascensionlogs.gg",
        dynamic_route_templates=_templates(),
        static_paths=[
            "/api/reports/public",
            "/api/reports/queue-status",
        ],
    )

    assert result.resolved_endpoint_codes == ()
    assert result.resolved_concrete_path_count == 0
    assert result.candidate_concrete_path_count == 1
    assert result.rejected_uncorroborated_candidate_count == 1


def test_dynamic_resolution_ignores_other_hosts_and_non_get_requests(tmp_path: Path) -> None:
    har = tmp_path / "mixed.har"
    har.write_text(
        json.dumps(
            {
                "log": {
                    "entries": [
                        {
                            "request": {
                                "method": "POST",
                                "url": (
                                    "https://coa.ascensionlogs.gg/api/reports/report-opaque"
                                ),
                            }
                        },
                        {
                            "request": {
                                "method": "GET",
                                "url": (
                                    "https://example.invalid/api/reports/report-opaque"
                                ),
                            }
                        },
                    ]
                }
            }
        ),
        encoding="utf-8",
    )

    result = resolve_correlated_dynamic_har_routes(
        har,
        allowed_host="coa.ascensionlogs.gg",
        dynamic_route_templates=_templates(),
        static_paths=[],
    )

    assert result.candidate_concrete_path_count == 0
    assert result.resolved_endpoint_codes == ()
