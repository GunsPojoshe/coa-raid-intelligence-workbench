from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.storage import persist_observed_report_slice


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Persist the private reconstructed report-slice parser records into local DuckDB and "
            "emit a scalar-free receipt. No network requests are performed."
        )
    )
    parser.add_argument(
        "--reconstruction",
        type=Path,
        default=Path("data/exchange/out/observed-report-slice-reconstruction.json"),
    )
    parser.add_argument(
        "--reconstructed-output",
        type=Path,
        default=Path("data/reconstructed/report-slice/observed-report-slice.reconstructed.json"),
    )
    parser.add_argument(
        "--normalization",
        type=Path,
        default=Path("data/exchange/out/observed-report-slice-normalization.json"),
    )
    parser.add_argument(
        "--mapping-dir",
        type=Path,
        default=Path("config/mappings"),
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("data/warehouse/coa.duckdb"),
    )
    parser.add_argument(
        "--migrations",
        type=Path,
        default=Path("migrations"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/observed-report-slice-persistence.json"),
    )
    return parser.parse_args()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def main() -> int:
    args = _arguments()
    receipt = persist_observed_report_slice(
        args.reconstruction,
        args.reconstructed_output,
        args.normalization,
        mapping_dir=args.mapping_dir,
        database_path=args.database,
        migrations_dir=args.migrations,
    )
    _write_json(args.output, receipt)

    summary = receipt["summary"]
    counts = summary["persisted_counts"]
    boundary = receipt["decision_boundary"]
    print("OBSERVED_REPORT_SLICE_SELECTED_PARSER_PERSISTENCE")
    print(f"schema_version={receipt['schema_version']}")
    print(f"persistence_kind={receipt['persistence_kind']}")
    print(f"persistence_version={receipt['persistence_version']}")
    print(f"source_batch_count={summary['source_batch_count']}")
    print(f"mapping_count={summary['mapping_count']}")
    print(f"reports={counts['reports']}")
    print(f"encounters={counts['encounters']}")
    print(f"actors={counts['actors']}")
    print(f"participants={counts['participants']}")
    print(f"aura_events={counts['aura_events']}")
    print(f"rejects={counts['rejects']}")
    print(
        "canonical_entity_observation_count="
        f"{summary['canonical_entity_observation_count']}"
    )
    print(
        "all_integrity_checks_passed="
        f"{str(summary['all_integrity_checks_passed']).lower()}"
    )
    print(f"transaction_committed={str(summary['transaction_committed']).lower()}")
    print(
        "ready_for_parser_observation_queries="
        f"{str(summary['ready_for_parser_observation_queries']).lower()}"
    )
    print(
        "ready_for_combatants_info_mapping_review="
        f"{str(summary['ready_for_combatants_info_mapping_review']).lower()}"
    )
    print(f"mechanic_semantics_verified={str(summary['mechanic_semantics_verified']).lower()}")
    print(f"full_report_slice_complete={str(summary['full_report_slice_complete']).lower()}")
    print(f"planner_scoring_allowed={str(summary['planner_scoring_allowed']).lower()}")
    print(
        "database_contains_source_scalar_values="
        f"{str(boundary['database_contains_source_scalar_values']).lower()}"
    )
    print()
    print("INTEGRITY_CHECKS")
    for name, passed in sorted(receipt["integrity_checks"].items()):
        print(f"{name}={str(passed).lower()}")
    print()
    print(f"database={args.database.as_posix()}")
    print(f"receipt={args.output.as_posix()}")
    print("Do not share or commit the local DuckDB database or reconstructed canonical slice.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
