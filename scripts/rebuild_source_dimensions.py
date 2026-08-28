from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.source_dimension_index import rebuild_source_dimension_index
from coa_workbench.collector.source_registry import load_source_registry


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rebuild the approved local Source Observatory dimension index."
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("config/ascension_logs_sources.yaml"),
    )
    parser.add_argument("--database", type=Path, default=Path("data/warehouse/coa.duckdb"))
    parser.add_argument("--migrations", type=Path, default=Path("migrations"))
    args = parser.parse_args()

    registry = load_source_registry(args.registry)
    endpoint_codes = [
        route.endpoint_code
        for route in registry.routes
        if route.observatory_ready and route.dimension_keys
    ]
    result = rebuild_source_dimension_index(
        args.database,
        args.migrations,
        source_code=registry.source_code,
        endpoint_codes=endpoint_codes,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
