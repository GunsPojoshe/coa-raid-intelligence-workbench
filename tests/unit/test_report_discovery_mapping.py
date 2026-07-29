from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from coa_workbench.normalizer.report_discovery_mapping import (
    ReportDiscoveryMappingContract,
)
from coa_workbench.normalizer.schema_inspector import structure_fingerprint


def _payload() -> dict:
    reports = []
    for report_id in (101, 102):
        reports.append(
            {
                "created_at": "2026-07-29T10:00:00Z",
                "end_time": "2026-07-29T11:00:00Z",
                "guild_id": None,
                "guild_name": None,
                "highest_difficulty": {"trial_level": None},
                "id": report_id,
                "locations": ["private-location"],
                "start_time": "2026-07-29T10:00:00Z",
                "title": "Private title",
                "uploader_username": "Private uploader",
                "visibility": "public",
            }
        )
    return {
        "pagination": {"page": 1},
        "reports": reports,
        "success": True,
    }


def _hash(payload: dict) -> str:
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def _mapping(payload: dict) -> dict:
    return {
        "mapping_schema_version": 1,
        "mapping_id": "coa-public-report-discovery-v1",
        "source_code": "coa_ascension_logs",
        "mapping_version": "1",
        "status": "candidate",
        "route_template": "/api/reports/public",
        "schema_fingerprint": structure_fingerprint(payload),
        "reviewed_payload_hash": _hash(payload),
        "review_summary_schema_version": 1,
        "provenance_type": "upstream_derived",
        "required_top_level": ["pagination", "reports", "success"],
        "collection": {
            "path": "/reports/*",
            "observed_occurrences": 2,
            "required_keys": [
                "created_at",
                "end_time",
                "guild_id",
                "guild_name",
                "highest_difficulty",
                "id",
                "locations",
                "start_time",
                "title",
                "uploader_username",
                "visibility",
            ],
            "fields": {
                "source_report_id": {
                    "selector": "/id",
                    "review_path": "/reports/*/id",
                    "types": ["integer"],
                    "nullable": False,
                    "required": True,
                },
                "title": {
                    "selector": "/title",
                    "review_path": "/reports/*/title",
                    "types": ["string"],
                    "nullable": False,
                    "required": True,
                },
                "created_at": {
                    "selector": "/created_at",
                    "review_path": "/reports/*/created_at",
                    "types": ["string"],
                    "nullable": False,
                    "required": True,
                },
                "start_time": {
                    "selector": "/start_time",
                    "review_path": "/reports/*/start_time",
                    "types": ["string"],
                    "nullable": False,
                    "required": True,
                },
                "end_time": {
                    "selector": "/end_time",
                    "review_path": "/reports/*/end_time",
                    "types": ["string"],
                    "nullable": False,
                    "required": True,
                },
                "visibility": {
                    "selector": "/visibility",
                    "review_path": "/reports/*/visibility",
                    "types": ["string"],
                    "nullable": False,
                    "required": True,
                },
                "uploader_username": {
                    "selector": "/uploader_username",
                    "review_path": "/reports/*/uploader_username",
                    "types": ["string"],
                    "nullable": False,
                    "required": True,
                },
            },
        },
        "deferred_scopes": [
            "/pagination",
            "/reports/*/guild_id",
            "/reports/*/guild_name",
            "/reports/*/highest_difficulty",
            "/reports/*/locations",
        ],
        "review_notes": ["Synthetic candidate mapping."],
    }


