from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

from coa_workbench.analytics.public_api_encounter_context import parse_encounter_reference_url
from coa_workbench.analytics.report_encounter_source_correlation import (
    correlate_report_encounter_payload,
)
from coa_workbench.collector import RawArchive, load_source_registry
from coa_workbench.collector.http_profile import SameOriginHttpSession
from coa_workbench.collector.http_read import read_response_resilient
from coa_workbench.collector.raw_archive import request_key_from_url

_ENDPOINT_CODE = "report_encounter_detail_source_correlation"
_ROUTE_TEMPLATE = "/api/reports/{reportId}/encounters/{encounterId}"
_MAX_JSON_BYTES = 32 * 1024 * 1024


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch exactly one already-reviewed first-party encounter-detail record and correlate "
            "its verified parser fields to the operator-selected report encounter. The emitted "
            "review is scalar-safe; the source payload remains private in RawArchive."
        )
    )
    parser.add_argument("--reference-url", required=True)
    parser.add_argument("--boss-name", required=True)
    parser.add_argument("--difficulty", required=True)
    parser.add_argument(
        "--mapping",
        type=Path,
        default=Path("config/mappings/coa_encounter_detail_v1.json"),
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
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    parser.add_argument("--retry-count", type=int, choices=(0, 1), default=1)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/exchange/out/coa-report-encounter-source-correlation-review.json"),
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
    if args.timeout_seconds <= 0:
        raise SystemExit("--timeout-seconds must be greater than zero")

    reference = parse_encounter_reference_url(args.reference_url)
    mapping_payload = json.loads(args.mapping.read_text(encoding="utf-8"))
    registry = load_source_registry(args.registry)
    archive = RawArchive(
        args.raw_root,
        database_path=args.database,
        migrations_dir=args.migrations,
    )
    session = SameOriginHttpSession(registry.base_url)
    route = f"/api/reports/{reference.report_id}/encounters/{reference.encounter_id}"
    url = urljoin(f"{registry.base_url.rstrip('/')}/", route.lstrip("/"))
    request = session.build_request(url)
    status, content_type, body, transport_error = read_response_resilient(
        request,
        timeout_seconds=args.timeout_seconds,
        opener=session.open,
        max_bytes=_MAX_JSON_BYTES,
        retry_count=args.retry_count,
    )

    if body is None or transport_error is not None:
        raise SystemExit(f"encounter-detail request failed: {transport_error or 'response body unavailable'}")
    if status is None or not 200 <= status < 300:
        raise SystemExit(f"encounter-detail request returned HTTP status {status}")

    archive.capture_bytes(
        body,
        source_code=registry.source_code,
        endpoint_code=_ENDPOINT_CODE,
        request_key=request_key_from_url("GET", url),
        fetched_at=datetime.now(timezone.utc),
        http_status=status,
        content_type=content_type,
        request_url=url,
        metadata={
            "capture_mode": "report_encounter_source_correlation",
            "route_template": _ROUTE_TEMPLATE,
            **session.safe_request_metadata(request),
        },
    )

    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SystemExit("encounter-detail response was not valid JSON") from exc

    correlation = correlate_report_encounter_payload(
        payload,
        mapping_payload,
        reference=reference,
        expected_boss_name=args.boss_name,
        expected_difficulty=args.difficulty,
    )
    summary = correlation.public_summary()
    review = {
        "schema_version": 1,
        "review_kind": "report_encounter_source_correlation",
        "source": {
            "first_party_encounter_detail": True,
            "reviewed_mapping_required": True,
            "compatible_normalization_required": True,
            "network_request_count": 1,
            "raw_capture_persisted": True,
            "events_read_used": False,
            "browser_har_used": False,
        },
        "correlation": summary,
        "verification": {
            "exact_reference_identity_verified": summary["exact_reference_identity_verified"],
            "report_encounter_boss_source_correlated": summary[
                "report_encounter_boss_source_correlated"
            ],
            "report_encounter_difficulty_source_correlated": summary[
                "report_encounter_difficulty_source_correlated"
            ],
            "boss_encounter_flag_verified": summary["boss_encounter_flag_verified"],
            "no_historical_difficulty_heuristic_used": True,
            "planner_scoring_allowed": False,
        },
        "privacy": {
            "report_ids_included": False,
            "encounter_ids_included": False,
            "boss_names_included": False,
            "difficulty_values_included": False,
            "location_values_included": False,
            "boss_ids_included": False,
            "creature_ids_included": False,
            "source_scalar_values_included": False,
            "source_structure_fingerprints_included": False,
            "raw_ids_included": False,
            "raw_paths_included": False,
            "request_urls_included": False,
            "query_values_included": False,
        },
        "public_release_safe": True,
    }
    _write_json(args.output, review)
    print(json.dumps(review, indent=2, sort_keys=True))
    return 0 if correlation.complete else 4


if __name__ == "__main__":
    raise SystemExit(main())
