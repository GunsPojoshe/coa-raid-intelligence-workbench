from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

from coa_workbench.analytics.public_api_encounter_context import parse_encounter_reference_url
from coa_workbench.analytics.report_encounter_source_correlation import (
    correlate_report_encounter_catalog_payload,
    load_persisted_report_encounter_catalog,
)
from coa_workbench.collector import RawArchive, load_source_registry
from coa_workbench.collector.http_profile import SameOriginHttpSession
from coa_workbench.collector.http_read import read_response_resilient
from coa_workbench.collector.raw_archive import request_key_from_url

_ENDPOINT_CODE = "report_encounters_api"
_ROUTE_TEMPLATE = "/api/reports/{reportId}/encounters"
_MAX_JSON_BYTES = 8 * 1024 * 1024


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Correlate one operator-selected report encounter to first-party boss/difficulty "
            "evidence. Prefer already persisted current-report encounter-catalog evidence; "
            "otherwise fetch only the small reviewed encounter catalog."
        )
    )
    parser.add_argument("--reference-url", required=True)
    parser.add_argument("--boss-name", required=True)
    parser.add_argument("--difficulty", required=True)
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


def _privacy() -> dict[str, bool]:
    return {
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
    }


def _source_summary(
    *,
    source_kind: str,
    persisted_observation_count: int,
    network_request_count: int,
    raw_capture_written_this_run: bool,
) -> dict[str, object]:
    return {
        "source_kind": source_kind,
        "first_party_encounter_catalog": True,
        "reviewed_route_required": True,
        "persisted_observation_preferred": True,
        "persisted_observation_used": source_kind == "persisted_first_party_encounter_catalog",
        "persisted_observation_count": persisted_observation_count,
        "network_request_count": network_request_count,
        "raw_capture_written_this_run": raw_capture_written_this_run,
        "encounter_detail_used": False,
        "events_read_used": False,
        "browser_har_used": False,
    }


def _failure_review(
    *,
    failure_kind: str,
    source_kind: str,
    persisted_observation_count: int,
    network_request_count: int,
    raw_capture_written_this_run: bool,
    http_status: int | None = None,
) -> dict[str, object]:
    return {
        "schema_version": 2,
        "review_kind": "report_encounter_source_correlation",
        "source": _source_summary(
            source_kind=source_kind,
            persisted_observation_count=persisted_observation_count,
            network_request_count=network_request_count,
            raw_capture_written_this_run=raw_capture_written_this_run,
        ),
        "failure": {
            "kind": failure_kind,
            "http_status": http_status,
        },
        "verification": {
            "exact_reference_identity_verified": False,
            "report_encounter_boss_source_correlated": False,
            "report_encounter_difficulty_source_correlated": False,
            "boss_encounter_flag_verified": False,
            "no_historical_difficulty_heuristic_used": True,
            "planner_scoring_allowed": False,
        },
        "privacy": _privacy(),
        "public_release_safe": True,
    }


def _transport_failure_kind(error: str | None) -> str:
    prepared = (error or "").casefold()
    if "timeout" in prepared:
        return "transport_timeout"
    if "disconnect" in prepared:
        return "remote_disconnect"
    if "network" in prepared:
        return "network_error"
    return "response_unavailable"


def main() -> int:
    args = _arguments()
    if args.timeout_seconds <= 0:
        raise SystemExit("--timeout-seconds must be greater than zero")

    reference = parse_encounter_reference_url(args.reference_url)
    persisted_count = 0
    network_request_count = 0
    raw_capture_written = False

    try:
        persisted = load_persisted_report_encounter_catalog(
            args.database,
            reference=reference,
        )
    except (RuntimeError, ValueError) as exc:
        review = _failure_review(
            failure_kind="persisted_evidence_rejected",
            source_kind="persisted_first_party_encounter_catalog",
            persisted_observation_count=0,
            network_request_count=0,
            raw_capture_written_this_run=False,
        )
        _write_json(args.output, review)
        print(json.dumps(review, indent=2, sort_keys=True))
        raise SystemExit(f"persisted report evidence rejected: {exc}") from exc

    if persisted is not None:
        payload = persisted.payload
        persisted_count = persisted.matching_observation_count
        source_kind = "persisted_first_party_encounter_catalog"
    else:
        source_kind = "live_first_party_encounter_catalog"
        registry = load_source_registry(args.registry)
        session = SameOriginHttpSession(registry.base_url)
        route = f"/api/reports/{reference.report_id}/encounters?includeTrash=false"
        url = urljoin(f"{registry.base_url.rstrip('/')}/", route.lstrip("/"))
        request = session.build_request(url)
        network_request_count = 1
        status, content_type, body, transport_error = read_response_resilient(
            request,
            timeout_seconds=args.timeout_seconds,
            opener=session.open,
            max_bytes=_MAX_JSON_BYTES,
            retry_count=args.retry_count,
        )

        if status is not None and not 200 <= status < 300:
            review = _failure_review(
                failure_kind="http_error",
                source_kind=source_kind,
                persisted_observation_count=0,
                network_request_count=network_request_count,
                raw_capture_written_this_run=False,
                http_status=status,
            )
            _write_json(args.output, review)
            print(json.dumps(review, indent=2, sort_keys=True))
            return 5
        if body is None or transport_error is not None:
            review = _failure_review(
                failure_kind=_transport_failure_kind(transport_error),
                source_kind=source_kind,
                persisted_observation_count=0,
                network_request_count=network_request_count,
                raw_capture_written_this_run=False,
            )
            _write_json(args.output, review)
            print(json.dumps(review, indent=2, sort_keys=True))
            return 5

        archive = RawArchive(
            args.raw_root,
            database_path=args.database,
            migrations_dir=args.migrations,
        )
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
        raw_capture_written = True

        try:
            payload = json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            review = _failure_review(
                failure_kind="invalid_json",
                source_kind=source_kind,
                persisted_observation_count=0,
                network_request_count=network_request_count,
                raw_capture_written_this_run=raw_capture_written,
            )
            _write_json(args.output, review)
            print(json.dumps(review, indent=2, sort_keys=True))
            return 5

    try:
        correlation = correlate_report_encounter_catalog_payload(
            payload,
            reference=reference,
            expected_boss_name=args.boss_name,
            expected_difficulty=args.difficulty,
            source_kind=source_kind,
        )
    except ValueError as exc:
        review = _failure_review(
            failure_kind="source_contract_rejected",
            source_kind=source_kind,
            persisted_observation_count=persisted_count,
            network_request_count=network_request_count,
            raw_capture_written_this_run=raw_capture_written,
        )
        _write_json(args.output, review)
        print(json.dumps(review, indent=2, sort_keys=True))
        raise SystemExit(f"encounter-catalog source correlation failed: {exc}") from exc

    summary = correlation.public_summary()
    review = {
        "schema_version": 2,
        "review_kind": "report_encounter_source_correlation",
        "source": _source_summary(
            source_kind=source_kind,
            persisted_observation_count=persisted_count,
            network_request_count=network_request_count,
            raw_capture_written_this_run=raw_capture_written,
        ),
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
        "privacy": _privacy(),
        "public_release_safe": True,
    }
    _write_json(args.output, review)
    print(json.dumps(review, indent=2, sort_keys=True))
    return 0 if correlation.complete else 4


if __name__ == "__main__":
    raise SystemExit(main())
