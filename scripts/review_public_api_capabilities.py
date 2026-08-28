from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.public_api_capability import (
    probe_public_api_capabilities,
    public_api_capability_probe_to_dict,
)
from coa_workbench.collector.public_api_credentials import (
    DEFAULT_PUBLIC_API_KEY_ENV,
    DEFAULT_PUBLIC_API_KEY_FILE,
    load_public_api_key,
)
from coa_workbench.collector.source_registry import load_source_registry


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Probe the documented official Public API capabilities of the local API key. "
            "Runs one stats:read request and one minimal events:read request. The receipt "
            "contains no API key, report IDs, titles, encounter IDs, player names or event values."
        )
    )
    parser.add_argument(
        "--api-key-file",
        type=Path,
        default=DEFAULT_PUBLIC_API_KEY_FILE,
        help="Ignored local API-key file. The key value is never printed.",
    )
    parser.add_argument(
        "--api-key-env",
        default=DEFAULT_PUBLIC_API_KEY_ENV,
        help="Fallback API-key environment variable. The value is never printed.",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("config/coa_public_api_sources.yaml"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/coa-public-api-capability-review.json"),
    )
    parser.add_argument("--timeout-seconds", type=float, default=20.0)
    parser.add_argument("--retry-count", type=int, choices=(0, 1), default=0)
    args = parser.parse_args()

    try:
        api_key = load_public_api_key(key_file=args.api_key_file, env_name=args.api_key_env)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    registry = load_source_registry(args.registry)
    result = probe_public_api_capabilities(
        registry,
        api_key=api_key,
        timeout_seconds=args.timeout_seconds,
        retry_count=args.retry_count,
    )
    rendered = public_api_capability_probe_to_dict(result)
    text = json.dumps(rendered, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    print(text, end="")

    if result.events_read_available:
        return 0
    if result.access_request_required:
        return 4
    return 5


if __name__ == "__main__":
    raise SystemExit(main())
