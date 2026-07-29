from __future__ import annotations

import argparse
from pathlib import Path

from coa_workbench.collector import (
    RawArchive,
    capture_bounded_report_pagination_evidence,
    load_source_registry,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Capture an explicit consecutive /api/reports/public page window for pagination "
            "evidence. The private batch contains report IDs and pagination values; the receipt "
            "is scalar-free and does not enable full guild crawling or scoring."
        )
    )
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path("evidence/real-data/argentum-guild-report-collection-contract.json"),
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("config/ascension_logs_sources.yaml"),
    )
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    parser.add_argument("--database", type=Path, default=Path("data/warehouse/coa.duckdb"))
    parser.add_argument("--migrations", type=Path, default=Path("migrations"))
    parser.add_argument("--guild-label", default="Argentum")
    parser.add_argument("--start-page", type=int, default=1)
    parser.add_argument("--page-count", type=int, choices=range(2, 6), default=3)
    parser.add_argument("--limit", type=int, choices=(5,), default=5)
    parser.add_argument("--timeout-seconds", type=float, default=20.0)
    parser.add_argument("--retry-count", type=int, choices=(0, 1), default=0)
    parser.add_argument(
        "--private-output",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/argentum-report-pagination-evidence.private.json"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/argentum-report-pagination-evidence.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    registry = load_source_registry(args.registry)
    archive = RawArchive(
        args.raw_root,
        database_path=args.database,
        migrations_dir=args.migrations,
    )
    receipt = capture_bounded_report_pagination_evidence(
        registry,
        archive,
        contract_path=args.contract,
        private_output_path=args.private_output,
        receipt_output_path=args.output,
        expected_guild_label=args.guild_label,
        start_page=args.start_page,
        page_count=args.page_count,
        limit=args.limit,
        timeout_seconds=args.timeout_seconds,
        retry_count=args.retry_count,
    )

    summary = receipt["summary"]
    boundary = receipt["decision_boundary"]
    print("BOUNDED_REPORT_PAGINATION_EVIDENCE")
    print(f"schema_version={receipt['schema_version']}")
    print(f"evidence_kind={receipt['evidence_kind']}")
    print(f"completed_page_count={summary['completed_page_count']}")
    print(f"report_occurrence_count={summary['report_occurrence_count']}")
    print(f"unique_report_id_count={summary['unique_report_id_count']}")
    print(f"duplicate_report_occurrence_count={summary['duplicate_report_occurrence_count']}")
    print(f"empty_page_count={summary['empty_page_count']}")
    print(
        "ready_for_manual_pagination_field_review="
        f"{str(summary['ready_for_manual_pagination_field_review']).lower()}"
    )
    print(f"ready_for_full_guild_crawl={str(boundary['ready_for_full_guild_crawl']).lower()}")
    print(f"ready_for_bis25_scoring={str(boundary['ready_for_bis25_scoring']).lower()}")
    print(f"private_output={args.private_output.as_posix()}")
    print(f"output={args.output.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
