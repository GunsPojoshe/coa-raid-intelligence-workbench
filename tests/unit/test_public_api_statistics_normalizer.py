from __future__ import annotations

import pytest

from coa_workbench.normalizer.public_api_statistics import parse_public_api_statistics


def _metric(base: float, parses: int) -> dict[str, object]:
    return {
        "avg": base,
        "median": base - 1.0,
        "max": base + 10.0,
        "min": base - 10.0,
        "total_parses": parses,
        "percentiles": {"50": base - 1.0, "75": base + 2.0, "95": base + 5.0},
    }


def _payload() -> dict[str, object]:
    return {
        "success": True,
        "phase": 12,
        "phase_name": "private-phase",
        "difficulty": "all",
        "metric": "avg_dps",
        "bracket": "all",
        "location": None,
        "boss_id": None,
        "damage_mode": "standard",
        "week_number": None,
        "day_number": None,
        "statistics": {
            "PrivateClassAlpha": {
                "total_parses": 30,
                "summary_a": 1.0,
                "summary_b": 2.0,
                "summary_c": 3,
                "specs": {
                    "PrivateSpecOne": _metric(100.0, 20),
                    "PrivateSpecTwo": _metric(80.0, 10),
                },
            },
            "PrivateClassBeta": {
                "total_parses": 5,
                "summary_a": 4.0,
                "summary_b": 5.0,
                "summary_c": 6,
                "children": {"PrivateSpecThree": _metric(60.0, 5)},
            },
        },
    }


def test_statistics_parser_normalizes_observed_class_spec_shape_and_request_scope() -> None:
    batch = parse_public_api_statistics(
        _payload(),
        query_keys=("phase", "difficulty", "metric", "bracket", "damageMode", "role"),
        query_values={
            "phase": "12",
            "difficulty": "all",
            "metric": "avg_dps",
            "bracket": "all",
            "damageMode": "standard",
            "role": "dps",
        },
    )

    assert batch.dimensions.phase == 12
    assert batch.dimensions.difficulty == "all"
    assert batch.dimensions.metric == "avg_dps"
    assert batch.dimensions.bracket == "all"
    assert batch.dimensions.damage_mode == "standard"
    assert batch.dimensions.role == "dps"
    assert batch.dimensions.class_filter is None
    assert batch.dimensions.spec_filter is None
    assert len(batch.class_summaries) == 2
    assert len(batch.records) == 3
    assert batch.percentile_value_count == 9
    assert batch.class_summaries[0].class_name == "PrivateClassAlpha"
    assert batch.records[0].spec_name == "PrivateSpecOne"
    assert batch.records[0].total_parses == 20
    assert batch.records[0].percentiles == (("50", 99.0), ("75", 102.0), ("95", 105.0))


def test_statistics_parser_recovers_echoed_legacy_query_values_but_refuses_missing_role() -> None:
    with pytest.raises(ValueError, match="bounded recapture is required"):
        parse_public_api_statistics(
            _payload(),
            query_keys=("phase", "difficulty", "metric", "bracket", "damageMode", "role"),
            query_values={},
        )


def test_statistics_parser_detects_query_response_conflict() -> None:
    with pytest.raises(ValueError, match="conflicts with echoed response field"):
        parse_public_api_statistics(
            _payload(),
            query_keys=("phase", "role"),
            query_values={"phase": "99", "role": "dps"},
        )


def test_statistics_parser_refuses_ambiguous_nested_class_structures() -> None:
    payload = _payload()
    statistics = payload["statistics"]
    assert isinstance(statistics, dict)
    class_row = statistics["PrivateClassAlpha"]
    assert isinstance(class_row, dict)
    class_row["other_specs"] = {"PrivateSpecOther": _metric(70.0, 1)}

    with pytest.raises(ValueError, match="exactly one observed spec-to-metric object"):
        parse_public_api_statistics(
            payload,
            query_keys=("role",),
            query_values={"role": "dps"},
        )


def test_statistics_parser_requires_exact_documented_metric_fields() -> None:
    payload = _payload()
    statistics = payload["statistics"]
    assert isinstance(statistics, dict)
    class_row = statistics["PrivateClassAlpha"]
    assert isinstance(class_row, dict)
    specs = class_row["specs"]
    assert isinstance(specs, dict)
    metric = specs["PrivateSpecOne"]
    assert isinstance(metric, dict)
    metric["unreviewed"] = 1

    with pytest.raises(ValueError, match="exactly one observed spec-to-metric object"):
        parse_public_api_statistics(
            payload,
            query_keys=("role",),
            query_values={"role": "dps"},
        )
