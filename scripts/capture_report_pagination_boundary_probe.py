from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector import (
    RawArchive,
    capture_report_pagination_boundary_probe,
    load_source_registry,
)


def _parse_pages(value: str) -> tuple[int, ...]:
    try:
        pages = tuple(int(item.strip()) for item in value.split(",") if item.strip())
    except ValueError as error:
        raise argparse.ArgumentTypeError("probe pages must be comma-separated integers") from error
    if not pages:
        raise argparse.ArgumentTypeError("probe pages cannot be empty")
    return pages


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Capture a fixed sparse public-report page set to bracket the pagination boundary "
            "without automatically crawling to the terminal page."
        )
    )
    parser.add_argument(
        "--semantic-review",
        type=Path,
        default=Path("data/exchange/out/argentum-report-pagination-semantic-review.json"),
    )
    parser.add_argument(
        "--baseline-private",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/argentum-report-pagination-evidence.private.json"
        ),
    )
    parser.add_argument("--guild-label", default="Argentum")
    parser.add_argument(
        "--probe-pages",
        type=_parse_pages,
        default=(4, 64, 1024, 8192, 65536),
    )
    parser.add_argument("--limit", type=int, default=5)
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
    parser.add_argument("--timeout-seconds", type=float, default=20.0)
    parser.add_argument("--retry-count", type=int, choices=(0, 1), default=1)
    parser.add_argument(
        "--private-output",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/argentum-report-pagination-boundary-probe.private.json"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/argentum-report-pagination-boundary-probe.json"),
    )
    args = parser.parse_args()

    registry = load_source_registry(args.registry)
    archive = RawArchive(
        args.raw_root,
        database_path=args.database,
        migrations_dir=args.migrations,
    )
    receipt = capture_report_pagination_boundary_probe(
        registry,
        archive,
        semantic_review_path=args.semantic_review,
        baseline_private_path=args.baseline_private,
        private_output_path=args.private_output,
        receipt_output_path=args.output,
        expected_guild_label=args.guild_label,
        probe_pages=args.probe_pages,
        limit=args.limit,
        timeout_seconds=args.timeout_seconds,
        retry_count=args.retry_count,
    )

    summary = receipt["summary"]
    print(
        "pagination boundary probe: "
        f"pages={summary['completed_probe_page_count']} "
        f"terminal_candidates={summary['has_more_false_probe_page_count']} "
        f"bracket={summary['terminal_bracket_observed']}"
    )
    print(f"private output: {args.private_output}")
    print(f"receipt output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
