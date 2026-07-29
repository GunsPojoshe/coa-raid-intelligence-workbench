from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.storage.combatants_observations import (
    persist_observed_combatants_info_observations,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Persist the exact manually promoted combatants-info observation batch atomically into "
            "DuckDB. Core report, encounter, actor and participant rows are validated but never "
            "mutated. The output receipt is scalar-free; the database remains private."
        )
    )
    parser.add_argument(
        "--promotion",
        type=Path,
        default=Path("data/exchange/out/observed-combatants-info-candidate-promotion.json"),
    )
    parser.add_argument(
        "--extraction-receipt",
        type=Path,
        default=Path("data/exchange/out/observed-combatants-info-candidate-extraction.json"),
    )
    parser.add_argument(
        "--private-extraction",
        type=Path,
        default=Path(
            "data/extracted/combatants-info/observed-combatants-info.candidate-extraction.json"
        ),
    )
    parser.add_argument("--database", type=Path, default=Path("data/warehouse/coa.duckdb"))
    parser.add_argument("--migrations", type=Path, default=Path("migrations"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/observed-combatants-info-persistence.json"),
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
    receipt = persist_observed_combatants_info_observations(
        args.promotion,
        extraction_receipt_path=args.extraction_receipt,
        private_extraction_path=args.private_extraction,
        database_path=args.database,
        migrations_path=args.migrations,
    )
    _write_json(args.output, receipt)

    summary = receipt["summary"]
    boundary = receipt["decision_boundary"]
    read_models = receipt["read_model_counts"]
    print("OBSERVED_COMBATANTS_INFO_PERSISTENCE")
    print(f"schema_version={receipt['schema_version']}")
    print(f"persistence_kind={receipt['persistence_kind']}")
    print(f"persistence_version={receipt['persistence_version']}")
    print(f"persisted_observation_count={summary['persisted_observation_count']}")
    print(f"actor_build_observation_count={summary['actor_build_observation_count']}")
    print(f"linked_actor_count={summary['linked_actor_count']}")
    print(f"parser_read_model_count={read_models['parser_observations']}")
    print(f"transaction_committed={str(summary['transaction_committed']).lower()}")
    print(
        "ready_for_actor_build_observation_queries="
        f"{str(summary['ready_for_actor_build_observation_queries']).lower()}"
    )
    print(
        "core_entity_mutation_performed="
        f"{str(summary['core_entity_mutation_performed']).lower()}"
    )
    print(
        "combatants_info_enrichment_available="
        f"{str(boundary['combatants_info_enrichment_available']).lower()}"
    )
    print(f"planner_scoring_allowed={str(boundary['planner_scoring_allowed']).lower()}")
    print(f"database_contains_source_scalar_values={str(summary['database_contains_source_scalar_values']).lower()}")
    print(f"output={args.output.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
