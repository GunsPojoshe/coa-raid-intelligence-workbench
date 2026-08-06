from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import pytest

from coa_workbench.collector import report_slice_normalization as normalization_module
from coa_workbench.collector.report_slice_normalization import (
    normalize_observed_report_slice_selected_parser_mappings,
)


def _write_json(path: Path, payload: object) -> bytes:
    body = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return body


def _contract_rows(count: int) -> list[dict[str, object]]:
    return [
        {
            "entity": "fixture",
            "canonical_field": f"field_{index}",
            "expression": "@item/id",
            "semantic_status": "verified_parser_field",
        }
        for index in range(count)
    ]


def _mapping(
    mapping_id: str,
    *,
    schema_fingerprint: str,
    payload_hash: str,
) -> dict[str, object]:
    if mapping_id == "coa-report-detail-v1":
        return {
            "mapping_id": mapping_id,
            "source_code": "coa_ascension_logs",
            "schema_fingerprint": schema_fingerprint,
            "mapping_version": "1",
            "status": "verified",
            "route_template": "/api/reports/{template}",
            "reviewed_payload_hash": payload_hash,
            "mechanic_semantics_verified": False,
            "verification_scope": (
                "parser_schema_raw_archive_dry_run_and_cross_payload_linkage_only"
            ),
            "event_type_map": {},
            "field_contracts": _contract_rows(19),
            "entities": {
                "reports": {
                    "collection": "/report",
                    "fields": {
                        "source_report_id": "@item/id",
                        "title": "@item/title",
                    },
                    "required": ["source_report_id", "title"],
                },
                "encounters": {
                    "collection": "/encounters/*",
                    "fields": {
                        "source_encounter_id": "@item/id",
                        "source_report_id": "@root/report/id",
                        "name": "@item/name",
                    },
                    "required": ["source_encounter_id", "source_report_id", "name"],
                },
            },
        }
    return {
        "mapping_id": mapping_id,
        "source_code": "coa_ascension_logs",
        "schema_fingerprint": schema_fingerprint,
        "mapping_version": "1",
        "status": "verified",
        "route_template": "/api/reports/{template}/encounters/{template}",
        "reviewed_payload_hash": payload_hash,
        "mechanic_semantics_verified": False,
        "verification_scope": "parser_schema_raw_archive_dry_run_and_cross_payload_linkage_only",
        "event_type_map": {},
        "field_contracts": _contract_rows(35),
        "entities": {
            "reports": {
                "collection": "/encounter",
                "fields": {"source_report_id": "@item/report_id"},
                "required": ["source_report_id"],
            },
            "encounters": {
                "collection": "/encounter",
                "fields": {
                    "source_encounter_id": "@item/id",
                    "source_report_id": "@item/report_id",
                    "name": "@item/name",
                },
                "required": ["source_encounter_id", "source_report_id", "name"],
            },
            "actors": {
                "collection": "/character_stats/*",
                "fields": {
                    "source_actor_id": "@item/character_id",
                    "name": "@item/name",
                },
                "required": ["source_actor_id", "name"],
            },
            "participants": {
                "collection": "/character_stats/*",
                "fields": {
                    "source_encounter_id": "@item/encounter_id",
                    "source_actor_id": "@item/character_id",
                },
                "required": ["source_encounter_id", "source_actor_id"],
            },
        },
    }


def _fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, duplicate_last: bool = False):
    raw_root = tmp_path / "raw"
    raw_root.mkdir()
    report_payload = {
        "report": {"id": 1, "title": "PRIVATE REPORT"},
        "encounters": [
            {"id": index, "name": f"PRIVATE ENCOUNTER {index}"}
            for index in range(1, 15)
        ],
    }
    character_stats = [
        {
            "character_id": index,
            "encounter_id": 5,
            "name": f"PRIVATE ACTOR {index}",
        }
        for index in range(1, 32)
    ]
    if duplicate_last:
        character_stats[-1]["character_id"] = character_stats[-2]["character_id"]
    encounter_payload = {
        "encounter": {"id": 5, "report_id": 1, "name": "PRIVATE ENCOUNTER 5"},
        "character_stats": character_stats,
    }

    payloads = {
        "report_detail": (report_payload, "a" * 64, "/api/reports/{template}"),
        "encounter_detail": (
            encounter_payload,
            "b" * 64,
            "/api/reports/{template}/encounters/{template}",
        ),
    }
    endpoints = []
    mapping_dir = tmp_path / "mappings"
    mapping_dir.mkdir()
    publication_rows = []
    mapping_meta = {
        "report_detail": ("coa-report-detail-v1", "coa_report_detail_v1.json", 19),
        "encounter_detail": (
            "coa-encounter-detail-v1",
            "coa_encounter_detail_v1.json",
            35,
        ),
    }
    for endpoint_kind, (payload, fingerprint, route) in payloads.items():
        body = json.dumps(payload, sort_keys=True).encode()
        payload_hash = hashlib.sha256(body).hexdigest()
        relative_path = f"{endpoint_kind}.json.gz"
        (raw_root / relative_path).write_bytes(gzip.compress(body))
        endpoints.append(
            {
                "endpoint_kind": endpoint_kind,
                "route_template": route,
                "payload_hash": payload_hash,
                "schema_fingerprint": fingerprint,
                "payload_path": relative_path,
            }
        )
        mapping_id, mapping_file, field_count = mapping_meta[endpoint_kind]
        mapping = _mapping(
            mapping_id,
            schema_fingerprint=fingerprint,
            payload_hash=payload_hash,
        )
        mapping_body = _write_json(mapping_dir / mapping_file, mapping)
        publication_rows.append(
            {
                "mapping_id": mapping_id,
                "mapping_file": mapping_file,
                "status": "verified",
                "field_contract_count": field_count,
                "content_sha256": hashlib.sha256(mapping_body).hexdigest(),
                "target_path": f"config/mappings/{mapping_file}",
                "already_current": False,
            }
        )

    publication_path = tmp_path / "publication.json"
    _write_json(
        publication_path,
        {
            "schema_version": 1,
            "publication_kind": "observed_report_slice_verified_mapping_publication",
            "published_mappings": publication_rows,
            "decision_boundary": {
                "status": "published",
                "automatic_publication": False,
                "manual_publication_completed": True,
                "selected_parser_normalization_allowed": True,
                "mechanic_semantics_verified": False,
                "combatants_info_enrichment_available": False,
                "aura_normalization_available": False,
                "full_report_slice_complete": False,
            },
            "summary": {
                "mapping_count": 2,
                "field_contract_count": 54,
                "all_staged_files_match_promotion": True,
                "all_targets_published": True,
                "contains_source_scalar_values": False,
                "selected_parser_normalization_allowed": True,
                "mechanic_semantics_verified": False,
                "full_report_slice_complete": False,
            },
        },
    )
    monkeypatch.setattr(
        normalization_module,
        "review_observed_report_slice_capture",
        lambda *args, **kwargs: {"endpoints": endpoints},
    )
    return publication_path, mapping_dir, raw_root


