from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector import (
    RawArchive,
    capture_public_report_discovery,
    load_source_registry,
    report_discovery_capture_to_dict,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Capture one explicitly bounded /api/reports/public page, archive the exact JSON "
            "response, and write a compact structural result without report scalar values."
        )
    )
    parser.add_argument("--local-category", default="public_recent")
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--limit", type=int, choices=range(1, 6), default=5)
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
        default=Path("data/exchange/out/report-discovery-page.json"),
    )
    parser.add_argument("--timeout-seconds", type=float, default=20.0)
    parser.add_argument("--retry-count", type=int, choices=(0, 1), default=0)
    args = parser.parse_args()

    registry = load_source_registry(args.registry)
    archive = RawArchive(
        args.raw_root,
        database_path=args.database,
        migrations_dir=args.migrations,
    )
    result = capture_public_report_discovery(
        registry,
        archive,
        local_category=args.local_category,
        page=args.page,
        limit=args.limit,
        timeout_seconds=args.timeout_seconds,
        retry_count=args.retry_count,
    )
    payload = report_discovery_capture_to_dict(result)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(args.output)
    print(rendered, end="")
    return 0 if result.complete else 4


if __name__ == "__main__":
    raise SystemExit(main())
