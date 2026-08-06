from __future__ import annotations

import gzip
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from coa_workbench.normalizer.canonical import NormalizationMapping, normalize_payload

from .report_slice_review import review_observed_report_slice_capture

_NORMALIZATION_SCHEMA_VERSION = 1
_PUBLICATION_KIND = "observed_report_slice_verified_mapping_publication"
_EXPECTED_MAPPINGS = {
    "coa-encounter-detail-v1": {
        "mapping_file": "coa_encounter_detail_v1.json",
        "endpoint_kind": "encounter_detail",
        "route_template": "/api/reports/{template}/encounters/{template}",
        "field_contract_count": 35,
        "expected_counts": {
            "reports": 1,
            "encounters": 1,
            "actors": 31,
            "participants": 31,
            "aura_events": 0,
            "rejects": 0,
        },
    },
    "coa-report-detail-v1": {
        "mapping_file": "coa_report_detail_v1.json",
        "endpoint_kind": "report_detail",
        "route_template": "/api/reports/{template}",
        "field_contract_count": 19,
        "expected_counts": {
            "reports": 1,
            "encounters": 14,
            "actors": 0,
            "participants": 0,
            "aura_events": 0,
            "rejects": 0,
        },
    },
}


def _generated_at() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_object(path: Path, description: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{description} must contain a JSON object")
    return payload


def _required_object(value: object, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"report slice normalization field {field_name} must be an object")
    return value


def _required_list(value: object, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"report slice normalization field {field_name} must be an array")
    return value


def _required_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(
            f"report slice normalization field {field_name} must be a non-empty string"
        )
    return value


def _required_boolean(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"report slice normalization field {field_name} must be a boolean")
    return value


def _required_sha256(value: object, field_name: str) -> str:
    prepared = _required_string(value, field_name).casefold()
    if len(prepared) != 64 or any(char not in "0123456789abcdef" for char in prepared):
        raise ValueError(f"report slice normalization field {field_name} must be a SHA-256 digest")
    return prepared


def _serialize(payload: Mapping[str, Any]) -> bytes:
    return (json.dumps(dict(payload), indent=2, sort_keys=True) + "\n").encode()


def _write_atomic(path: Path, body: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(body)
    temporary.replace(path)


def _validate_publication(
    publication: Mapping[str, Any],
    *,
    mapping_dir: Path,
) -> dict[str, dict[str, Any]]:
    if publication.get("schema_version") != 1:
        raise ValueError("unsupported report slice publication schema version")
    if publication.get("publication_kind") != _PUBLICATION_KIND:
        raise ValueError("unexpected report slice publication kind")

    summary = _required_object(publication.get("summary"), "summary")
    expected_summary = {
        "mapping_count": 2,
        "field_contract_count": 54,
        "all_staged_files_match_promotion": True,
        "all_targets_published": True,
        "contains_source_scalar_values": False,
        "selected_parser_normalization_allowed": True,
        "mechanic_semantics_verified": False,
        "full_report_slice_complete": False,
    }
    for field_name, expected in expected_summary.items():
        if summary.get(field_name) != expected:
            raise ValueError(f"report slice publication summary mismatch: {field_name}")

    boundary = _required_object(publication.get("decision_boundary"), "decision_boundary")
    expected_boundary = {
        "status": "published",
        "automatic_publication": False,
        "manual_publication_completed": True,
        "selected_parser_normalization_allowed": True,
        "mechanic_semantics_verified": False,
        "combatants_info_enrichment_available": False,
        "aura_normalization_available": False,
        "full_report_slice_complete": False,
    }
    for field_name, expected in expected_boundary.items():
        if boundary.get(field_name) != expected:
            raise ValueError(f"report slice publication boundary mismatch: {field_name}")

    rows: dict[str, dict[str, Any]] = {}
    for raw_row in _required_list(publication.get("published_mappings"), "published_mappings"):
        row = _required_object(raw_row, "published_mappings[]")
        mapping_id = _required_string(row.get("mapping_id"), "mapping_id")
        if mapping_id not in _EXPECTED_MAPPINGS or mapping_id in rows:
            raise ValueError(f"unsupported or duplicated published mapping: {mapping_id}")
        expected = _EXPECTED_MAPPINGS[mapping_id]
        mapping_file = _required_string(row.get("mapping_file"), "mapping_file")
        if mapping_file != expected["mapping_file"]:
            raise ValueError(f"published mapping file mismatch for {mapping_id}")
        if row.get("status") != "verified":
            raise ValueError(f"published mapping {mapping_id} must be verified")
        if row.get("field_contract_count") != expected["field_contract_count"]:
            raise ValueError(f"published field contract count mismatch for {mapping_id}")
        if not isinstance(row.get("already_current"), bool):
            raise ValueError(f"published mapping current-state flag is invalid for {mapping_id}")
        target_path = Path(_required_string(row.get("target_path"), "target_path"))
        if target_path.name != mapping_file:
            raise ValueError(f"published target path mismatch for {mapping_id}")

        mapping_path = mapping_dir / mapping_file
        mapping_body = mapping_path.read_bytes()
        expected_hash = _required_sha256(row.get("content_sha256"), "content_sha256")
        if hashlib.sha256(mapping_body).hexdigest() != expected_hash:
            raise ValueError(f"published mapping content hash mismatch for {mapping_id}")
        mapping = json.loads(mapping_body)
        if not isinstance(mapping, dict):
            raise ValueError(f"published mapping {mapping_id} must contain an object")
        if mapping.get("mapping_id") != mapping_id:
            raise ValueError(f"published mapping id mismatch for {mapping_id}")
        if mapping.get("status") != "verified":
            raise ValueError(f"published mapping file is not verified: {mapping_id}")
        if mapping.get("route_template") != expected["route_template"]:
            raise ValueError(f"published mapping route mismatch for {mapping_id}")
        if mapping.get("event_type_map") != {}:
            raise ValueError(f"published mapping {mapping_id} must not define aura semantics")
        if mapping.get("mechanic_semantics_verified") is not False:
            raise ValueError(f"published mapping mechanics boundary changed for {mapping_id}")
        if mapping.get("verification_scope") != (
            "parser_schema_raw_archive_dry_run_and_cross_payload_linkage_only"
        ):
            raise ValueError(f"published mapping verification scope mismatch for {mapping_id}")
        contracts = _required_list(mapping.get("field_contracts"), "field_contracts")
        if len(contracts) != expected["field_contract_count"]:
            raise ValueError(f"published embedded contract count mismatch for {mapping_id}")
        for raw_contract in contracts:
            contract = _required_object(raw_contract, "field_contracts[]")
            if contract.get("semantic_status") != "verified_parser_field":
                raise ValueError(f"published parser field is not verified for {mapping_id}")
        if not NormalizationMapping.from_dict(mapping).production_ready:
            raise ValueError(f"published mapping is not production ready: {mapping_id}")

        rows[mapping_id] = {
            "mapping": mapping,
            "mapping_file": mapping_file,
            "mapping_content_sha256": expected_hash,
            "expected": expected,
        }

    if set(rows) != set(_EXPECTED_MAPPINGS):
        raise ValueError("published mapping set mismatch")
    return rows


def _load_archived_payload(endpoint: Mapping[str, Any], *, raw_root: Path) -> Any:
    root = raw_root.resolve()
    relative_path = _required_string(endpoint.get("payload_path"), "payload_path")
    path = (root / relative_path).resolve()
    if not path.is_relative_to(root) or not path.is_file() or not path.name.endswith(".json.gz"):
        raise ValueError("reviewed payload must be a gzip JSON archive below raw-root")
    body = gzip.decompress(path.read_bytes())
    expected_hash = _required_sha256(endpoint.get("payload_hash"), "payload_hash")
    if hashlib.sha256(body).hexdigest() != expected_hash:
        raise ValueError("reviewed payload hash changed before normalization")
    return json.loads(body)


def normalize_observed_report_slice_selected_parser_mappings(
    publication_path: Path,
    *,
    mapping_dir: Path,
    capture_path: Path,
    route_inventory_path: Path,
    raw_root: Path,
    normalized_output_dir: Path,
) -> dict[str, Any]:
    """Normalize the two published parser mappings and return a scalar-free receipt."""
    publication = _load_object(publication_path, "report slice mapping publication")
    published = _validate_publication(publication, mapping_dir=mapping_dir)
    structural = review_observed_report_slice_capture(
        capture_path,
        route_inventory_path=route_inventory_path,
        raw_root=raw_root,
    )
    endpoints = {
        _required_string(row.get("endpoint_kind"), "endpoint_kind"): row
        for raw_row in _required_list(structural.get("endpoints"), "endpoints")
        for row in [_required_object(raw_row, "endpoints[]")]
    }

    batches: dict[str, Any] = {}
    receipt_rows: list[dict[str, Any]] = []
    aggregate_counts = {
        "reports": 0,
        "encounters": 0,
        "actors": 0,
        "participants": 0,
        "aura_events": 0,
        "rejects": 0,
    }

    for mapping_id in sorted(published):
        row = published[mapping_id]
        mapping = row["mapping"]
        expected = row["expected"]
        endpoint = endpoints.get(expected["endpoint_kind"])
        if endpoint is None:
            raise ValueError(f"structural review endpoint is missing: {expected['endpoint_kind']}")
        if endpoint.get("route_template") != mapping.get("route_template"):
            raise ValueError(f"normalization route mismatch for {mapping_id}")
        if endpoint.get("payload_hash") != mapping.get("reviewed_payload_hash"):
            raise ValueError(f"normalization payload hash mismatch for {mapping_id}")
        if endpoint.get("schema_fingerprint") != mapping.get("schema_fingerprint"):
            raise ValueError(f"normalization schema fingerprint mismatch for {mapping_id}")

        payload = _load_archived_payload(endpoint, raw_root=raw_root)
        batch = normalize_payload(
            payload,
            NormalizationMapping.from_dict(mapping),
            schema_fingerprint=_required_sha256(mapping.get("schema_fingerprint"), "schema_fingerprint"),
        )
        counts = batch.counts()
        if counts != expected["expected_counts"]:
            raise ValueError(
                f"published mapping normalization counts mismatch for {mapping_id}: "
                f"expected={expected['expected_counts']} actual={counts}"
            )
        for name, count in counts.items():
            aggregate_counts[name] += count

        batch_payload = {
            "schema_version": 1,
            "normalization_kind": "canonical_batch",
            "source_payload_hash": endpoint["payload_hash"],
            "schema_fingerprint": endpoint["schema_fingerprint"],
            "batch": batch.to_dict(),
        }
        batch_body = _serialize(batch_payload)
        output_name = f"{row['mapping_file'].removesuffix('.json')}.normalized.json"
        output_path = normalized_output_dir / output_name
        _write_atomic(output_path, batch_body)
        batches[mapping_id] = batch
        receipt_rows.append(
            {
                "mapping_id": mapping_id,
                "mapping_file": row["mapping_file"],
                "mapping_content_sha256": row["mapping_content_sha256"],
                "source_payload_hash": endpoint["payload_hash"],
                "schema_fingerprint": endpoint["schema_fingerprint"],
                "normalized_batch_file": output_name,
                "normalized_batch_sha256": hashlib.sha256(batch_body).hexdigest(),
                "counts": counts,
                "mapping_hash_verified": True,
                "raw_archive_verified": True,
            }
        )

    report_batch = batches["coa-report-detail-v1"]
    encounter_batch = batches["coa-encounter-detail-v1"]
    report_ids = {row["report_id"] for row in report_batch.reports}
    encounter_report_ids = {row["report_id"] for row in encounter_batch.reports}
    report_encounter_ids = {row["encounter_id"] for row in report_batch.encounters}
    exact_encounter_ids = {row["encounter_id"] for row in encounter_batch.encounters}
    actor_ids = {row["actor_id"] for row in encounter_batch.actors}
    participant_pairs = {
        (row["encounter_id"], row["actor_id"]) for row in encounter_batch.participants
    }
    cross_payload_checks = {
        "single_report_id_in_each_batch": len(report_ids) == 1 and len(encounter_report_ids) == 1,
        "report_id_consistent": report_ids == encounter_report_ids,
        "exact_encounter_present_in_report_batch": len(exact_encounter_ids) == 1
        and exact_encounter_ids.issubset(report_encounter_ids),
        "participant_actor_references_resolved": all(
            row["actor_id"] in actor_ids for row in encounter_batch.participants
        ),
        "participant_encounter_references_resolved": all(
            row["encounter_id"] in exact_encounter_ids for row in encounter_batch.participants
        ),
        "participant_pairs_unique": len(participant_pairs) == len(encounter_batch.participants),
    }
    failed_checks = sorted(name for name, passed in cross_payload_checks.items() if not passed)
    if failed_checks:
        raise ValueError(
            "normalized report slice cross-payload checks failed: " + ", ".join(failed_checks)
        )

    return {
        "schema_version": _NORMALIZATION_SCHEMA_VERSION,
        "normalization_kind": "observed_report_slice_selected_parser_normalization",
        "generated_at": _generated_at(),
        "source_publication_name": publication_path.name,
        "normalized_batches": receipt_rows,
        "cross_payload_checks": cross_payload_checks,
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
            "mapping_count": len(receipt_rows),
            "field_contract_count": 54,
            "exact_raw_archive_count": len(receipt_rows),
            "aggregate_counts": aggregate_counts,
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
    }
