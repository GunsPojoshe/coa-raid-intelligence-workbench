from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import parse_qsl, urlsplit

from coa_workbench.collector.interaction_session import ActionNetworkWindow
from coa_workbench.collector.network_observation import NetworkObservation
from coa_workbench.collector.spa_route_inventory import normalize_api_route_shape

INTERACTION_DIFFERENTIAL_VERSION = "interaction-differential-v1"


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _request_shape(observation: NetworkObservation) -> tuple[str, str, tuple[str, ...]]:
    return (observation.method, observation.route_shape, observation.request_body_keys)


def _shape_label(shape: tuple[str, str, tuple[str, ...]]) -> str:
    method, route_shape, _body_keys = shape
    return f"{method} {route_shape}"


def _group_observations(
    observations: Iterable[NetworkObservation],
) -> dict[tuple[str, str, tuple[str, ...]], tuple[NetworkObservation, ...]]:
    grouped: dict[tuple[str, str, tuple[str, ...]], list[NetworkObservation]] = defaultdict(list)
    for observation in observations:
        grouped[_request_shape(observation)].append(observation)
    return {key: tuple(value) for key, value in grouped.items()}


def _query_value_sets(
    observations: Iterable[NetworkObservation],
) -> dict[str, tuple[str, ...]]:
    values: dict[str, set[str]] = defaultdict(set)
    for observation in observations:
        for key, value in parse_qsl(urlsplit(observation.url).query, keep_blank_values=True):
            values[key].add(value)
    return {key: tuple(sorted(items)) for key, items in values.items()}


def _request_body_value_sets(
    observations: Iterable[NetworkObservation],
) -> dict[str, tuple[str, ...]]:
    values: dict[str, set[str]] = defaultdict(set)
    for observation in observations:
        if observation.request_body is None:
            continue
        try:
            payload = json.loads(observation.request_body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        for key, value in payload.items():
            values[str(key)].add(_canonical_json(value))
    return {key: tuple(sorted(items)) for key, items in values.items()}


def _dynamic_path_value_sets(
    observations: Iterable[NetworkObservation],
) -> dict[int, tuple[str, ...]]:
    values: dict[int, set[str]] = defaultdict(set)
    for observation in observations:
        concrete_segments = observation.path.split("/")
        normalized_segments = normalize_api_route_shape(observation.path).split("/")
        if len(concrete_segments) != len(normalized_segments):
            continue
        for index, (concrete, normalized) in enumerate(
            zip(concrete_segments, normalized_segments, strict=True)
        ):
            if concrete != normalized:
                values[index].add(concrete)
    return {index: tuple(sorted(items)) for index, items in values.items()}


def _response_fingerprints(observations: Iterable[NetworkObservation]) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                fingerprint
                for observation in observations
                if (fingerprint := observation.response_structure_fingerprint) is not None
            }
        )
    )


def _changed_keys(
    before: dict[str, tuple[str, ...]],
    after: dict[str, tuple[str, ...]],
) -> tuple[str, ...]:
    return tuple(sorted(key for key in set(before) | set(after) if before.get(key) != after.get(key)))


def _changed_indexes(
    before: dict[int, tuple[str, ...]],
    after: dict[int, tuple[str, ...]],
) -> tuple[int, ...]:
    return tuple(sorted(key for key in set(before) | set(after) if before.get(key) != after.get(key)))


@dataclass(frozen=True, slots=True)
class RouteTransitionDelta:
    method: str
    route_shape: str
    request_body_keys: tuple[str, ...]
    query_value_keys_changed: tuple[str, ...]
    request_body_value_keys_changed: tuple[str, ...]
    dynamic_path_segment_indexes_changed: tuple[int, ...]
    response_structure_changed: bool
    occurrence_count_changed: bool

    @property
    def changed(self) -> bool:
        return bool(
            self.query_value_keys_changed
            or self.request_body_value_keys_changed
            or self.dynamic_path_segment_indexes_changed
            or self.response_structure_changed
            or self.occurrence_count_changed
        )

    def public_summary(self) -> dict[str, object]:
        return {
            "method": self.method,
            "route_shape": self.route_shape,
            "request_body_keys": list(self.request_body_keys),
            "query_value_keys_changed": list(self.query_value_keys_changed),
            "request_body_value_keys_changed": list(self.request_body_value_keys_changed),
            "dynamic_path_segment_indexes_changed": list(
                self.dynamic_path_segment_indexes_changed
            ),
            "response_structure_changed": self.response_structure_changed,
            "occurrence_count_changed": self.occurrence_count_changed,
        }


