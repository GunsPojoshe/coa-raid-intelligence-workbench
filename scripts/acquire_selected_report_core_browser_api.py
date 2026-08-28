from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.analytics.public_api_encounter_context import parse_encounter_reference_url
from coa_workbench.analytics.selected_report_source_availability import (
    review_selected_report_source_availability,
)
from coa_workbench.collector.browser_context_api import (
    BrowserContextApiConfig,
    browser_context_url_opener,
)
from coa_workbench.collector.browser_observatory import PlaywrightUnavailableError
from coa_workbench.collector.selected_report_browser_api_acquisition import (
    acquire_selected_report_core_sources_in_browser_context,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Acquire selected-report core sources through exact reviewed API GETs executed by "
            "same-origin browser fetch(). A persistent private browser profile may satisfy managed "
            "edge challenges. No HAR or trace is recorded."
        )
    )
    parser.add_argument("--reference-url", required=True)
    parser.add_argument(
        "--browser-start-url",
        default="https://coa.ascensionlogs.gg/",
    )
    parser.add_argument("--allowed-host", default="coa.ascensionlogs.gg")
    parser.add_argument(
        "--user-data-dir",
        type=Path,
        default=Path("data/private/browser-observatory/browser-profile"),
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
    parser.add_argument("--timeout-seconds", type=float, default=20.0)
    parser.add_argument("--navigation-timeout-seconds", type=float, default=45.0)
    parser.add_argument("--clearance-timeout-seconds", type=float, default=120.0)
    parser.add_argument("--max-bytes", type=int, default=32 * 1024 * 1024)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/coa-selected-report-browser-api-acquisition-review.json"),
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
    before = review_selected_report_source_availability(
        args.database,
        raw_root=args.raw_root,
        reference=reference,
    )

    if before.offline_source_observatory_reuse_ready:
        review = acquire_selected_report_core_sources_in_browser_context(
            database_path=args.database,
            migrations_path=args.migrations,
            raw_root=args.raw_root,
            registry_path=args.registry,
            reference=reference,
            opener=None,
            timeout_seconds=args.timeout_seconds,
            max_bytes=args.max_bytes,
            browser_navigation_performed=False,
        )
    else:
        config = BrowserContextApiConfig(
            start_url=args.browser_start_url,
            allowed_host=args.allowed_host,
            user_data_dir=args.user_data_dir,
            navigation_timeout_seconds=args.navigation_timeout_seconds,
            clearance_timeout_seconds=args.clearance_timeout_seconds,
        )
        try:
            with browser_context_url_opener(config) as opener:
                review = acquire_selected_report_core_sources_in_browser_context(
                    database_path=args.database,
                    migrations_path=args.migrations,
                    raw_root=args.raw_root,
                    registry_path=args.registry,
                    reference=reference,
                    opener=opener,
                    timeout_seconds=args.timeout_seconds,
                    max_bytes=args.max_bytes,
                    browser_navigation_performed=True,
                )
        except (PlaywrightUnavailableError, TimeoutError) as exc:
            print(str(exc))
            return 5

    summary = {
        "schema_version": 1,
        "review_kind": "selected_report_browser_context_api_acquisition",
        "review": review.public_summary(),
        "public_release_safe": True,
    }
    _write_json(args.output, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if review.complete else 4


if __name__ == "__main__":
    raise SystemExit(main())
