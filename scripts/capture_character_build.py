from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector import (
    RawArchive,
    build_page_capture_to_dict,
    capture_character_build_pages,
    load_source_registry,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Capture public character-build and armory pages into the immutable raw archive."
        )
    )
    parser.add_argument("--character", required=True)
    parser.add_argument("--realm", required=True)
    parser.add_argument("--spec")
    parser.add_argument("--phase", type=int, default=0)
    parser.add_argument("--location", default="World Bosses")
    parser.add_argument("--difficulty", default="normal")
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
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    registry = load_source_registry(args.registry)
    archive = RawArchive(
        args.raw_root,
        database_path=args.database,
        migrations_dir=args.migrations,
    )
    results = capture_character_build_pages(
        registry,
        archive,
        character=args.character,
        realm=args.realm,
        phase=args.phase,
        location=args.location,
        difficulty=args.difficulty,
        spec=args.spec,
        timeout_seconds=args.timeout_seconds,
    )
    payload = {
        "character": args.character,
        "realm": args.realm,
        "spec": args.spec,
        "pages": [build_page_capture_to_dict(item) for item in results],
    }
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")

    failed = [
        item
        for item in results
        if item.error or item.status is None or item.status >= 400 or item.capture is None
    ]
    return 4 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
