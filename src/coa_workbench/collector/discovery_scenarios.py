from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml

DISCOVERY_SCENARIO_VERSION = "discovery-scenario-coverage-v1"
_PUBLIC_CODE = re.compile(r"^[a-z][a-z0-9_.-]{0,79}$")
_COVERAGE_STATES = (
    "unobserved",
    "observed",
    "repeatable_structure",
    "scalar_variation_observed",
)


def validate_scenario_code(value: str) -> str:
    if not _PUBLIC_CODE.fullmatch(value):
        raise ValueError("scenario_code must be a lowercase public-safe code")
    return value


@dataclass(frozen=True, slots=True)
class DiscoveryScenario:
    scenario_code: str
    surface_family: str
    objective: str

    def __post_init__(self) -> None:
        validate_scenario_code(self.scenario_code)
        validate_scenario_code(self.surface_family)
        if not self.objective.strip():
            raise ValueError("scenario objective must be non-empty")

    def public_summary(self) -> dict[str, object]:
        return {
            "scenario_code": self.scenario_code,
            "surface_family": self.surface_family,
            "objective": self.objective,
        }


@dataclass(frozen=True, slots=True)
class DiscoveryScenarioManifest:
    source_code: str
    scenarios: tuple[DiscoveryScenario, ...]
    schema_version: int = 1

    def __post_init__(self) -> None:
        validate_scenario_code(self.source_code)
        if self.schema_version != 1:
            raise ValueError("unsupported discovery scenario schema_version")
        codes = [scenario.scenario_code for scenario in self.scenarios]
        if len(codes) != len(set(codes)):
            raise ValueError("scenario codes must be unique")


def load_discovery_scenario_manifest(path: Path) -> DiscoveryScenarioManifest:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("discovery scenario manifest must contain an object")
    raw_scenarios = payload.get("scenarios")
    if not isinstance(raw_scenarios, list):
        raise ValueError("discovery scenario manifest scenarios must be an array")
    scenarios: list[DiscoveryScenario] = []
    for index, raw in enumerate(raw_scenarios):
        if not isinstance(raw, dict):
            raise ValueError(f"scenarios[{index}] must be an object")
        code = raw.get("scenario_code")
        surface = raw.get("surface_family")
        objective = raw.get("objective")
        if not isinstance(code, str) or not isinstance(surface, str) or not isinstance(objective, str):
            raise ValueError(f"scenarios[{index}] fields must be strings")
        scenarios.append(DiscoveryScenario(code, surface, objective))
    source_code = payload.get("source_code")
    schema_version = payload.get("schema_version")
    if not isinstance(source_code, str):
        raise ValueError("source_code must be a string")
    if not isinstance(schema_version, int) or isinstance(schema_version, bool):
        raise ValueError("schema_version must be an integer")
    return DiscoveryScenarioManifest(
        source_code=source_code,
        scenarios=tuple(scenarios),
        schema_version=schema_version,
    )


def _integer(value: object) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _receipt_metrics(receipt: Mapping[str, Any]) -> dict[str, object]:
    source = receipt.get("source")
    source = source if isinstance(source, Mapping) else {}
    repetition = receipt.get("repetition_review")
    repetition = repetition if isinstance(repetition, Mapping) else {}
    source_code = source.get("source_code")
    if not isinstance(source_code, str):
        source_code = "unknown"
    else:
        try:
            source_code = validate_scenario_code(source_code)
        except ValueError:
            source_code = "invalid"
    scenario_code = source.get("scenario_code")
    if not isinstance(scenario_code, str):
        scenario_code = "unassigned"
    else:
        try:
            scenario_code = validate_scenario_code(scenario_code)
        except ValueError:
            scenario_code = "invalid"
    return {
        "source_code": source_code,
        "scenario_code": scenario_code,
        "action_count": _integer(receipt.get("action_count")),
        "network_request_count": _integer(source.get("network_request_count")),
        "network_silent_action_count": _integer(receipt.get("network_silent_action_count")),
        "repeated_signature_count": _integer(
            repetition.get("exclusive_repeated_signature_count")
        ),
        "scalar_variation_signature_count": _integer(
            repetition.get("exclusive_repeated_signature_with_scalar_variation_count")
        ),
    }


def _coverage_state(metrics: Mapping[str, int]) -> str:
    if metrics["session_count"] == 0:
        return "unobserved"
    if metrics["scalar_variation_signature_count"] > 0:
        return "scalar_variation_observed"
    if metrics["repeated_signature_count"] > 0:
        return "repeatable_structure"
    return "observed"


def build_discovery_scenario_coverage(
    manifest: DiscoveryScenarioManifest,
    receipts: Iterable[Mapping[str, Any]],
) -> dict[str, object]:
    metrics_by_code: dict[str, dict[str, int]] = {
        scenario.scenario_code: {
            "session_count": 0,
            "action_count": 0,
            "network_request_count": 0,
            "network_silent_action_count": 0,
            "repeated_signature_count": 0,
            "scalar_variation_signature_count": 0,
        }
        for scenario in manifest.scenarios
    }
    unknown_codes: dict[str, int] = {}
    unassigned_session_count = 0
    invalid_scenario_session_count = 0
    foreign_source_session_count = 0

    for receipt in receipts:
        metrics = _receipt_metrics(receipt)
        source_code = str(metrics["source_code"])
        if source_code != manifest.source_code:
            foreign_source_session_count += 1
            continue
        scenario_code = str(metrics["scenario_code"])
        if scenario_code == "unassigned":
            unassigned_session_count += 1
            continue
        if scenario_code == "invalid":
            invalid_scenario_session_count += 1
            continue
        target = metrics_by_code.get(scenario_code)
        if target is None:
            unknown_codes[scenario_code] = unknown_codes.get(scenario_code, 0) + 1
            continue
        target["session_count"] += 1
        for key in (
            "action_count",
            "network_request_count",
            "network_silent_action_count",
            "repeated_signature_count",
            "scalar_variation_signature_count",
        ):
            target[key] += int(metrics[key])

    scenario_rows: list[dict[str, object]] = []
    state_counts = {state: 0 for state in _COVERAGE_STATES}
    for scenario in manifest.scenarios:
        metrics = metrics_by_code[scenario.scenario_code]
        state = _coverage_state(metrics)
        state_counts[state] += 1
        scenario_rows.append(
            {
                **scenario.public_summary(),
                "coverage_state": state,
                **metrics,
                "semantic_review_required": True,
            }
        )

    observed_scenarios = len(manifest.scenarios) - state_counts["unobserved"]
    return {
        "coverage_version": DISCOVERY_SCENARIO_VERSION,
        "source_code": manifest.source_code,
        "scenario_count": len(manifest.scenarios),
        "observed_scenario_count": observed_scenarios,
        "scenarios": scenario_rows,
        "state_counts": state_counts,
        "unassigned_session_count": unassigned_session_count,
        "invalid_scenario_session_count": invalid_scenario_session_count,
        "foreign_source_session_count": foreign_source_session_count,
        "unknown_scenario_codes": [
            {"scenario_code": code, "session_count": unknown_codes[code]}
            for code in sorted(unknown_codes)
        ],
        "coverage_is_semantic_proof": False,
        "coverage_is_completion_percentage": False,
    }


__all__ = [
    "DISCOVERY_SCENARIO_VERSION",
    "DiscoveryScenario",
    "DiscoveryScenarioManifest",
    "build_discovery_scenario_coverage",
    "load_discovery_scenario_manifest",
    "validate_scenario_code",
]
