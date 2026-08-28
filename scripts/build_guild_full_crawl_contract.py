from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.guild_full_crawl_contract import (
    build_guild_full_crawl_contract,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a scalar-free full-crawl collection contract from the verified public "
            "manifest, identity decision and filtered guild manifest. The contract opens "
            "only bounded route-semantics capture and keeps full crawl and scoring disabled."
        )
    )
    parser.add_argument(
        "--public-manifest",
        type=Path,
        default=Path("evidence/real-data/argentum-public-report-manifest.json"),
    )
    parser.add_argument(
        "--identity-decision",
        type=Path,
        default=Path("evidence/real-data/argentum-guild-identity-decision.json"),
    )
    parser.add_argument(
        "--guild-manifest",
        type=Path,
        default=Path("evidence/real-data/argentum-guild-report-manifest.json"),
    )
    parser.add_argument("--guild-label", default="Argentum")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/argentum-guild-full-crawl-contract.json"),
    )
    return parser.parse_args()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def main() -> int:
    args = _arguments()
    contract = build_guild_full_crawl_contract(
        args.public_manifest,
        args.identity_decision,
        args.guild_manifest,
        expected_guild_label=args.guild_label,
    )
    _write_json(args.output, contract)

    summary = contract["summary"]
    boundary = contract["decision_boundary"]
    print("GUILD_FULL_CRAWL_COLLECTION_CONTRACT")
    print(f"contract_version={contract['contract_version']}")
    print(f"source_reports={summary['source_public_report_count']}")
    print(f"selected_reports={summary['selected_guild_report_count']}")
    print(
        "full_crawl_collection_contract_reviewed="
        f"{str(boundary['full_crawl_collection_contract_reviewed']).lower()}"
    )
    print(
        "ready_for_bounded_route_semantics_capture="
        f"{str(boundary['ready_for_bounded_route_semantics_capture']).lower()}"
    )
    print(
        "guild_api_route_semantics_verified="
        f"{str(boundary['guild_api_route_semantics_verified']).lower()}"
    )
    print(f"ready_for_full_guild_crawl={str(boundary['ready_for_full_guild_crawl']).lower()}")
    print(f"planner_scoring_allowed={str(boundary['planner_scoring_allowed']).lower()}")
    print(f"output={args.output.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