def _summary(payload: dict) -> dict:
    mapping = _mapping(payload)
    required_keys = mapping["collection"]["required_keys"]
    fields = []
    for name, contract in mapping["collection"]["fields"].items():
        fields.append(
            {
                "name": name,
                "path": contract["review_path"],
                "occurrence_count": 2,
                "types": contract["types"],
                "nullable": contract["nullable"],
                "observed_on_all_items": True,
            }
        )
    return {
        "schema_version": 1,
        "summary_kind": "report_discovery_mapping_summary",
        "payload": {
            "payload_hash": mapping["reviewed_payload_hash"],
            "schema_fingerprint": mapping["schema_fingerprint"],
            "top_level_kind": "object",
            "top_level_keys": ["pagination", "reports", "success"],
            "review_status": "candidate",
        },
        "candidate_decision": {
            "unique_report_like_collection": True,
            "report_item_selector": "/reports/*",
            "can_promote": False,
        },
        "report_item_shape": {
            "path": "/reports/*",
            "occurrence_count": 2,
            "required_keys": required_keys,
            "fields": fields,
        },
        "summary": {
            "contains_source_scalar_values": False,
        },
    }


def test_candidate_mapping_validates_summary_and_exact_payload():
    payload = _payload()
    contract = ReportDiscoveryMappingContract.from_dict(_mapping(payload))

    review_result = contract.validate_against_summary(_summary(payload))
    archive_result = contract.validate_against_payload(
        payload,
        payload_hash=_hash(payload),
        schema_fingerprint=structure_fingerprint(payload),
        route="/api/reports/public",
    )

    assert review_result["field_count"] == 7
    assert review_result["production_ready"] is False
    assert archive_result["report_item_count"] == 2
    assert archive_result["extracted_value_count"] == 14
    assert archive_result["nullable_value_count"] == 0
    assert archive_result["raw_payload_validated"] is True


def test_candidate_mapping_is_blocked_from_production():
    contract = ReportDiscoveryMappingContract.from_dict(_mapping(_payload()))

    assert contract.production_ready is False
    with pytest.raises(ValueError, match="is not verified"):
        contract.require_verified()


def test_verified_mapping_requires_review_metadata():
    payload = _payload()
    mapping = _mapping(payload)
    mapping["status"] = "verified"

    with pytest.raises(ValueError, match="reviewed_by"):
        ReportDiscoveryMappingContract.from_dict(mapping)

    mapping["reviewed_by"] = "Operator"
    mapping["reviewed_at"] = "2026-07-29T16:41:00+03:00"
    contract = ReportDiscoveryMappingContract.from_dict(mapping)

    assert contract.production_ready is True
    contract.require_verified()


def test_checked_in_report_mapping_is_verified():
    repository_root = Path(__file__).resolve().parents[2]
    contract = ReportDiscoveryMappingContract.from_path(
        repository_root / "config" / "mappings" / "coa_public_report_discovery_v1.json"
    )

    assert contract.production_ready is True
    assert contract.reviewed_by == "GunsPojoshe (operator), OpenAI-assisted review"
    assert contract.reviewed_at == "2026-07-29T16:41:00+03:00"
    assert contract.deferred_scopes == (
        "/pagination",
        "/reports/*/guild_id",
        "/reports/*/guild_name",
        "/reports/*/highest_difficulty",
        "/reports/*/locations",
    )
    contract.require_verified()


def test_summary_type_mismatch_is_rejected():
    payload = _payload()
    contract = ReportDiscoveryMappingContract.from_dict(_mapping(payload))
    summary = _summary(payload)
    summary["report_item_shape"]["fields"][0]["types"] = ["string"]

    with pytest.raises(ValueError, match="type mismatch"):
        contract.validate_against_summary(summary)


def test_raw_hash_or_required_key_mismatch_is_rejected():
    payload = _payload()
    contract = ReportDiscoveryMappingContract.from_dict(_mapping(payload))

    with pytest.raises(ValueError, match="reviewed payload hash mismatch"):
        contract.validate_against_payload(
            payload,
            payload_hash="0" * 64,
            schema_fingerprint=structure_fingerprint(payload),
            route="/api/reports/public",
        )

    changed = deepcopy(payload)
    del changed["reports"][0]["title"]
    with pytest.raises(ValueError, match="missing required keys"):
        contract.validate_against_payload(
            changed,
            payload_hash=_hash(payload),
            schema_fingerprint=structure_fingerprint(payload),
            route="/api/reports/public",
        )
