from __future__ import annotations

import argparse
from pathlib import Path

from coa_workbench.collector import RawArchive, load_source_registry
from coa_workbench.collector.guild_identity_search_access_diagnostic import (
    capture_guild_identity_search_access_diagnostic,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Capture bounded HTTP 403 bodies and test no-credential browser-like profiles "
            "for the recovered guild search route. This does not verify guild identity."
        )
    )
    parser.add_argument(
        "--search-probe-receipt",
        type=Path,
        default=Path("evidence/real-data/argentum-guild-search-probe-http403.json"),
    )
    parser.add_argument(
        "--search-probe-private",
        type=Path,
        default=Path("data/extracted/report-discovery/argentum-guild-search-probe.private.json"),
    )
    parser.add_argument(
        "--private-output",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/argentum-guild-search-access-diagnostic.private.json"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/argentum-guild-search-access-diagnostic.json"),
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
    parser.add_argument("--guild-label", default="Argentum")
    parser.add_argument("--curl-executable")
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--max-bytes", type=int, default=256 * 1024)
    args = parser.parse_args()

    registry = load_source_registry(args.registry)
    archive = RawArchive(
        args.raw_root,
        database_path=args.database,
        migrations_dir=args.migrations,
    )
    receipt = capture_guild_identity_search_access_diagnostic(
        registry,
        archive,
        public_search_probe_path=args.search_probe_receipt,
        private_search_probe_path=args.search_probe_private,
        private_output_path=args.private_output,
        receipt_output_path=args.output,
        expected_guild_label=args.guild_label,
        curl_executable=args.curl_executable,
        timeout_seconds=args.timeout_seconds,
        max_bytes=args.max_bytes,
    )

    summary = receipt["summary"]
    boundary = receipt["decision_boundary"]
    print(
        "guild search access diagnostic: "
        f"attempts={summary['attempt_count']} "
        f"selected_profile={summary['selected_access_profile']} "
        f"denial_categories={summary['denial_categories']}"
    )
    for attempt in receipt["attempts"]:
        print(
            "access attempt: "
            f"profile={attempt['profile']} "
            f"return_code={attempt['return_code']} "
            f"http_status={attempt['http_status']} "
            f"denial_category={attempt['denial_category']}"
        )
    print(f"private output: {args.private_output}")
    print(f"receipt output: {args.output}")
    print(
        "ready for profiled guild search probe: "
        f"{boundary['ready_for_profiled_guild_search_probe']}"
    )
    print("guild identity verified: false")
    print("ready for guild filtering: false")
    return 0 if boundary["ready_for_profiled_guild_search_probe"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
