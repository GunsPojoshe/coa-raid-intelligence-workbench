from __future__ import annotations

import json
from pathlib import Path

from coa_workbench.collector.discovery_scenarios import (
    DiscoveryScenario,
    DiscoveryScenarioManifest,
    build_discovery_scenario_coverage,
    load_discovery_scenario_manifest,
)


def _receipt(
    scenario_code: str,
    *,
    source_code: str = "coa_ascension_logs",
    actions: int = 3,
    requests: int = 5,
    repeated: int = 0,
    scalar: int = 0,
) -> dict[str, object]:
    return {
        "action_count": actions,
        "network_silent_action_count": 1,
        "source": {
            "source_code": source_code,
            "scenario_code": scenario_code,
            "network_request_count": requests,
        },
        "repetition_review": {
            "exclusive_repeated_signature_count": repeated,
            "exclusive_repeated_signature_with_scalar_variation_count": scalar,
        },
    }


def test_scenario_coverage_states_are_evidence_states_not_completion() -> None:
    manifest = DiscoveryScenarioManifest(
        source_code="coa_ascension_logs",
        scenarios=(
            DiscoveryScenario("reports.discovery", "reports", "Catalog discovery"),
            DiscoveryScenario("report.difficulty", "report", "Difficulty correlation"),
            DiscoveryScenario("rankings.discovery", "rankings", "Rankings discovery"),
            DiscoveryScenario("statistics.discovery", "statistics", "Statistics discovery"),
        ),
    )
    receipts = (
        _receipt("reports.discovery"),
        _receipt("report.difficulty", repeated=1),
        _receipt("rankings.discovery", repeated=2, scalar=1),
    )

    result = build_discovery_scenario_coverage(manifest, receipts)
    by_code = {row["scenario_code"]: row for row in result["scenarios"]}

    assert by_code["reports.discovery"]["coverage_state"] == "observed"
    assert by_code["report.difficulty"]["coverage_state"] == "repeatable_structure"
    assert by_code["rankings.discovery"]["coverage_state"] == "scalar_variation_observed"
    assert by_code["statistics.discovery"]["coverage_state"] == "unobserved"
    assert result["observed_scenario_count"] == 3
    assert result["coverage_is_semantic_proof"] is False
    assert result["coverage_is_completion_percentage"] is False


def test_scenario_coverage_reports_unassigned_unknown_invalid_and_foreign_receipts() -> None:
    manifest = DiscoveryScenarioManifest(
        source_code="coa_ascension_logs",
        scenarios=(DiscoveryScenario("reports.discovery", "reports", "Catalog discovery"),),
    )

    result = build_discovery_scenario_coverage(
        manifest,
        (
            _receipt("unassigned"),
            _receipt("future.surface"),
            _receipt("Private / Leaky Scenario"),
            _receipt("reports.discovery", source_code="coa_armory"),
        ),
    )

    assert result["unassigned_session_count"] == 1
    assert result["invalid_scenario_session_count"] == 1
    assert result["foreign_source_session_count"] == 1
    assert result["unknown_scenario_codes"] == [
        {"scenario_code": "future.surface", "session_count": 1}
    ]
    assert "Private / Leaky Scenario" not in json.dumps(result, sort_keys=True)


def test_manifest_loader_rejects_duplicate_codes(tmp_path: Path) -> None:
    path = tmp_path / "scenarios.yaml"
    path.write_text(
        """schema_version: 1
source_code: coa_ascension_logs
scenarios:
  - scenario_code: reports.discovery
    surface_family: reports
    objective: First
  - scenario_code: reports.discovery
    surface_family: reports
    objective: Second
""",
        encoding="utf-8",
    )

    try:
        load_discovery_scenario_manifest(path)
    except ValueError as exc:
        assert str(exc) == "scenario codes must be unique"
    else:
        raise AssertionError("expected ValueError")
