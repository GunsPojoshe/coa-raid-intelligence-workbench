from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from coa_workbench.collector.network_observation import NetworkObservation

INTERACTION_SESSION_VERSION = "interaction-session-v1"


def _timestamp(value: str) -> datetime:
    prepared = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(prepared)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("interaction timestamps must include a timezone")
    return parsed


@dataclass(frozen=True, slots=True)
class ActionMarker:
    action_id: str
    observed_at: str
    kind: str
    private_label: str | None = None

    def public_summary(self) -> dict[str, object]:
        return {
            "action_id": self.action_id,
            "observed_at": self.observed_at,
            "kind": self.kind,
            "private_label_included": False,
        }


@dataclass(frozen=True, slots=True)
class ActionNetworkWindow:
    action: ActionMarker
    observations: tuple[NetworkObservation, ...]

    @property
    def network_silent(self) -> bool:
        return not self.observations

    def public_summary(self) -> dict[str, object]:
        route_shapes = sorted({item.route_shape for item in self.observations})
        return {
            "action": self.action.public_summary(),
            "network_silent": self.network_silent,
            "observation_count": len(self.observations),
            "route_shapes": route_shapes,
            "privacy": {
                "private_action_label_included": False,
                "request_values_included": False,
                "response_values_included": False,
            },
        }


def correlate_actions_with_network(
    actions: Iterable[ActionMarker],
    observations: Iterable[NetworkObservation],
) -> tuple[ActionNetworkWindow, ...]:
    """Assign each observation to the most recent action marker.

    The next action marker closes the previous action's window. Traffic before the first action is not
    assigned; callers can preserve it separately as baseline traffic.
    """

    prepared_actions = sorted(actions, key=lambda item: (_timestamp(item.observed_at), item.action_id))
    if len({item.action_id for item in prepared_actions}) != len(prepared_actions):
        raise ValueError("action IDs must be unique")

    prepared_observations = sorted(
        observations,
        key=lambda item: (_timestamp(item.observed_at), item.ordinal),
    )
    buckets: dict[str, list[NetworkObservation]] = {
        action.action_id: [] for action in prepared_actions
    }

    action_index = -1
    for observation in prepared_observations:
        observation_time = _timestamp(observation.observed_at)
        while (
            action_index + 1 < len(prepared_actions)
            and _timestamp(prepared_actions[action_index + 1].observed_at) <= observation_time
        ):
            action_index += 1
        if action_index >= 0:
            buckets[prepared_actions[action_index].action_id].append(observation)

    return tuple(
        ActionNetworkWindow(action=action, observations=tuple(buckets[action.action_id]))
        for action in prepared_actions
    )


def build_public_interaction_review(
    actions: Iterable[ActionMarker],
    observations: Iterable[NetworkObservation],
) -> dict[str, object]:
    windows = correlate_actions_with_network(actions, observations)
    return {
        "review_version": INTERACTION_SESSION_VERSION,
        "action_count": len(windows),
        "network_silent_action_count": sum(window.network_silent for window in windows),
        "windows": [window.public_summary() for window in windows],
        "semantic_promotion_performed": False,
        "privacy": {
            "private_action_labels_included": False,
            "concrete_urls_included": False,
            "query_values_included": False,
            "request_bodies_included": False,
            "response_bodies_included": False,
        },
    }


__all__ = [
    "INTERACTION_SESSION_VERSION",
    "ActionMarker",
    "ActionNetworkWindow",
    "build_public_interaction_review",
    "correlate_actions_with_network",
]
