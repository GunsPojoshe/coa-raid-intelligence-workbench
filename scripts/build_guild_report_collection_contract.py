from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.guild_report_collection_contract import (
    build_guild_report_collection_contract,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a scalar-free guild-wide report collection contract from the verified public "
            "report discovery mapping and combatants persistence receipt. The contract opens only "
            "bounded pagination evidence capture; it does not crawl reports or score players."
        )
    )
    parser.add_argument(
        "--mapping",
        type=Path,
        default=Path("config/mappings/coa_public_report_discovery_v1.json"),
    )
    parser.add_argument(
        "--persistence",
        type=Path,
        default=Path("evidence/real-data/observed-combatants-info-persistence.json"),
    )
    parser.add_argument("--guild-label", default="Argentum")
    parser.add_argument("--minimum-candidates", type=int, default=30)
    parser.add_argument("--preferred-candidates", type=int, default=40)
    parser.add_argument("--final-roster-size", type=int, default=25)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/argentum-guild-report-collection-contract.json"),
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
    contract = build_guild_report_collection_contract(
        args.mapping,
        args.persistence,
        guild_label=args.guild_label,
        minimum_candidate_characters=args.minimum_candidates,
        preferred_candidate_characters=args.preferred_candidates,
        final_roster_size=args.final_roster_size,
    )
    _write_json(args.output, contract)

    summary = contract["summary"]
    boundary = contract["decision_boundary"]
    print("GUILD_REPORT_COLLECTION_CONTRACT")
    print(f"contract_version={contract['contract_version']}")
    print(f"collection_phases={summary['collection_phase_count']}")
    print(f"open_phases={summary['open_phase_count']}")
    print(f"blocked_phases={summary['blocked_phase_count']}")
    print(f"current_exact_payload_actors={summary['current_exact_payload_actor_count']}")
    print(f"minimum_candidates={summary['minimum_candidate_character_count']}")
    print(f"preferred_candidates={summary['preferred_candidate_character_count']}")
    print(f"final_roster_size={summary['final_roster_size']}")
    print(
        "ready_for_bounded_pagination_capture="
        f"{str(boundary['ready_for_bounded_pagination_capture']).lower()}"
    )
    print(f"ready_for_full_guild_crawl={str(boundary['ready_for_full_guild_crawl']).lower()}")
    print(f"ready_for_bis25_scoring={str(boundary['ready_for_bis25_scoring']).lower()}")
    print(f"output={args.output.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