@dataclass(frozen=True, slots=True)
class TransitionDelta:
    previous_action_id: str
    action_id: str
    action_kind: str
    control_code: str | None
    transition_code: str | None
    network_silent: bool
    added_request_shapes: tuple[str, ...]
    removed_request_shapes: tuple[str, ...]
    changed_routes: tuple[RouteTransitionDelta, ...]

    @property
    def group_code(self) -> str:
        control = self.control_code or self.action_kind
        transition = self.transition_code or self.action_kind
        return f"{control}:{transition}"

    def _signature_core(self) -> dict[str, object]:
        return {
            "network_silent": self.network_silent,
            "added_request_shapes": list(self.added_request_shapes),
            "removed_request_shapes": list(self.removed_request_shapes),
            "changed_routes": [item.public_summary() for item in self.changed_routes],
        }

    @property
    def delta_signature(self) -> str:
        return _sha256(self._signature_core())

    def public_summary(self) -> dict[str, object]:
        return {
            "previous_action_id": self.previous_action_id,
            "action_id": self.action_id,
            "action_kind": self.action_kind,
            "control_code": self.control_code,
            "transition_code": self.transition_code,
            "group_code": self.group_code,
            "network_silent": self.network_silent,
            "added_request_shapes": list(self.added_request_shapes),
            "removed_request_shapes": list(self.removed_request_shapes),
            "changed_routes": [item.public_summary() for item in self.changed_routes],
            "delta_signature": self.delta_signature,
            "semantic_status": "structural_transition_only",
        }


def compare_action_windows(
    before: ActionNetworkWindow,
    after: ActionNetworkWindow,
) -> TransitionDelta:
    before_groups = _group_observations(before.observations)
    after_groups = _group_observations(after.observations)
    before_shapes = set(before_groups)
    after_shapes = set(after_groups)

    changed_routes: list[RouteTransitionDelta] = []
    for shape in sorted(before_shapes & after_shapes):
        before_observations = before_groups[shape]
        after_observations = after_groups[shape]
        method, route_shape, body_keys = shape
        route_delta = RouteTransitionDelta(
            method=method,
            route_shape=route_shape,
            request_body_keys=body_keys,
            query_value_keys_changed=_changed_keys(
                _query_value_sets(before_observations),
                _query_value_sets(after_observations),
            ),
            request_body_value_keys_changed=_changed_keys(
                _request_body_value_sets(before_observations),
                _request_body_value_sets(after_observations),
            ),
            dynamic_path_segment_indexes_changed=_changed_indexes(
                _dynamic_path_value_sets(before_observations),
                _dynamic_path_value_sets(after_observations),
            ),
            response_structure_changed=(
                _response_fingerprints(before_observations)
                != _response_fingerprints(after_observations)
            ),
            occurrence_count_changed=len(before_observations) != len(after_observations),
        )
        if route_delta.changed:
            changed_routes.append(route_delta)

    action = after.action
    return TransitionDelta(
        previous_action_id=before.action.action_id,
        action_id=action.action_id,
        action_kind=action.kind,
        control_code=action.control_code,
        transition_code=action.transition_code,
        network_silent=after.network_silent,
        added_request_shapes=tuple(sorted(_shape_label(shape) for shape in after_shapes - before_shapes)),
        removed_request_shapes=tuple(
            sorted(_shape_label(shape) for shape in before_shapes - after_shapes)
        ),
        changed_routes=tuple(changed_routes),
    )


def build_transition_deltas(
    windows: Iterable[ActionNetworkWindow],
) -> tuple[TransitionDelta, ...]:
    prepared = tuple(windows)
    return tuple(
        compare_action_windows(before, after)
        for before, after in zip(prepared, prepared[1:], strict=False)
    )


def build_repetition_review(deltas: Iterable[TransitionDelta]) -> dict[str, object]:
    prepared = tuple(deltas)
    by_group: dict[str, list[TransitionDelta]] = defaultdict(list)
    for delta in prepared:
        by_group[delta.group_code].append(delta)

    signature_groups: dict[str, set[str]] = defaultdict(set)
    for delta in prepared:
        signature_groups[delta.delta_signature].add(delta.group_code)

    groups: list[dict[str, object]] = []
    candidate_count = 0
    for group_code in sorted(by_group):
        counts = Counter(delta.delta_signature for delta in by_group[group_code])
        repeated: list[dict[str, object]] = []
        for signature, count in sorted(counts.items()):
            if count < 2:
                continue
            negative_control_groups = sorted(signature_groups[signature] - {group_code})
            exclusive = not negative_control_groups
            candidate_count += int(exclusive)
            repeated.append(
                {
                    "delta_signature": signature,
                    "occurrence_count": count,
                    "exclusive_to_group": exclusive,
                    "negative_control_group_codes": negative_control_groups,
                    "semantic_status": "candidate_specific_structural_signature"
                    if exclusive
                    else "shared_structural_signature",
                }
            )
        groups.append(
            {
                "group_code": group_code,
                "transition_count": len(by_group[group_code]),
                "repeated_signatures": repeated,
            }
        )

    return {
        "review_version": INTERACTION_DIFFERENTIAL_VERSION,
        "transition_count": len(prepared),
        "group_count": len(groups),
        "exclusive_repeated_signature_count": candidate_count,
        "groups": groups,
        "semantic_promotion_performed": False,
    }


__all__ = [
    "INTERACTION_DIFFERENTIAL_VERSION",
    "RouteTransitionDelta",
    "TransitionDelta",
    "build_repetition_review",
    "build_transition_deltas",
    "compare_action_windows",
]
