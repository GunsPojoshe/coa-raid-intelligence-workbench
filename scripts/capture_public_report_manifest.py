from __future__ import annotations

import argparse
from pathlib import Path

from coa_workbench.collector import RawArchive, load_source_registry
from coa_workbench.collector.current_public_report_manifest import (
    capture_current_public_report_manifest,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Capture the current public-report page range into a resumable private manifest "
            "and a scalar-free integrity receipt. The manually promoted limit-25 contract "
            "reduces temporal drift; transport failures preserve the checkpoint."
        )
    )
    parser.add_argument(
        "--limit-promotion",
        type=Path,
        default=Path("evidence/real-data/argentum-report-pagination-limit-promotion.json"),
    )
    parser.add_argument(
        "--limit-probe-receipt",
        type=Path,
        default=Path("data/exchange/out/argentum-report-pagination-limit-probe.json"),
    )
    parser.add_argument(
        "--limit-probe-private",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/argentum-report-pagination-limit-probe.private.json"
        ),
    )
    parser.add_argument(
        "--terminal-receipt",
        type=Path,
        default=Path("data/exchange/out/argentum-report-pagination-terminal-search.json"),
    )
    parser.add_argument(
        "--terminal-private",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/"
            "argentum-report-pagination-terminal-search.private.json"
        ),
    )
    parser.add_argument(
        "--boundary-receipt",
        type=Path,
        default=Path("data/exchange/out/argentum-report-pagination-boundary-probe.json"),
    )
    parser.add_argument(
        "--boundary-private",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/argentum-report-pagination-boundary-probe.private.json"
        ),
    )
    parser.add_argument("--terminal-max-requests", type=int, default=20)
    parser.add_argument("--manifest-max-attempts", type=int, default=3)
    parser.add_argument("--refresh-terminal", action="store_true")
    parser.add_argument(
        "--mapping",
        type=Path,
        default=Path("config/mappings/coa_public_report_discovery_v1.json"),
    )
    parser.add_argument("--guild-label", default="Argentum")
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/argentum-public-report-manifest.checkpoint.json"
        ),
    )
    parser.add_argument(
        "--private-output",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/argentum-public-report-manifest.private.json"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/argentum-public-report-manifest.json"),
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
    parser.add_argument("--request-delay-seconds", type=float, default=0.15)
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()

    registry = load_source_registry(args.registry)
    archive = RawArchive(
        args.raw_root,
        database_path=args.database,
        migrations_dir=args.migrations,
    )

    if args.refresh_terminal or args.no_resume:
        for path in (args.checkpoint, args.private_output, args.output):
            path.unlink(missing_ok=True)

    last_manifest_progress = 0

    def progress(phase: str, current: int, total: int) -> None:
        nonlocal last_manifest_progress
        if phase == "manifest_page":
            if current == total or current - last_manifest_progress >= 25:
                print(f"manifest progress: page {current}/{total}", flush=True)
                last_manifest_progress = current
        else:
            print(f"{phase}: {current}/{total}", flush=True)

    receipt = capture_current_public_report_manifest(
        registry,
        archive,
        boundary_receipt_path=args.boundary_receipt,
        boundary_private_path=args.boundary_private,
        terminal_receipt_path=args.terminal_receipt,
        terminal_private_path=args.terminal_private,
        mapping_path=args.mapping,
        checkpoint_path=args.checkpoint,
        private_output_path=args.private_output,
        receipt_output_path=args.output,
        limit_promotion_path=args.limit_promotion,
        limit_probe_receipt_path=args.limit_probe_receipt,
        limit_probe_private_path=args.limit_probe_private,
        expected_guild_label=args.guild_label,
        terminal_max_requests=args.terminal_max_requests,
        manifest_max_attempts=args.manifest_max_attempts,
        timeout_seconds=args.timeout_seconds,
        retry_count=args.retry_count,
        request_delay_seconds=args.request_delay_seconds,
        progress_callback=progress,
        status_callback=lambda message: print(message, flush=True),
    )

    summary = receipt["summary"]
    guild_summary = receipt["guild_field_summary"]
    print(
        "public report manifest: "
        f"pages={summary['completed_page_count']} "
        f"reports={summary['report_occurrence_count']} "
        f"unique={summary['unique_report_id_count']} "
        f"argentum_matches={guild_summary['target_label_exact_match_report_count']}"
    )
    print(f"checkpoint: {args.checkpoint}")
    print(f"private output: {args.private_output}")
    print(f"receipt output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
