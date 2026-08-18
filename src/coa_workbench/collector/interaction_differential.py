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

INTERACTION_DIFFERENTIAL_VERSION = "interaction-differential-v2"

_RequestShape = tuple[str, str, tuple[str, ...]]


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _request_shape(observation: NetworkObservation) -> _RequestShape:
    return (observation.method, observation.route_shape, observation.request_body_keys)


def _shape_label(shape: _RequestShape) -> str:
    method, route_shape, _body_keys = shape
    return f"{method} {route_shape}"


def _group_observations(
    observations: Iterable[NetworkObservation],
) -> dict[_RequestShape, tuple[NetworkObservation, ...]]:
    grouped: dict[_RequestShape, list[NetworkObservation]] = defaultdict(list)
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


def _varied_keys(mappings: Iterable[dict[str, tuple[str, ...]]]) -> tuple[str, ...]:
    prepared = tuple(mappings)
    keys = set().union(*(mapping.keys() for mapping in prepared)) if prepared else set()
    return tuple(
        sorted(
            key
            for key in keys
            if len({_canonical_json(mapping.get(key, ())) for mapping in prepared}) > 1
        )
    )


def _varied_indexes(mappings: Iterable[dict[int, tuple[str, ...]]]) -> tuple[int, ...]:
    prepared = tuple(mappings)
    keys = set().union(*(mapping.keys() for mapping in prepared)) if prepared else set()
    return tuple(
        sorted(
            key
            for key in keys
            if len({_canonical_json(mapping.get(key, ())) for mapping in prepared}) > 1
        )
    )


def _burst_core(window: ActionNetworkWindow) -> dict[str, object]:
    groups = _group_observations(window.observations)
    routes: list[dict[str, object]] = []
    for shape in sorted(groups):
        method, route_shape, body_keys = shape
        routes.append(
            {
                "method": method,
                "route_shape": route_shape,
                "request_body_keys": list(body_keys),
                "response_structure_fingerprints": list(_response_fingerprints(groups[shape])),
            }
        )
    return {
        "network_silent": window.network_silent,
        "routes": routes,
    }


def _burst_signature(window: ActionNetworkWindow) -> str:
    return _sha256(_burst_core(window))


def _scalar_variation_evidence(
    windows: Iterable[ActionNetworkWindow],
) -> list[dict[str, object]]:
    prepared = tuple(windows)
    grouped_windows = [_group_observations(window.observations) for window in prepared]
    if not grouped_windows:
        return []

    common_shapes = set(grouped_windows[0])
    for groups in grouped_windows[1:]:
        common_shapes.intersection_update(groups)

    evidence: list[dict[str, object]] = []
    for shape in sorted(common_shapes):
        observations_per_window = [groups[shape] for groups in grouped_windows]
        query_keys = _varied_keys(_query_value_sets(items) for items in observations_per_window)
        body_keys = _varied_keys(
            _request_body_value_sets(items) for items in observations_per_window
        )
        path_indexes = _varied_indexes(
            _dynamic_path_value_sets(items) for items in observations_per_window
        )
        if not query_keys and not body_keys and not path_indexes:
            continue
        method, route_shape, request_body_keys = shape
        evidence.append(
            {
                "method": method,
                "route_shape": route_shape,
                "request_body_keys": list(request_body_keys),
                "query_value_keys_varied": list(query_keys),
                "request_body_value_keys_varied": list(body_keys),
                "dynamic_path_segment_indexes_varied": list(path_indexes),
            }
        )
    return evidence


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
            "semantic_status": "adjacent_structural_diagnostic_only",
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


def build_repetition_review(windows: Iterable[ActionNetworkWindow]) -> dict[str, object]:
    prepared = tuple(window for window in windows if window.action.kind != "baseline")
    by_group: dict[str, list[ActionNetworkWindow]] = defaultdict(list)
    signature_groups: dict[str, set[str]] = defaultdict(set)

    for window in prepared:
        control = window.action.control_code or window.action.kind
        transition = window.action.transition_code or window.action.kind
        group_code = f"{control}:{transition}"
        by_group[group_code].append(window)
        signature_groups[_burst_signature(window)].add(group_code)

    groups: list[dict[str, object]] = []
    candidate_count = 0
    scalar_variation_candidate_count = 0
    for group_code in sorted(by_group):
        group_windows = by_group[group_code]
        counts = Counter(_burst_signature(window) for window in group_windows)
        repeated: list[dict[str, object]] = []
        for signature, count in sorted(counts.items()):
            if count < 2:
                continue
            matching = tuple(
                window for window in group_windows if _burst_signature(window) == signature
            )
            negative_control_groups = sorted(signature_groups[signature] - {group_code})
            exclusive = not negative_control_groups
            variation_evidence = _scalar_variation_evidence(matching)
            scalar_variation_observed = bool(variation_evidence)
            candidate_count += int(exclusive)
            scalar_variation_candidate_count += int(exclusive and scalar_variation_observed)
            repeated.append(
                {
                    "burst_signature": signature,
                    "occurrence_count": count,
                    "exclusive_to_group": exclusive,
                    "negative_control_group_codes": negative_control_groups,
                    "scalar_variation_observed": scalar_variation_observed,
                    "scalar_variation_evidence": variation_evidence,
                    "semantic_status": "candidate_specific_structural_signature"
                    if exclusive
                    else "shared_structural_signature",
                }
            )
        groups.append(
            {
                "group_code": group_code,
                "action_count": len(group_windows),
                "repeated_signatures": repeated,
            }
        )

    return {
        "review_version": INTERACTION_DIFFERENTIAL_VERSION,
        "action_count": len(prepared),
        "group_count": len(groups),
        "exclusive_repeated_signature_count": candidate_count,
        "exclusive_repeated_signature_with_scalar_variation_count": (
            scalar_variation_candidate_count
        ),
        "groups": groups,
        "corroboration_basis": "intrinsic_action_request_burst",
        "adjacent_transition_delta_used_for_corroboration": False,
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
