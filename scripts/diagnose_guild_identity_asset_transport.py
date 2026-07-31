from __future__ import annotations

import argparse
from pathlib import Path

from coa_workbench.collector import load_source_registry
from coa_workbench.collector.guild_identity_asset_transport_diagnostic import (
    diagnose_guild_identity_asset_transport,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Probe bounded curl transport profiles for one private guild SPA asset. "
            "This does not download the full asset or verify guild identity."
        )
    )
    parser.add_argument(
        "--recovery-receipt",
        type=Path,
        default=Path(
            "evidence/real-data/argentum-guild-asset-recovery-tls-failure.json"
        ),
    )
    parser.add_argument(
        "--recovery-private",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/argentum-guild-asset-recovery.private.json"
        ),
    )
    parser.add_argument(
        "--private-output",
        type=Path,
        default=Path(
            "data/extracted/report-discovery/"
            "argentum-guild-asset-transport-diagnostic.private.json"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "data/exchange/out/argentum-guild-asset-transport-diagnostic.json"
        ),
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("config/ascension_logs_sources.yaml"),
    )
    parser.add_argument("--guild-label", default="Argentum")
    parser.add_argument("--curl-executable")
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--max-probe-bytes", type=int, default=1024 * 1024)
    args = parser.parse_args()

    registry = load_source_registry(args.registry)
    receipt = diagnose_guild_identity_asset_transport(
        registry,
        public_recovery_path=args.recovery_receipt,
        private_recovery_path=args.recovery_private,
        private_output_path=args.private_output,
        receipt_output_path=args.output,
        expected_guild_label=args.guild_label,
        curl_executable=args.curl_executable,
        timeout_seconds=args.timeout_seconds,
        max_probe_bytes=args.max_probe_bytes,
    )

    summary = receipt["summary"]
    boundary = receipt["decision_boundary"]
    print(
        "guild asset transport diagnostic: "
        f"attempts={summary['attempt_count']} "
        f"selected_profile={summary['selected_profile']} "
        f"transport_candidate={summary['transport_profile_candidate_observed']}"
    )
    for attempt in receipt["attempts"]:
        print(
            "transport attempt: "
            f"profile={attempt['profile']} "
            f"return_code={attempt['return_code']} "
            f"http_status={attempt['http_status']} "
            f"failure_class={attempt['failure_class']}"
        )
    print(f"private output: {args.private_output}")
    print(f"receipt output: {args.output}")
    print(
        "ready for profiled asset recovery: "
        f"{boundary['ready_for_profiled_asset_recovery']}"
    )
    print("guild identity verified: false")
    print("ready for guild filtering: false")
    return 0 if boundary["ready_for_profiled_asset_recovery"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
