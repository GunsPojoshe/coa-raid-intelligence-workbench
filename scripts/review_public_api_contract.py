from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.public_api_contract import build_public_api_contract_review
from coa_workbench.collector.source_registry import load_source_registry


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Review an official CoA Ascension Logs OpenAPI document and cross-check it against "
            "the local documented public-API registry. No API key or network request is required."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Local OpenAPI JSON document downloaded from the official /openapi.json endpoint.",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("config/coa_public_api_sources.yaml"),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("OpenAPI document must be a JSON object")

    registry = load_source_registry(args.registry)
    result = build_public_api_contract_review(payload, registry=registry)
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
