from __future__ import annotations

import pytest

from coa_workbench.collector.public_api_statistics_review import (
    build_public_api_statistics_shape_review,
)


def _metric(avg: float, parses: int) -> dict[str, object]:
    return {
        "avg": avg,
        "median": avg - 1,
        "max": avg + 10,
        "min": avg - 10,
        "total_parses": parses,
        "percentiles": {"50": avg - 1, "95": avg + 5},
    }


def test_statistics_shape_review_is_scalar_safe_and_detects_metric_objects():
    payload = {
        "success": True,
        "phase": 91,
        "difficulty": "secret-difficulty",
        "statistics": {
            "PrivateClassAlpha": {
                "PrivateSpecOne": _metric(1234.5, 77),
                "PrivateSpecTwo": _metric(987.5, 31),
            },
            "PrivateClassBeta": {
                "PrivateSpecThree": _metric(456.0, 12),
            },
        },
    }

    review = build_public_api_statistics_shape_review(payload)

    assert review["response"]["statistics_kind"] == "object"
    assert review["response"]["statistics_top_level_entry_count"] == 2
    assert review["response"]["documented_metric_fields"]["avg"]["occurrence_count"] == 3
    assert review["response"]["documented_metric_fields"]["percentiles"]["occurrence_count"] == 3
    assert review["response"]["objects_with_documented_metric_fields"] == 3
    assert review["verification"]["statistics_normalization_ready"] is True
    assert review["public_release_safe"] is True

    rendered = repr(review)
    assert "PrivateClassAlpha" not in rendered
    assert "PrivateSpecOne" not in rendered
    assert "secret-difficulty" not in rendered


def test_statistics_shape_review_rejects_unsuccessful_payload():
    with pytest.raises(ValueError, match="not successful"):
        build_public_api_statistics_shape_review({"success": False, "statistics": {}})


def test_statistics_shape_review_requires_structured_statistics():
    with pytest.raises(ValueError, match="object or array"):
        build_public_api_statistics_shape_review({"success": True, "statistics": "private"})
