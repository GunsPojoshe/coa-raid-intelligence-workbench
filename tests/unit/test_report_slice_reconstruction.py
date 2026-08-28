from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from coa_workbench.collector.report_slice_reconstruction import (
    reconstruct_observed_report_slice,
)


def _write_json(path: Path, payload: object) -> bytes:
    body = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return body


def _batch_payload(
    mapping_id: str,
    *,
    batch: dict[str, object],
    source_payload_hash: str,
    schema_fingerprint: str,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "normalization_kind": "canonical_batch",
        "source_payload_hash": source_payload_hash,
        "schema_fingerprint": schema_fingerprint,
        "batch": {
            "source_code": "coa_ascension_logs",
            "mapping_id": mapping_id,
            "mapping_version": "1",
            "normalizer_version": "canonical-normalizer-v1",
            **batch,
        },
    }


def _fixture(
    tmp_path: Path,
    *,
    conflicting_encounter: bool = False,
    duplicate_participant: bool = False,
) -> tuple[Path, Path]:
    normalized_dir = tmp_path / "normalized"
    report_encounters = [
        {
            "encounter_id": f"encounter-{index}",
            "report_id": "report-1",
            "source_encounter_id": index,
            "source_report_id": 1,
            "name": f"PRIVATE ENCOUNTER {index}",
            "start_time": f"2026-01-01T00:{index:02d}:00Z",
        }
        for index in range(1, 15)
    ]
    report_batch = {
        "counts": {
            "reports": 1,
            "encounters": 14,
            "actors": 0,
            "participants": 0,
            "aura_events": 0,
            "rejects": 0,
        },
        "reports": [
            {
                "report_id": "report-1",
                "source_report_id": 1,
                "title": "PRIVATE REPORT",
                "realm": "PRIVATE REALM",
            }
        ],
        "encounters": report_encounters,
        "actors": [],
        "participants": [],
        "aura_events": [],
        "rejects": [],
    }

    actors = [
        {
            "actor_id": f"actor-{index}",
            "source_actor_id": index,
            "name": f"PRIVATE ACTOR {index}",
        }
        for index in range(1, 32)
    ]
    participants = [
        {
            "encounter_id": "encounter-5",
            "actor_id": f"actor-{index}",
            "source_encounter_id": 5,
            "source_actor_id": index,
            "avg_dps": float(index),
        }
        for index in range(1, 32)
    ]
    if duplicate_participant:
        participants[-1]["actor_id"] = participants[-2]["actor_id"]
        participants[-1]["source_actor_id"] = participants[-2]["source_actor_id"]

    encounter_batch = {
        "counts": {
            "reports": 1,
            "encounters": 1,
            "actors": 31,
            "participants": 31,
            "aura_events": 0,
            "rejects": 0,
        },
        "reports": [
            {
                "report_id": "report-1",
                "source_report_id": 1,
                "realm": "PRIVATE REALM",
            }
        ],
        "encounters": [
            {
                "encounter_id": "encounter-5",
                "report_id": "report-1",
                "source_encounter_id": 5,
                "source_report_id": 1,
                "name": (
                    "PRIVATE CONFLICTING ENCOUNTER"
                    if conflicting_encounter
                    else "PRIVATE ENCOUNTER 5"
                ),
                "start_time": "2026-01-01T00:05:00Z",
                "difficulty": "PRIVATE DIFFICULTY",
                "player_count": 31,
            }
        ],
        "actors": actors,
        "participants": participants,
        "aura_events": [],
        "rejects": [],
    }

    rows = []
    fixtures = [
        (
            "coa-encounter-detail-v1",
            "coa_encounter_detail_v1.normalized.json",
            encounter_batch,
            "a" * 64,
            "b" * 64,
            {
                "reports": 1,
                "encounters": 1,
                "actors": 31,
                "participants": 31,
                "aura_events": 0,
                "rejects": 0,
            },
        ),
        (
            "coa-report-detail-v1",
            "coa_report_detail_v1.normalized.json",
            report_batch,
            "c" * 64,
            "d" * 64,
            {
                "reports": 1,
                "encounters": 14,
                "actors": 0,
                "participants": 0,
                "aura_events": 0,
                "rejects": 0,
            },
        ),
    ]
    for mapping_id, filename, batch, source_hash, fingerprint, counts in fixtures:
        body = _write_json(
            normalized_dir / filename,
            _batch_payload(
                mapping_id,
                batch=batch,
                source_payload_hash=source_hash,
                schema_fingerprint=fingerprint,
            ),
        )
        rows.append(
            {
                "mapping_id": mapping_id,
                "mapping_file": filename.replace(".normalized.json", ".json"),
                "mapping_content_sha256": "e" * 64,
                "source_payload_hash": source_hash,
                "schema_fingerprint": fingerprint,
                "normalized_batch_file": filename,
                "normalized_batch_sha256": hashlib.sha256(body).hexdigest(),
                "counts": counts,
                "mapping_hash_verified": True,
                "raw_archive_verified": True,
            }
        )

    normalization_path = tmp_path / "normalization.json"
    _write_json(
        normalization_path,
        {
            "schema_version": 1,
            "normalization_kind": "observed_report_slice_selected_parser_normalization",
            "normalized_batches": rows,
            "cross_payload_checks": {
                "exact_encounter_present_in_report_batch": True,
                "participant_actor_references_resolved": True,
                "participant_encounter_references_resolved": True,
                "participant_pairs_unique": True,
                "report_id_consistent": True,
                "single_report_id_in_each_batch": True,
            },
            "decision_boundary": {
                "status": "normalized_parser_slice",
                "selected_parser_normalization_completed": True,
                "ready_for_deterministic_reconstruction": True,
                "automatic_commit": False,
                "mechanic_semantics_verified": False,
                "combatants_info_enrichment_available": False,
                "aura_normalization_available": False,
                "full_report_slice_complete": False,
                "normalized_batch_files_contain_source_scalar_values": True,
            },
            "summary": {
                "mapping_count": 2,
                "field_contract_count": 54,
                "exact_raw_archive_count": 2,
                "aggregate_counts": {
                    "reports": 2,
                    "encounters": 15,
                    "actors": 31,
                    "participants": 31,
                    "aura_events": 0,
                    "rejects": 0,
                },
                "all_mapping_hashes_verified": True,
                "all_raw_archives_verified": True,
                "all_normalization_counts_match": True,
                "cross_payload_consistent": True,
                "contains_source_scalar_values": False,
                "normalized_batch_files_contain_source_scalar_values": True,
                "ready_for_deterministic_reconstruction": True,
                "mechanic_semantics_verified": False,
                "full_report_slice_complete": False,
            },
        },
    )
    return normalization_path, normalized_dir


