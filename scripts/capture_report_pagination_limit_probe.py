from __future__ import annotations

import argparse
from pathlib import Path

from coa_workbench.collector import (
    RawArchive,
    capture_report_pagination_limit_probe,
    load_source_registry,
)


def _parse_limits(value: str) -> tuple[int, ...]:
    try:
        limits = tuple(int(item.strip()) for item in value.split(",") if item.strip())
    except ValueError as error:
        raise argparse.ArgumentTypeError("limits must be comma-separated integers") from error
    if not limits:
        raise argparse.ArgumentTypeError("limits cannot be empty")
    return limits


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Probe larger public-report page limits without changing the verified production "
            "limit or starting a full manifest crawl."
        )
    )
    parser.add_argument("--guild-label", default="Argentum")
    parser.add_argument(
        "--limits",
        type=_parse_limits,
        default=(5, 25, 50, 100, 250, 500),
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
    parser.add_argument("--timeout-seconds", type=float, default=20.0)
    parser.add_argument("--retry-count", type=int, choices=(0, 1), default=1)
    parser.add_argument(
        "--private-output",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/argentum-report-pagination-limit-probe.private.json"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/argentum-report-pagination-limit-probe.json"),
    )
    args = parser.parse_args()

    registry = load_source_registry(args.registry)
    archive = RawArchive(
        args.raw_root,
        database_path=args.database,
        migrations_dir=args.migrations,
    )
    receipt = capture_report_pagination_limit_probe(
        registry,
        archive,
        private_output_path=args.private_output,
        receipt_output_path=args.output,
        expected_guild_label=args.guild_label,
        candidates=args.limits,
        timeout_seconds=args.timeout_seconds,
        retry_count=args.retry_count,
    )

    summary = receipt["summary"]
    print(
        "pagination limit probe: "
        f"candidates={summary['candidate_count']} "
        f"supported={summary['observed_supported_limit_count']} "
        f"selected={summary['selected_limit_candidate']}"
    )
    print(f"private output: {args.private_output}")
    print(f"receipt output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
