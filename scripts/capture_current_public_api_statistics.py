from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.public_api_catalog import (
    load_latest_public_api_payload,
    parse_public_api_phases,
    select_current_phase_number,
)
from coa_workbench.collector.public_api_credentials import (
    DEFAULT_PUBLIC_API_KEY_ENV,
    DEFAULT_PUBLIC_API_KEY_FILE,
    load_public_api_key,
)
from coa_workbench.collector.public_api_stats_capture import (
    capture_public_api_stats,
    public_api_stats_capture_to_dict,
)
from coa_workbench.collector.raw_archive import RawArchive
from coa_workbench.collector.source_registry import load_source_registry


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Select the current content phase from the latest archived official /phases response "
            "and capture one bounded /statistics slice without printing the selected phase value."
        )
    )
    parser.add_argument(
        "--difficulty",
        choices=("normal", "heroic", "mythic", "ascended", "all"),
        default="all",
    )
    parser.add_argument(
        "--metric",
        choices=("avg_dps", "avg_hps", "avg_dtps"),
        default="avg_dps",
    )
    parser.add_argument("--bracket", default="all")
    parser.add_argument(
        "--damage-mode",
        choices=("standard", "boss-only", "trash"),
        default="standard",
    )
    parser.add_argument(
        "--role",
        choices=("tank", "dps", "tanks-and-dps", "support"),
        default="dps",
    )
    parser.add_argument("--realm")
    parser.add_argument(
        "--api-key-file",
        type=Path,
        default=DEFAULT_PUBLIC_API_KEY_FILE,
    )
    parser.add_argument("--api-key-env", default=DEFAULT_PUBLIC_API_KEY_ENV)
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
        default=Path("data/exchange/out/coa-public-api-current-statistics.json"),
    )
    parser.add_argument("--timeout-seconds", type=float, default=20.0)
    parser.add_argument("--retry-count", type=int, choices=(0, 1), default=0)
    args = parser.parse_args()

    registry = load_source_registry(args.registry)
    phases_payload = load_latest_public_api_payload(
        args.raw_root,
        source_code=registry.source_code,
        endpoint_code="public_api_phases",
    )
    phase_number = select_current_phase_number(parse_public_api_phases(phases_payload))
    try:
        api_key = load_public_api_key(key_file=args.api_key_file, env_name=args.api_key_env)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    query: dict[str, object] = {
        "phase": phase_number,
        "difficulty": args.difficulty,
        "metric": args.metric,
        "bracket": args.bracket,
        "damageMode": args.damage_mode,
    }
    if args.metric != "avg_hps":
        query["role"] = args.role
    if args.realm is not None:
        query["realm"] = args.realm

    archive = RawArchive(
        args.raw_root,
        database_path=args.database,
        migrations_dir=args.migrations,
    )
    result = capture_public_api_stats(
        registry,
        archive,
        endpoint_code="public_api_statistics",
        api_key=api_key,
        query=query,
        timeout_seconds=args.timeout_seconds,
        retry_count=args.retry_count,
    )
    rendered = public_api_stats_capture_to_dict(result)
    rendered["selection"] = {
        "phase_source_endpoint": "public_api_phases",
        "phase_selector": "unique_is_active_true_and_end_date_null",
        "phase_value_included": False,
        "query_values_included": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(rendered, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result.complete else 4


if __name__ == "__main__":
    raise SystemExit(main())
