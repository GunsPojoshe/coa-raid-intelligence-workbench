from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from coa_workbench.collector.har_observation_source import load_har_network_observations
from coa_workbench.collector.interaction_session import (
    ActionMarker,
    build_public_interaction_review,
)

_PUBLIC_CODE = re.compile(r"^[a-z][a-z0-9_.-]{0,79}$")


def _optional_public_code(raw: dict[str, Any], key: str, index: int) -> str | None:
    value = raw.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not _PUBLIC_CODE.fullmatch(value):
        raise ValueError(f"actions[{index}].{key} must match {_PUBLIC_CODE.pattern} or be null")
    return value


def _load_actions(path: Path) -> tuple[ActionMarker, ...]:
    payload: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("action manifest must contain a JSON object")
    raw_actions = payload.get("actions")
    if not isinstance(raw_actions, list):
        raise ValueError("action manifest actions must be an array")

    actions: list[ActionMarker] = []
    for index, raw in enumerate(raw_actions):
        if not isinstance(raw, dict):
            raise ValueError(f"actions[{index}] must be an object")
        action_id = raw.get("action_id")
        observed_at = raw.get("observed_at")
        kind = raw.get("kind")
        if not isinstance(action_id, str) or not action_id:
            raise ValueError(f"actions[{index}].action_id must be a non-empty string")
        if not isinstance(observed_at, str) or not observed_at:
            raise ValueError(f"actions[{index}].observed_at must be a non-empty string")
        if not isinstance(kind, str) or not kind:
            raise ValueError(f"actions[{index}].kind must be a non-empty string")
        private_label = raw.get("private_label")
        if private_label is not None and not isinstance(private_label, str):
            raise ValueError(f"actions[{index}].private_label must be a string or null")
        actions.append(
            ActionMarker(
                action_id=action_id,
                observed_at=observed_at,
                kind=kind,
                private_label=private_label,
                control_code=_optional_public_code(raw, "control_code", index),
                transition_code=_optional_public_code(raw, "transition_code", index),
            )
        )
    return tuple(actions)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build a scalar-safe UI-action to Network differential review from a private HAR "
            "and action manifest. Private action labels and scalar request/response values are "
            "not copied into the output."
        )
    )
    parser.add_argument("har", type=Path)
    parser.add_argument("actions", type=Path)
    parser.add_argument("--allowed-host", default="coa.ascensionlogs.gg")
    parser.add_argument("--api-prefix", default="/api/")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    observations = load_har_network_observations(
        args.har,
        allowed_host=args.allowed_host,
        api_prefix=args.api_prefix,
    )
    actions = _load_actions(args.actions)
    result = build_public_interaction_review(actions, observations)
    result["source"] = {
        "observation_source": "har",
        "har_path_included": False,
        "action_manifest_path_included": False,
        "network_requests_performed": False,
    }

    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
