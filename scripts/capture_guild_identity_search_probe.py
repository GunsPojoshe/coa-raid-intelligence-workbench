from __future__ import annotations

import argparse
from pathlib import Path

from coa_workbench.collector import RawArchive, load_source_registry
from coa_workbench.collector.guild_identity_search_probe import (
    capture_guild_identity_search_probe,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Capture one bounded /api/guilds/search response for scalar-free route and "
            "identity mapping review. This does not verify guild identity or enable filtering."
        )
    )
    parser.add_argument(
        "--profiled-recovery-receipt",
        type=Path,
        default=Path("evidence/real-data/argentum-guild-asset-profiled-recovery.json"),
    )
    parser.add_argument(
        "--profiled-recovery-private",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/argentum-guild-asset-profiled-recovery.private.json"
        ),
    )
    parser.add_argument(
        "--private-output",
        type=Path,
        default=Path("data/extracted/report-discovery/argentum-guild-search-probe.private.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/argentum-guild-search-probe.json"),
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
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--curl-executable")
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--max-bytes", type=int, default=2 * 1024 * 1024)
    args = parser.parse_args()

    registry = load_source_registry(args.registry)
    archive = RawArchive(
        args.raw_root,
        database_path=args.database,
        migrations_dir=args.migrations,
    )
    receipt = capture_guild_identity_search_probe(
        registry,
        archive,
        public_profiled_recovery_path=args.profiled_recovery_receipt,
        private_profiled_recovery_path=args.profiled_recovery_private,
        private_output_path=args.private_output,
        receipt_output_path=args.output,
        expected_guild_label=args.guild_label,
        limit=args.limit,
        curl_executable=args.curl_executable,
        timeout_seconds=args.timeout_seconds,
        max_bytes=args.max_bytes,
    )

    response = receipt["response"]
    matches = receipt["match_review"]
    boundary = receipt["decision_boundary"]
    print(
        "guild identity search probe: "
        f"completed={response['completed']} "
        f"http_status={response['http_status']} "
        f"exact_label_objects={matches['exact_label_object_count']} "
        f"source_id_matches={matches['source_id_match_object_count']} "
        f"one_to_one_candidate={matches['one_to_one_identity_candidate']}"
    )
    print(f"private output: {args.private_output}")
    print(f"receipt output: {args.output}")
    print(
        "ready for guild search mapping review: "
        f"{boundary['ready_for_guild_search_mapping_review']}"
    )
    print("guild identity verified: false")
    print("ready for guild filtering: false")
    return 0 if boundary["ready_for_guild_search_mapping_review"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
