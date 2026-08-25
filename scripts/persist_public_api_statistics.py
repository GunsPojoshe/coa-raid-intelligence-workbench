from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.analytics.public_api_population_priors import (
    population_prior_public_summary,
    read_public_api_population_priors,
)
from coa_workbench.collector.public_api_archive import load_latest_public_api_capture
from coa_workbench.collector.source_registry import load_source_registry
from coa_workbench.normalizer.canonical import stable_id
from coa_workbench.normalizer.public_api_statistics import (
    PUBLIC_API_STATISTICS_NORMALIZER_VERSION,
    parse_public_api_statistics,
)
from coa_workbench.storage.public_api_statistics import persist_public_api_statistics


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Normalize and persist the latest private official /statistics capture twice, proving "
            "deterministic DuckDB replay while emitting only scalar-safe counts and trust flags."
        )
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("config/coa_public_api_sources.yaml"),
    )
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("data/warehouse/coa.duckdb"),
    )
    parser.add_argument("--migrations", type=Path, default=Path("migrations"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/coa-public-api-statistics-persistence-review.json"),
    )
    args = parser.parse_args()

    registry = load_source_registry(args.registry)
    capture = load_latest_public_api_capture(
        args.raw_root,
        source_code=registry.source_code,
        endpoint_code="public_api_statistics",
    )
    try:
        batch = parse_public_api_statistics(
            capture.payload,
            query_keys=capture.query_keys,
            query_values=capture.query_value_mapping(),
        )
    except ValueError as exc:
        raise SystemExit(
            f"Cannot normalize the latest archived /statistics capture: {exc}"
        ) from exc

    first = persist_public_api_statistics(
        database_path=args.database,
        migrations_path=args.migrations,
        source_raw_id=capture.raw_id,
        source_code=registry.source_code,
        batch=batch,
    )
    second = persist_public_api_statistics(
        database_path=args.database,
        migrations_path=args.migrations,
        source_raw_id=capture.raw_id,
        source_code=registry.source_code,
        batch=batch,
    )

    batch_id = stable_id(
        "public_api_statistics_batch",
        capture.raw_id,
        PUBLIC_API_STATISTICS_NORMALIZER_VERSION,
    )
    snapshot = read_public_api_population_priors(args.database, batch_id=batch_id)
    read_summary = population_prior_public_summary(snapshot)
    replay_idempotent = (
        second["batch_matched"] is True
        and second["class_rows_inserted"] == 0
        and second["class_rows_matched"] == len(batch.class_summaries)
        and second["spec_rows_inserted"] == 0
        and second["spec_rows_matched"] == len(batch.records)
    )
    receipt = {
        "schema_version": 1,
        "review_kind": "official_public_api_statistics_persistence",
        "normalization": {
            "normalizer_version": second["normalizer_version"],
            "class_count": len(batch.class_summaries),
            "spec_record_count": len(batch.records),
            "percentile_value_count": batch.percentile_value_count,
            "request_context_complete": True,
        },
        "first_persistence": {
            "batch_inserted": first["batch_inserted"],
            "batch_matched": first["batch_matched"],
            "class_rows_inserted": first["class_rows_inserted"],
            "class_rows_matched": first["class_rows_matched"],
            "spec_rows_inserted": first["spec_rows_inserted"],
            "spec_rows_matched": first["spec_rows_matched"],
        },
        "replay": {
            "batch_matched": second["batch_matched"],
            "class_rows_inserted": second["class_rows_inserted"],
            "class_rows_matched": second["class_rows_matched"],
            "spec_rows_inserted": second["spec_rows_inserted"],
            "spec_rows_matched": second["spec_rows_matched"],
            "idempotent": replay_idempotent,
        },
        "read_model": read_summary,
        "verification": {
            "official_documented_api_source": True,
            "archived_capture_replayed": True,
            "documented_dimensions_persisted": True,
            "analysis_run_registered": second["analysis_run_registered"],
            "source_dependency_registered": second["source_dependency_registered"],
            "site_tier_list_algorithm_verified": False,
            "planner_scoring_allowed": False,
        },
        "privacy": {
            "query_values_included": False,
            "phase_values_included": False,
            "difficulty_values_included": False,
            "boss_ids_included": False,
            "class_names_included": False,
            "spec_names_included": False,
            "metric_scalar_values_included": False,
            "percentile_scalar_values_included": False,
            "raw_ids_included": False,
            "fingerprints_included": False,
            "raw_paths_included": False,
        },
        "public_release_safe": True,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if replay_idempotent else 5


if __name__ == "__main__":
    raise SystemExit(main())
