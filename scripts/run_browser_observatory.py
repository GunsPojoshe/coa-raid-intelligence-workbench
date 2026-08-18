from __future__ import annotations

import argparse
import json
from pathlib import Path

from coa_workbench.collector.browser_observatory import (
    BrowserObservatoryConfig,
    PlaywrightUnavailableError,
    run_browser_observatory,
    run_browser_profile_bootstrap,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run a headed private Browser Observatory session. The browser uses a dedicated ignored "
            "profile; HAR, trace and private action descriptors remain below data/private."
        )
    )
    parser.add_argument("--start-url", required=True)
    parser.add_argument("--allowed-host", default="coa.ascensionlogs.gg")
    parser.add_argument("--api-prefix", default="/api/")
    parser.add_argument("--source-code", default="coa_ascension_logs")
    parser.add_argument("--scenario-code", default="unassigned")
    parser.add_argument(
        "--private-root",
        type=Path,
        default=Path("data/private/browser-observatory"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/exchange/out"),
    )
    parser.add_argument("--no-trace", action="store_true")
    parser.add_argument("--bootstrap-profile", action="store_true")
    args = parser.parse_args()

    config = BrowserObservatoryConfig(
        start_url=args.start_url,
        allowed_host=args.allowed_host,
        api_prefix=args.api_prefix,
        source_code=args.source_code,
        scenario_code=args.scenario_code,
        user_data_dir=args.private_root / "browser-profile",
        private_session_root=args.private_root / "sessions",
        public_output_dir=args.output_dir,
        trace_enabled=not args.no_trace,
    )
    try:
        result = (
            run_browser_profile_bootstrap(config)
            if args.bootstrap_profile
            else run_browser_observatory(config)
        )
    except PlaywrightUnavailableError as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
