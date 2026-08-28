from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.analytics.public_api_encounter_context import parse_encounter_reference_url
from coa_workbench.collector.selected_report_api_acquisition import (
    acquire_selected_report_core_sources,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Acquire the selected report's core runtime sources via reviewed direct API GETs only. "
            "Sources already Source Observatory-ready are skipped. No HAR is used."
        )
    )
    parser.add_argument("--reference-url", required=True)
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
    parser.add_argument("--timeout-seconds", type=float, default=20.0)
    parser.add_argument("--max-bytes", type=int, default=32 * 1024 * 1024)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/coa-selected-report-api-acquisition-review.json"),
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
    reference = parse_encounter_reference_url(args.reference_url)
    review = acquire_selected_report_core_sources(
        database_path=args.database,
        migrations_path=args.migrations,
        raw_root=args.raw_root,
        registry_path=args.registry,
        reference=reference,
        timeout_seconds=args.timeout_seconds,
        max_bytes=args.max_bytes,
    )
    summary = {
        "schema_version": 1,
        "review_kind": "selected_report_api_acquisition",
        "review": review.public_summary(),
        "public_release_safe": True,
    }
    _write_json(args.output, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if review.complete else 4


if __name__ == "__main__":
    raise SystemExit(main())
