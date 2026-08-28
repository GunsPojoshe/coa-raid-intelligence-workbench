from __future__ import annotations

import json

from coa_workbench.collector.interaction_differential import (
    build_repetition_review,
    compare_action_windows,
)
from coa_workbench.collector.interaction_session import ActionMarker, ActionNetworkWindow
from coa_workbench.collector.network_observation import NetworkObservation


def _observation(
    ordinal: int,
    observed_at: str,
    url: str,
    *,
    request_body: bytes | None = None,
    response_body: bytes = b'{"rows":[{"amount":1}]}',
) -> NetworkObservation:
    return NetworkObservation(
        ordinal=ordinal,
        observed_at=observed_at,
        method="GET",
        url=url,
        status=200,
        request_content_type="application/json" if request_body is not None else None,
        response_content_type="application/json",
        request_body=request_body,
        response_body=response_body,
        resource_type="xhr",
        source_kind="har",
    )


def _window(
    action_id: str,
    observed_at: str,
    observation: NetworkObservation,
    *,
    control_code: str,
    transition_code: str = "change",
    kind: str = "select",
) -> ActionNetworkWindow:
    return ActionNetworkWindow(
        action=ActionMarker(
            action_id=action_id,
            observed_at=observed_at,
            kind=kind,
            control_code=control_code,
            transition_code=transition_code,
        ),
        observations=(observation,),
    )


def test_transition_delta_reports_changed_query_keys_without_values() -> None:
    before = _window(
        "baseline",
        "2026-08-19T00:00:01Z",
        _observation(
            1,
            "2026-08-19T00:00:02Z",
            "https://coa.ascensionlogs.gg/api/reports/100?difficulty=private-before",
        ),
        control_code="baseline",
    )
    after = _window(
        "difficulty-1",
        "2026-08-19T00:00:03Z",
        _observation(
            2,
            "2026-08-19T00:00:04Z",
            "https://coa.ascensionlogs.gg/api/reports/100?difficulty=private-after",
        ),
        control_code="difficulty",
    )

    delta = compare_action_windows(before, after)

    assert delta.added_request_shapes == ()
    assert delta.removed_request_shapes == ()
    assert len(delta.changed_routes) == 1
    assert delta.changed_routes[0].query_value_keys_changed == ("difficulty",)
    rendered = json.dumps(delta.public_summary(), sort_keys=True)
    assert "private-before" not in rendered
    assert "private-after" not in rendered
    assert "/api/reports/100" not in rendered


def test_transition_delta_reports_dynamic_path_and_body_key_changes() -> None:
    before = _window(
        "boss-1",
        "2026-08-19T00:00:01Z",
        _observation(
            1,
            "2026-08-19T00:00:02Z",
            "https://coa.ascensionlogs.gg/api/reports/100/encounters/200",
            request_body=b'{"encounterId":"private-boss-a","mode":"summary"}',
        ),
        control_code="boss",
    )
    after = _window(
        "boss-2",
        "2026-08-19T00:00:03Z",
        _observation(
            2,
            "2026-08-19T00:00:04Z",
            "https://coa.ascensionlogs.gg/api/reports/100/encounters/300",
            request_body=b'{"encounterId":"private-boss-b","mode":"summary"}',
        ),
        control_code="boss",
    )

    delta = compare_action_windows(before, after)
    route = delta.changed_routes[0]

    assert route.dynamic_path_segment_indexes_changed == (5,)
    assert route.request_body_value_keys_changed == ("encounterId",)
    assert route.response_structure_changed is False
    rendered = json.dumps(delta.public_summary(), sort_keys=True)
    assert "private-boss-a" not in rendered
    assert "private-boss-b" not in rendered
    assert "/encounters/200" not in rendered
    assert "/encounters/300" not in rendered


def test_repetition_review_uses_intrinsic_bursts_not_previous_action() -> None:
    baseline = _window(
        "baseline",
        "2026-08-19T00:00:01Z",
        _observation(
            1,
            "2026-08-19T00:00:02Z",
            "https://coa.ascensionlogs.gg/api/background",
        ),
        control_code="baseline",
        transition_code="baseline",
        kind="baseline",
    )
    difficulty_one = _window(
        "difficulty-1",
        "2026-08-19T00:00:03Z",
        _observation(
            2,
            "2026-08-19T00:00:04Z",
            "https://coa.ascensionlogs.gg/api/reports/100?difficulty=private-a",
        ),
        control_code="difficulty",
    )
    unrelated_between = _window(
        "boss-1",
        "2026-08-19T00:00:05Z",
        _observation(
            3,
            "2026-08-19T00:00:06Z",
            "https://coa.ascensionlogs.gg/api/reports/100/encounters/200",
        ),
        control_code="boss",
    )
    difficulty_two = _window(
        "difficulty-2",
        "2026-08-19T00:00:07Z",
        _observation(
            4,
            "2026-08-19T00:00:08Z",
            "https://coa.ascensionlogs.gg/api/reports/100?difficulty=private-b",
        ),
        control_code="difficulty",
    )

    review = build_repetition_review(
        (baseline, difficulty_one, unrelated_between, difficulty_two)
    )
    difficulty = next(
        group for group in review["groups"] if group["group_code"] == "difficulty:change"
    )

    assert review["corroboration_basis"] == "intrinsic_action_request_burst"
    assert review["adjacent_transition_delta_used_for_corroboration"] is False
    assert len(difficulty["repeated_signatures"]) == 1
    repeated = difficulty["repeated_signatures"][0]
    assert repeated["occurrence_count"] == 2
    assert repeated["exclusive_to_group"] is True
    assert repeated["negative_control_group_codes"] == []
    assert repeated["scalar_variation_observed"] is True
    evidence = repeated["scalar_variation_evidence"]
    assert evidence[0]["query_value_keys_varied"] == ["difficulty"]
    rendered = json.dumps(review, sort_keys=True)
    assert "private-a" not in rendered
    assert "private-b" not in rendered
    assert "/api/reports/100" not in rendered


def test_repetition_review_rejects_signature_shared_by_negative_control() -> None:
    windows = (
        _window(
            "difficulty-1",
            "2026-08-19T00:00:01Z",
            _observation(
                1,
                "2026-08-19T00:00:02Z",
                "https://coa.ascensionlogs.gg/api/reports/100?difficulty=a",
            ),
            control_code="difficulty",
        ),
        _window(
            "difficulty-2",
            "2026-08-19T00:00:03Z",
            _observation(
                2,
                "2026-08-19T00:00:04Z",
                "https://coa.ascensionlogs.gg/api/reports/100?difficulty=b",
            ),
            control_code="difficulty",
        ),
        _window(
            "tab-1",
            "2026-08-19T00:00:05Z",
            _observation(
                3,
                "2026-08-19T00:00:06Z",
                "https://coa.ascensionlogs.gg/api/reports/100?difficulty=c",
            ),
            control_code="tab",
        ),
    )

    review = build_repetition_review(windows)
    difficulty = next(
        group for group in review["groups"] if group["group_code"] == "difficulty:change"
    )
    repeated = difficulty["repeated_signatures"][0]

    assert repeated["exclusive_to_group"] is False
    assert repeated["negative_control_group_codes"] == ["tab:change"]
    assert review["exclusive_repeated_signature_count"] == 0
    assert review["exclusive_repeated_signature_with_scalar_variation_count"] == 0
