from __future__ import annotations

import json

from coa_workbench.collector.interaction_session import (
    ActionMarker,
    build_public_interaction_review,
    correlate_actions_with_network,
)
from coa_workbench.collector.network_observation import NetworkObservation


def _observation(ordinal: int, observed_at: str, path: str) -> NetworkObservation:
    return NetworkObservation(
        ordinal=ordinal,
        observed_at=observed_at,
        method="GET",
        url=f"https://coa.ascensionlogs.gg{path}",
        status=200,
        response_content_type="application/json",
        response_body=b'{"success":true}',
        source_kind="har",
    )


def test_action_windows_include_network_silent_transitions() -> None:
    actions = (
        ActionMarker(
            action_id="a1",
            observed_at="2026-08-19T00:00:01Z",
            kind="difficulty_change",
            private_label="private difficulty value",
        ),
        ActionMarker(
            action_id="a2",
            observed_at="2026-08-19T00:00:03Z",
            kind="tab_change",
            private_label="Summary",
        ),
        ActionMarker(
            action_id="a3",
            observed_at="2026-08-19T00:00:05Z",
            kind="boss_change",
            private_label="Private Boss",
        ),
    )
    observations = (
        _observation(0, "2026-08-19T00:00:00Z", "/api/background"),
        _observation(1, "2026-08-19T00:00:02Z", "/api/reports/123"),
        _observation(2, "2026-08-19T00:00:06Z", "/api/reports/123/encounters/456"),
    )

    windows = correlate_actions_with_network(actions, observations)

    assert [len(window.observations) for window in windows] == [1, 0, 1]
    assert windows[1].network_silent is True

    review = build_public_interaction_review(actions, observations)
    rendered = json.dumps(review, sort_keys=True)
    assert review["action_count"] == 3
    assert review["network_silent_action_count"] == 1
    assert "private difficulty value" not in rendered
    assert "Summary" not in rendered
    assert "Private Boss" not in rendered
    assert review["semantic_promotion_performed"] is False


def test_action_ids_must_be_unique() -> None:
    actions = (
        ActionMarker("same", "2026-08-19T00:00:01Z", "first"),
        ActionMarker("same", "2026-08-19T00:00:02Z", "second"),
    )

    try:
        correlate_actions_with_network(actions, ())
    except ValueError as exc:
        assert str(exc) == "action IDs must be unique"
    else:
        raise AssertionError("expected ValueError")
