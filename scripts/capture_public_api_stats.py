from __future__ import annotations

import argparse
import json
from pathlib import Path

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

_ENDPOINT_CODES = {
    "phases": "public_api_phases",
    "bosses": "public_api_bosses",
    "statistics": "public_api_statistics",
}


def _query(args: argparse.Namespace) -> dict[str, object]:
    if args.endpoint == "bosses":
        return {}
    if args.endpoint == "phases":
        return {"realm": args.realm} if args.realm is not None else {}
    return {
        key: value
        for key, value in {
            "phase": args.phase,
            "difficulty": args.difficulty,
            "metric": args.metric,
            "bracket": args.bracket,
            "location": args.location,
            "bossId": args.boss_id,
            "damageMode": args.damage_mode,
            "role": args.role,
            "class": args.class_name,
            "spec": args.spec,
            "weekNumber": args.week_number,
            "realm": args.realm,
        }.items()
        if value is not None
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Capture one official self-serve stats:read API endpoint into RawArchive. "
            "The API key is loaded from an ignored local file or environment variable and is "
            "never accepted as a command-line value or query parameter."
        )
    )
    parser.add_argument("--endpoint", choices=tuple(_ENDPOINT_CODES), required=True)
    parser.add_argument("--phase", type=int)
    parser.add_argument("--difficulty")
    parser.add_argument("--metric")
    parser.add_argument("--bracket")
    parser.add_argument("--location")
    parser.add_argument("--boss-id", type=int)
    parser.add_argument("--damage-mode")
    parser.add_argument("--role")
    parser.add_argument("--class", dest="class_name")
    parser.add_argument("--spec")
    parser.add_argument("--week-number", type=int)
    parser.add_argument("--realm")
    parser.add_argument(
        "--api-key-file",
        type=Path,
        default=DEFAULT_PUBLIC_API_KEY_FILE,
        help=(
            "Ignored local file containing the API key. The file value is preferred over the "
            "environment fallback."
        ),
    )
    parser.add_argument(
        "--api-key-env",
        default=DEFAULT_PUBLIC_API_KEY_ENV,
        help="Fallback environment variable containing the API key. The value is never printed.",
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
        default=Path("data/exchange/out/coa-public-api-stats-capture.json"),
    )
    parser.add_argument("--timeout-seconds", type=float, default=20.0)
    parser.add_argument("--retry-count", type=int, choices=(0, 1), default=0)
    args = parser.parse_args()

    try:
        api_key = load_public_api_key(key_file=args.api_key_file, env_name=args.api_key_env)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    registry = load_source_registry(args.registry)
    archive = RawArchive(
        args.raw_root,
        database_path=args.database,
        migrations_dir=args.migrations,
    )
    result = capture_public_api_stats(
        registry,
        archive,
        endpoint_code=_ENDPOINT_CODES[args.endpoint],
        api_key=api_key,
        query=_query(args),
        timeout_seconds=args.timeout_seconds,
        retry_count=args.retry_count,
    )
    rendered = public_api_stats_capture_to_dict(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(rendered, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(rendered, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.complete else 4


if __name__ == "__main__":
    raise SystemExit(main())