def test_reconstruction_merges_private_batches_and_emits_safe_receipt(tmp_path):
    normalization_path, normalized_dir = _fixture(tmp_path)
    reconstructed_path = tmp_path / "reconstructed.json"

    receipt = reconstruct_observed_report_slice(
        normalization_path,
        normalized_output_dir=normalized_dir,
        reconstructed_output_path=reconstructed_path,
    )

    assert receipt["summary"]["output_counts"] == {
        "reports": 1,
        "encounters": 14,
        "actors": 31,
        "participants": 31,
        "aura_events": 0,
        "rejects": 0,
    }
    assert receipt["summary"]["duplicate_report_count"] == 1
    assert receipt["summary"]["duplicate_encounter_count"] == 1
    assert receipt["summary"]["field_conflict_count"] == 0
    assert all(receipt["linkage_checks"].values())
    assert "PRIVATE" not in json.dumps(receipt)

    reconstructed = json.loads(reconstructed_path.read_text())
    assert "PRIVATE REPORT" in reconstructed_path.read_text()
    exact = next(
        row
        for row in reconstructed["canonical_slice"]["encounters"]
        if row["encounter_id"] == "encounter-5"
    )
    assert exact["difficulty"] == "PRIVATE DIFFICULTY"
    assert exact["name"] == "PRIVATE ENCOUNTER 5"


def test_reconstruction_rejects_changed_normalized_batch(tmp_path):
    normalization_path, normalized_dir = _fixture(tmp_path)
    path = normalized_dir / "coa_report_detail_v1.normalized.json"
    path.write_text(path.read_text() + " ", encoding="utf-8")

    with pytest.raises(ValueError, match="content hash mismatch"):
        reconstruct_observed_report_slice(
            normalization_path,
            normalized_output_dir=normalized_dir,
            reconstructed_output_path=tmp_path / "reconstructed.json",
        )


def test_reconstruction_rejects_conflicting_duplicate_field(tmp_path):
    normalization_path, normalized_dir = _fixture(tmp_path, conflicting_encounter=True)

    with pytest.raises(ValueError, match="field conflict for encounters.name"):
        reconstruct_observed_report_slice(
            normalization_path,
            normalized_output_dir=normalized_dir,
            reconstructed_output_path=tmp_path / "reconstructed.json",
        )


def test_reconstruction_rejects_duplicate_participant_pair(tmp_path):
    normalization_path, normalized_dir = _fixture(tmp_path, duplicate_participant=True)

    with pytest.raises(ValueError, match="duplicated participants key"):
        reconstruct_observed_report_slice(
            normalization_path,
            normalized_output_dir=normalized_dir,
            reconstructed_output_path=tmp_path / "reconstructed.json",
        )


def test_reconstruction_rejects_full_slice_claim(tmp_path):
    normalization_path, normalized_dir = _fixture(tmp_path)
    normalization = json.loads(normalization_path.read_text())
    normalization["summary"]["full_report_slice_complete"] = True
    _write_json(normalization_path, normalization)

    with pytest.raises(ValueError, match="summary mismatch"):
        reconstruct_observed_report_slice(
            normalization_path,
            normalized_output_dir=normalized_dir,
            reconstructed_output_path=tmp_path / "reconstructed.json",
        )