def test_selected_parser_normalization_writes_private_batches_and_safe_receipt(
    tmp_path, monkeypatch
):
    publication_path, mapping_dir, raw_root = _fixture(tmp_path, monkeypatch)
    output_dir = tmp_path / "normalized"

    receipt = normalize_observed_report_slice_selected_parser_mappings(
        publication_path,
        mapping_dir=mapping_dir,
        capture_path=tmp_path / "capture.json",
        route_inventory_path=tmp_path / "inventory.json",
        raw_root=raw_root,
        normalized_output_dir=output_dir,
    )

    assert receipt["summary"]["aggregate_counts"] == {
        "reports": 2,
        "encounters": 15,
        "actors": 31,
        "participants": 31,
        "aura_events": 0,
        "rejects": 0,
    }
    assert all(receipt["cross_payload_checks"].values())
    assert receipt["summary"]["ready_for_deterministic_reconstruction"] is True
    serialized_receipt = json.dumps(receipt)
    assert "PRIVATE REPORT" not in serialized_receipt
    assert "PRIVATE ACTOR" not in serialized_receipt
    batch_text = "\n".join(path.read_text() for path in output_dir.glob("*.json"))
    assert "PRIVATE REPORT" in batch_text
    assert "PRIVATE ACTOR" in batch_text


def test_selected_parser_normalization_rejects_changed_published_mapping(tmp_path, monkeypatch):
    publication_path, mapping_dir, raw_root = _fixture(tmp_path, monkeypatch)
    path = mapping_dir / "coa_report_detail_v1.json"
    path.write_text(path.read_text() + " ", encoding="utf-8")

    with pytest.raises(ValueError, match="content hash mismatch"):
        normalize_observed_report_slice_selected_parser_mappings(
            publication_path,
            mapping_dir=mapping_dir,
            capture_path=tmp_path / "capture.json",
            route_inventory_path=tmp_path / "inventory.json",
            raw_root=raw_root,
            normalized_output_dir=tmp_path / "normalized",
        )


def test_selected_parser_normalization_rejects_full_slice_claim(tmp_path, monkeypatch):
    publication_path, mapping_dir, raw_root = _fixture(tmp_path, monkeypatch)
    publication = json.loads(publication_path.read_text())
    publication["decision_boundary"]["full_report_slice_complete"] = True
    _write_json(publication_path, publication)

    with pytest.raises(ValueError, match="boundary mismatch"):
        normalize_observed_report_slice_selected_parser_mappings(
            publication_path,
            mapping_dir=mapping_dir,
            capture_path=tmp_path / "capture.json",
            route_inventory_path=tmp_path / "inventory.json",
            raw_root=raw_root,
            normalized_output_dir=tmp_path / "normalized",
        )


def test_selected_parser_normalization_rejects_duplicate_participant_pair(tmp_path, monkeypatch):
    publication_path, mapping_dir, raw_root = _fixture(
        tmp_path,
        monkeypatch,
        duplicate_last=True,
    )

    with pytest.raises(ValueError, match="participant_pairs_unique"):
        normalize_observed_report_slice_selected_parser_mappings(
            publication_path,
            mapping_dir=mapping_dir,
            capture_path=tmp_path / "capture.json",
            route_inventory_path=tmp_path / "inventory.json",
            raw_root=raw_root,
            normalized_output_dir=tmp_path / "normalized",
        )
