from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector import (
    ARMORY_ENDPOINT_KINDS,
    RawArchive,
    capture_armory_endpoints_progressively,
    load_source_registry,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Capture selected public Armory API endpoints independently, archive completed JSON "
            "responses, and update a resumable privacy-safe progress manifest after each endpoint."
        )
    )
    parser.add_argument("--character-id", required=True)
    parser.add_argument("--class-slug", required=True)
    parser.add_argument(
        "--endpoint",
        action="append",
        choices=ARMORY_ENDPOINT_KINDS,
        dest="endpoints",
        help="Endpoint kind to capture. Repeat to select multiple endpoints.",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("config/ascension_logs_sources.yaml"),
    )
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("data/warehouse/coa.duckdb"),
    )
    parser.add_argument("--migrations", type=Path, default=Path("migrations"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/armory-endpoint-capture.json"),
    )
    parser.add_argument("--timeout-seconds", type=float, default=20.0)
    parser.add_argument("--retry-count", type=int, choices=(0, 1), default=0)
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()

    registry = load_source_registry(args.registry)
    archive = RawArchive(
        args.raw_root,
        database_path=args.database,
        migrations_dir=args.migrations,
    )
    result = capture_armory_endpoints_progressively(
        registry,
        archive,
        character_id=args.character_id,
        class_slug=args.class_slug,
        output_path=args.output,
        endpoint_kinds=args.endpoints or ARMORY_ENDPOINT_KINDS,
        timeout_seconds=args.timeout_seconds,
        retry_count=args.retry_count,
        resume=not args.no_resume,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["summary"]["complete"] else 4


if __name__ == "__main__":
    raise SystemExit(main())
