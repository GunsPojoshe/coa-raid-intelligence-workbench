from __future__ import annotations

import gzip
import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit

from coa_workbench.normalizer.canonical import find_matches, pointer_get, stable_id

from .report_slice_review import review_observed_report_slice_capture

_EXTRACTION_SCHEMA_VERSION = 1
_EXTRACTION_VERSION = "combatants-candidate-extractor-v1"
_DESIGN_KIND = "observed_combatants_info_mapping_design"
_ENDPOINT_KIND = "combatants_info"
_ROUTE_TEMPLATE = "/api/reports/{template}/encounters/{template}/combatants-info"
_PAYLOAD_HASH = "45672e0f0ff9eb461c575bdd38385795daa6326378bc3f8ad51474276140dc14"
_SCHEMA_FINGERPRINT = "41d6d15422c668f83d2ccae1ec0ff2969671861f9e43b21cb371578961c5f8ff"
_SOURCE_CODE = "coa_ascension_logs"
_ROUTE_PATTERN = re.compile(r"/api/reports/([1-9][0-9]*)/encounters/([1-9][0-9]*)/combatants-info")

_EXPECTED_DESIGNS: dict[str, dict[str, Any]] = {
    "coa-combatants-actor-enrichment-v1": {
        "design_type": "actor_enrichment_observation",
        "selected_field_count": 14,
        "expected_source_match_count": 11,
        "target_entity_type": "actor_enrichment_observation",
        "identity_policy": "existing_stable_actor_id",
        "source_groups": ["actor_identity", "guild_membership", "specialization_summary"],
    },
    "coa-combatants-instance-context-v1": {
        "design_type": "deduplicated_context_observation",
        "selected_field_count": 8,
        "expected_source_match_count": 11,
        "target_entity_type": "combatants_instance_context_observation",
        "identity_policy": "selected_record_sha256",
        "source_groups": ["instance_context"],
    },
    "coa-combatants-talent-container-v1": {
        "design_type": "nested_parser_observation",
        "selected_field_count": 3,
        "expected_source_match_count": 11,
        "target_entity_type": "combatants_talent_container_observation",
        "identity_policy": "raw_match_path_and_selected_record_sha256",
        "source_groups": ["talent_container_summary"],
    },
    "coa-combatants-classless-talent-rank-v1": {
        "design_type": "nested_parser_observation",
        "selected_field_count": 5,
        "expected_source_match_count": 564,
        "target_entity_type": "combatants_classless_talent_rank_observation",
        "identity_policy": "raw_match_path_and_selected_record_sha256",
        "source_groups": ["classless_talent_rank"],
    },
    "coa-combatants-hero-build-entry-v1": {
        "design_type": "nested_parser_observation",
        "selected_field_count": 2,
        "expected_source_match_count": 564,
        "target_entity_type": "combatants_hero_build_entry_observation",
        "identity_policy": "raw_match_path_and_selected_record_sha256",
        "source_groups": ["hero_build_entry"],
    },
    "coa-combatants-gear-slot-v1": {
        "design_type": "nested_parser_observation",
        "selected_field_count": 5,
        "expected_source_match_count": 189,
        "target_entity_type": "combatants_gear_slot_observation",
        "identity_policy": "raw_match_path_and_selected_record_sha256",
        "source_groups": ["gear_slot_summary"],
    },
}


def _generated_at() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_object(path: Path, label: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return payload


def _required_object(value: object, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"combatants extraction field {field_name} must be an object")
    return value


def _required_list(value: object, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"combatants extraction field {field_name} must be an array")
    return value


def _required_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"combatants extraction field {field_name} must be a non-empty string")
    return value


def _required_sha256(value: object, field_name: str) -> str:
    prepared = _required_string(value, field_name).casefold()
    if len(prepared) != 64 or any(char not in "0123456789abcdef" for char in prepared):
        raise ValueError(f"combatants extraction field {field_name} must be a SHA-256 digest")
    return prepared


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _serialize(payload: Mapping[str, Any]) -> bytes:
    return (json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def _write_atomic(path: Path, body: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(body)
    temporary.replace(path)


def _json_type(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    raise TypeError(f"unsupported JSON type: {type(value).__name__}")


def _validate_design(design: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    if design.get("schema_version") != 1 or design.get("design_kind") != _DESIGN_KIND:
        raise ValueError("unsupported combatants-info mapping design")

    endpoint = _required_object(design.get("endpoint"), "endpoint")
    expected_endpoint = {
        "endpoint_kind": _ENDPOINT_KIND,
        "route_template": _ROUTE_TEMPLATE,
        "payload_hash": _PAYLOAD_HASH,
        "schema_fingerprint": _SCHEMA_FINGERPRINT,
        "transport_provenance_type": "upstream_derived",
        "content_provenance_status": "candidate_companion_addon_enrichment",
    }
    for name, expected in expected_endpoint.items():
        if endpoint.get(name) != expected:
            raise ValueError(f"combatants-info mapping design endpoint mismatch: {name}")

    summary = _required_object(design.get("summary"), "summary")
    expected_summary = {
        "mapping_design_count": 6,
        "source_group_count": 8,
        "selected_field_contract_count": 37,
        "actor_enrichment_design_count": 1,
        "context_observation_design_count": 1,
        "nested_observation_design_count": 4,
        "immutable_observation_design_count": 6,
        "dedicated_extractor_design_count": 6,
        "generic_normalizer_compatible_design_count": 0,
        "expected_outer_actor_link_count": 11,
        "deferred_field_count": 19,
        "missing_optional_scope_count": 2,
        "contains_source_scalar_values": False,
        "candidate_mapping_files_ready": False,
        "ready_for_candidate_extractor_implementation": True,
        "combatants_info_enrichment_available": False,
        "normalization_allowed": False,
        "planner_scoring_allowed": False,
    }
    for name, expected in expected_summary.items():
        if summary.get(name) != expected:
            raise ValueError(f"combatants-info mapping design summary mismatch: {name}")

    boundary = _required_object(design.get("decision_boundary"), "decision_boundary")
    expected_boundary = {
        "status": "mapping_design",
        "automatic_implementation": False,
        "candidate_mapping_files_ready": False,
        "generic_normalizer_extension_allowed": False,
        "dedicated_extractor_required": True,
        "exact_raw_validation_required": True,
        "actor_merge_validation_required": True,
        "route_context_validation_required": True,
        "companion_addon_provenance_verified": False,
        "nested_collection_semantics_verified": False,
        "can_promote": False,
        "combatants_info_enrichment_available": False,
        "normalization_allowed": False,
        "mechanic_semantics_verified": False,
        "planner_scoring_allowed": False,
        "ready_for_candidate_extractor_implementation": True,
    }
    for name, expected in expected_boundary.items():
        if boundary.get(name) != expected:
            raise ValueError(f"combatants-info mapping design boundary mismatch: {name}")

    rows: dict[str, dict[str, Any]] = {}
    total_contracts = 0
    for raw_row in _required_list(design.get("mapping_designs"), "mapping_designs"):
        row = _required_object(raw_row, "mapping_designs[]")
        design_id = _required_string(row.get("design_id"), "design_id")
        expected = _EXPECTED_DESIGNS.get(design_id)
        if expected is None or design_id in rows:
            raise ValueError(f"unsupported or duplicated combatants design: {design_id}")
        for name in (
            "design_type",
            "selected_field_count",
            "expected_source_match_count",
        ):
            if row.get(name) != expected[name]:
                raise ValueError(f"combatants design mismatch: {design_id} {name}")
        if row.get("design_version") != "1" or row.get("implementation_status") != "design_only":
            raise ValueError(f"combatants design state mismatch: {design_id}")
        if row.get("candidate_mapping_file") is not None:
            raise ValueError(f"combatants design unexpectedly has a mapping file: {design_id}")
        if row.get("source_groups") != expected["source_groups"]:
            raise ValueError(f"combatants design source groups mismatch: {design_id}")
        if row.get("generic_normalizer_compatible") is not False:
            raise ValueError(f"combatants design generic-normalizer boundary changed: {design_id}")
        if row.get("dedicated_extractor_required") is not True:
            raise ValueError(f"combatants design dedicated extractor boundary changed: {design_id}")
        if row.get("exact_raw_validation_required") is not True:
            raise ValueError(f"combatants design exact raw boundary changed: {design_id}")
        if row.get("promotion_allowed") is not False or row.get("normalization_allowed") is not False:
            raise ValueError(f"combatants design promotion boundary changed: {design_id}")

        target = _required_object(row.get("target"), "target")
        if target.get("storage_table") != "canonical_entity_observation":
            raise ValueError(f"combatants design target table mismatch: {design_id}")
        if target.get("entity_type") != expected["target_entity_type"]:
            raise ValueError(f"combatants design target entity mismatch: {design_id}")
        if target.get("trust_status") != "observed_candidate":
            raise ValueError(f"combatants design trust status mismatch: {design_id}")
        if target.get("core_entity_mutation_allowed") is not False:
            raise ValueError(f"combatants design core mutation boundary changed: {design_id}")

        identity = _required_object(row.get("identity_contract"), "identity_contract")
        if identity.get("identity_policy") != expected["identity_policy"]:
            raise ValueError(f"combatants design identity policy mismatch: {design_id}")
        if identity.get("selected_record_sha256_required") is not True:
            raise ValueError(f"combatants design record hash boundary changed: {design_id}")
        if identity.get("semantic_uniqueness_claimed") is not False:
            raise ValueError(f"combatants design semantic uniqueness changed: {design_id}")

        contracts = _required_list(row.get("field_contracts"), "field_contracts")
        if len(contracts) != expected["selected_field_count"]:
            raise ValueError(f"combatants design contract count mismatch: {design_id}")
        for raw_contract in contracts:
            contract = _required_object(raw_contract, "field_contracts[]")
            _required_string(contract.get("source_group"), "source_group")
            _required_string(contract.get("source_path"), "source_path")
            _required_string(contract.get("output_field"), "output_field")
            if contract.get("parser_status") != "reviewed_candidate":
                raise ValueError(f"combatants parser status mismatch: {design_id}")
            if contract.get("semantic_status") != "unverified":
                raise ValueError(f"combatants semantic boundary changed: {design_id}")
            if not isinstance(contract.get("required"), bool):
                raise ValueError(f"combatants required flag invalid: {design_id}")
            types = _required_list(contract.get("types"), "types")
            if not types or any(not isinstance(item, str) or not item for item in types):
                raise ValueError(f"combatants type contract invalid: {design_id}")
            total_contracts += 1
        rows[design_id] = row

    if set(rows) != set(_EXPECTED_DESIGNS) or total_contracts != 37:
        raise ValueError("combatants-info mapping design set or contract count mismatch")
    return rows


def _capture_endpoint(capture: Mapping[str, Any]) -> dict[str, Any]:
    if capture.get("schema_version") != 1 or capture.get("capture_kind") != "observed_report_slice":
        raise ValueError("unsupported observed report slice capture")
    matches = [
        _required_object(row, "capture.endpoints[]")
        for row in _required_list(capture.get("endpoints"), "capture.endpoints")
        if isinstance(row, dict) and row.get("endpoint_kind") == _ENDPOINT_KIND
    ]
    if len(matches) != 1:
        raise ValueError("capture must contain one combatants-info endpoint")
    row = matches[0]
    if row.get("route_template") != _ROUTE_TEMPLATE or row.get("complete") is not True:
        raise ValueError("combatants-info capture endpoint is not complete")
    capture_row = _required_object(row.get("capture"), "capture endpoint")
    if capture_row.get("payload_hash") != _PAYLOAD_HASH:
        raise ValueError("combatants-info capture payload hash mismatch")
    if capture_row.get("schema_fingerprint") != _SCHEMA_FINGERPRINT:
        raise ValueError("combatants-info capture fingerprint mismatch")
    return capture_row


def _load_observation_context(
    capture_row: Mapping[str, Any],
    *,
    raw_root: Path,
) -> dict[str, Any]:
    observation_id = _required_sha256(capture_row.get("observation_id"), "observation_id")
    raw_id = _required_sha256(capture_row.get("raw_id"), "raw_id")
    root = raw_root.resolve()
    candidates = list(root.rglob(f"*_{observation_id[:16]}.json"))
    candidates = [path for path in candidates if path.parent.name == "observations"]
    if len(candidates) != 1:
        raise ValueError("unable to resolve the exact combatants observation manifest")
    path = candidates[0].resolve()
    if not path.is_relative_to(root):
        raise ValueError("combatants observation manifest escaped raw-root")
    manifest = _load_object(path, "combatants observation manifest")
    if manifest.get("schema_version") != 1:
        raise ValueError("unsupported combatants observation manifest")
    if manifest.get("observation_id") != observation_id or manifest.get("raw_id") != raw_id:
        raise ValueError("combatants observation manifest identity mismatch")
    metadata = _required_object(manifest.get("metadata"), "observation metadata")
    if metadata.get("endpoint_kind") != _ENDPOINT_KIND:
        raise ValueError("combatants observation endpoint kind mismatch")
    if metadata.get("route_template") != _ROUTE_TEMPLATE:
        raise ValueError("combatants observation route template mismatch")
    request_url = _required_string(manifest.get("request_url"), "request_url")
    route_path = urlsplit(request_url).path
    match = _ROUTE_PATTERN.fullmatch(route_path)
    if match is None:
        raise ValueError("combatants observation request route does not match the exact route contract")
    return {
        "observation_id": observation_id,
        "raw_id": raw_id,
        "source_report_id": match.group(1),
        "source_encounter_id": match.group(2),
        "route_path": route_path,
    }


def _load_verified_payload(endpoint: Mapping[str, Any], *, raw_root: Path) -> Any:
    root = raw_root.resolve()
    relative = _required_string(endpoint.get("payload_path"), "payload_path")
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or not path.is_file() or not path.name.endswith(".json.gz"):
        raise ValueError("combatants payload must be a gzip JSON archive below raw-root")
    body = gzip.decompress(path.read_bytes())
    if hashlib.sha256(body).hexdigest() != _PAYLOAD_HASH:
        raise ValueError("combatants payload hash changed before candidate extraction")
    payload = json.loads(body)
    if not isinstance(payload, dict):
        raise ValueError("combatants payload must contain an object")
    return payload


def _load_database_context(
    database_path: Path,
    *,
    source_report_id: str,
    source_encounter_id: str,
) -> dict[str, Any]:
    if not database_path.is_file():
        raise ValueError("combatants extraction database does not exist")
    import duckdb

    expected_report_id = stable_id("report", _SOURCE_CODE, source_report_id)
    expected_encounter_id = stable_id(
        "encounter",
        _SOURCE_CODE,
        source_report_id,
        source_encounter_id,
    )
    with duckdb.connect(str(database_path), read_only=True) as connection:
        report_rows = connection.execute(
            "SELECT report_id FROM report WHERE source_report_id = ?",
            [source_report_id],
        ).fetchall()
        encounter_rows = connection.execute(
            "SELECT encounter_id, report_id FROM encounter WHERE source_encounter_id = ?",
            [source_encounter_id],
        ).fetchall()
        actor_rows = connection.execute(
            "SELECT actor_id, source_actor_id, nickname FROM actor WHERE source_actor_id IS NOT NULL"
        ).fetchall()
    if report_rows != [(expected_report_id,)]:
        raise ValueError("combatants route report does not resolve to the persisted report")
    if encounter_rows != [(expected_encounter_id, expected_report_id)]:
        raise ValueError("combatants route encounter does not resolve to the persisted encounter")
    actors: dict[str, dict[str, Any]] = {}
    for actor_id, source_actor_id, nickname in actor_rows:
        source_key = str(source_actor_id)
        if source_key in actors:
            raise ValueError(f"duplicate persisted source actor id: {source_key}")
        actors[source_key] = {
            "actor_id": str(actor_id),
            "nickname": nickname,
        }
    return {
        "report_id": expected_report_id,
        "encounter_id": expected_encounter_id,
        "actors": actors,
    }


def _outer_actor(payload: Mapping[str, Any], raw_path: str) -> tuple[str, str]:
    segments = raw_path.strip("/").split("/")
    if len(segments) < 2 or segments[0] != "combatants":
        raise ValueError(f"combatants match is outside the outer collection: {raw_path}")
    outer_path = f"/combatants/{segments[1]}"
    outer = pointer_get(payload, outer_path)
    if not isinstance(outer, dict):
        raise ValueError(f"combatants outer row is not an object: {outer_path}")
    source_actor_id = outer.get("character_id")
    if not isinstance(source_actor_id, int) or isinstance(source_actor_id, bool):
        raise ValueError(f"combatants outer actor id is invalid: {outer_path}")
    return str(source_actor_id), outer_path


def _extract_contract_fields(
    match_value: object,
    *,
    scope: str,
    contracts: list[dict[str, Any]],
) -> dict[str, Any]:
    if not isinstance(match_value, dict):
        raise ValueError(f"combatants selected scope is not an object: {scope}")
    result: dict[str, Any] = {}
    for contract in contracts:
        source_path = _required_string(contract.get("source_path"), "source_path")
        prefix = scope.rstrip("/") + "/"
        if not source_path.startswith(prefix):
            raise ValueError(f"combatants contract is outside its source scope: {source_path}")
        relative = "/" + source_path.removeprefix(prefix)
        value = pointer_get(match_value, relative, None)
        required = contract.get("required") is True
        if value is None:
            if required:
                raise ValueError(f"required combatants field is missing: {source_path}")
            result[_required_string(contract.get("output_field"), "output_field")] = None
            continue
        allowed_types = set(_required_list(contract.get("types"), "types"))
        actual_type = _json_type(value)
        if actual_type not in allowed_types:
            raise ValueError(
                f"combatants field type mismatch: {source_path} expected={sorted(allowed_types)} "
                f"actual={actual_type}"
            )
        result[_required_string(contract.get("output_field"), "output_field")] = value
    return result


def _contracts_by_group(row: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for raw_contract in _required_list(row.get("field_contracts"), "field_contracts"):
        contract = _required_object(raw_contract, "field_contracts[]")
        group = _required_string(contract.get("source_group"), "source_group")
        result[group].append(contract)
    return dict(result)


def _observation_row(
    *,
    design_id: str,
    entity_type: str,
    payload_hash: str,
    report_id: str,
    encounter_id: str,
    actor_id: str | None,
    source_actor_id: str | None,
    raw_path: str | None,
    selected_fields: Mapping[str, Any],
) -> dict[str, Any]:
    record_hash = _sha256_json(selected_fields)
    identity_path = raw_path or "<no-raw-path>"
    observation_id = stable_id(
        "combatants_candidate_observation",
        design_id,
        payload_hash,
        identity_path,
        record_hash,
        actor_id or "",
    )
    return {
        "observation_id": observation_id,
        "design_id": design_id,
        "entity_type": entity_type,
        "report_id": report_id,
        "encounter_id": encounter_id,
        "actor_id": actor_id,
        "source_actor_id": source_actor_id,
        "raw_match_path": raw_path,
        "selected_record_sha256": record_hash,
        "selected_fields": dict(selected_fields),
        "trust_status": "observed_candidate",
    }


def extract_combatants_info_candidate_payload(
    payload: Mapping[str, Any],
    designs: Mapping[str, Mapping[str, Any]],
    *,
    report_id: str,
    encounter_id: str,
    actor_index: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]], dict[str, Any]]:
    """Extract private candidate observations from one exact combatants-info payload."""
    scopes_by_group: dict[str, str] = {}
    for row in designs.values():
        groups = _required_list(row.get("source_groups"), "source_groups")
        scopes = _required_list(row.get("source_scopes"), "source_scopes")
        if len(groups) != len(scopes):
            raise ValueError("combatants design group/scope count mismatch")
        for group, scope in zip(groups, scopes, strict=True):
            group_name = _required_string(group, "source group")
            scope_path = _required_string(scope, "source scope")
            existing = scopes_by_group.setdefault(group_name, scope_path)
            if existing != scope_path:
                raise ValueError(f"combatants source group has conflicting scopes: {group_name}")

    matches_by_group = {
        group: list(find_matches(payload, scope)) for group, scope in scopes_by_group.items()
    }
    observations: dict[str, list[dict[str, Any]]] = {}
    receipt_rows: list[dict[str, Any]] = []
    linked_source_actors: set[str] = set()
    actor_name_match_count = 0

    for design_id in sorted(designs):
        row = designs[design_id]
        expected = _EXPECTED_DESIGNS[design_id]
        contracts_by_group = _contracts_by_group(row)
        entity_type = _required_object(row.get("target"), "target")["entity_type"]
        output_rows: list[dict[str, Any]] = []
        source_match_count = 0
        duplicate_count = 0

        if row.get("design_type") == "actor_enrichment_observation":
            group_records: dict[str, dict[str, tuple[str, dict[str, Any]]]] = {}
            for group in expected["source_groups"]:
                scope = scopes_by_group[group]
                records: dict[str, tuple[str, dict[str, Any]]] = {}
                matches = matches_by_group[group]
                if len(matches) != expected["expected_source_match_count"]:
                    raise ValueError(f"combatants source match count mismatch: {design_id} {group}")
                for match in matches:
                    source_actor_id, outer_path = _outer_actor(payload, match.path)
                    if source_actor_id in records:
                        raise ValueError(f"duplicate actor match inside combatants group: {group}")
                    fields = _extract_contract_fields(
                        match.value,
                        scope=scope,
                        contracts=contracts_by_group[group],
                    )
                    records[source_actor_id] = (outer_path, fields)
                group_records[group] = records
            actor_sets = [set(records) for records in group_records.values()]
            if not actor_sets or any(actor_set != actor_sets[0] for actor_set in actor_sets[1:]):
                raise ValueError("combatants actor enrichment groups do not reference the same actors")
            source_match_count = len(actor_sets[0])
            for source_actor_id in sorted(actor_sets[0], key=int):
                persisted = actor_index.get(source_actor_id)
                if persisted is None:
                    raise ValueError(f"combatants actor is missing from persisted actor table: {source_actor_id}")
                expected_actor_id = stable_id("actor", _SOURCE_CODE, source_actor_id)
                if persisted.get("actor_id") != expected_actor_id:
                    raise ValueError(f"combatants actor stable id mismatch: {source_actor_id}")
                selected_fields: dict[str, Any] = {}
                outer_path = ""
                for group in expected["source_groups"]:
                    group_path, fields = group_records[group][source_actor_id]
                    outer_path = group_path
                    overlap = set(selected_fields).intersection(fields)
                    if overlap:
                        raise ValueError(f"combatants actor output field collision: {sorted(overlap)}")
                    selected_fields.update(fields)
                nickname = persisted.get("nickname")
                if nickname not in (None, "") and nickname != selected_fields.get("name"):
                    raise ValueError(f"combatants actor nickname conflict: {source_actor_id}")
                actor_name_match_count += 1
                linked_source_actors.add(source_actor_id)
                output_rows.append(
                    _observation_row(
                        design_id=design_id,
                        entity_type=str(entity_type),
                        payload_hash=_PAYLOAD_HASH,
                        report_id=report_id,
                        encounter_id=encounter_id,
                        actor_id=expected_actor_id,
                        source_actor_id=source_actor_id,
                        raw_path=outer_path,
                        selected_fields=selected_fields,
                    )
                )

        elif row.get("design_type") == "deduplicated_context_observation":
            group = expected["source_groups"][0]
            scope = scopes_by_group[group]
            matches = matches_by_group[group]
            source_match_count = len(matches)
            if source_match_count != expected["expected_source_match_count"]:
                raise ValueError(f"combatants source match count mismatch: {design_id}")
            grouped: dict[str, dict[str, Any]] = {}
            for match in matches:
                source_actor_id, _outer_path = _outer_actor(payload, match.path)
                persisted = actor_index.get(source_actor_id)
                if persisted is None:
                    raise ValueError(f"combatants context actor is not persisted: {source_actor_id}")
                selected_fields = _extract_contract_fields(
                    match.value,
                    scope=scope,
                    contracts=contracts_by_group[group],
                )
                record_hash = _sha256_json(selected_fields)
                bucket = grouped.setdefault(
                    record_hash,
                    {
                        "fields": selected_fields,
                        "actor_ids": [],
                        "source_actor_ids": [],
                        "raw_paths": [],
                    },
                )
                bucket["actor_ids"].append(persisted["actor_id"])
                bucket["source_actor_ids"].append(source_actor_id)
                bucket["raw_paths"].append(match.path)
                linked_source_actors.add(source_actor_id)
            for record_hash in sorted(grouped):
                bucket = grouped[record_hash]
                observation = _observation_row(
                    design_id=design_id,
                    entity_type=str(entity_type),
                    payload_hash=_PAYLOAD_HASH,
                    report_id=report_id,
                    encounter_id=encounter_id,
                    actor_id=None,
                    source_actor_id=None,
                    raw_path=None,
                    selected_fields=bucket["fields"],
                )
                observation["linked_actor_ids"] = sorted(bucket["actor_ids"])
                observation["linked_source_actor_ids"] = sorted(
                    bucket["source_actor_ids"], key=int
                )
                observation["source_raw_match_paths"] = sorted(bucket["raw_paths"])
                output_rows.append(observation)
            duplicate_count = source_match_count - len(output_rows)

        else:
            group = expected["source_groups"][0]
            scope = scopes_by_group[group]
            matches = matches_by_group[group]
            source_match_count = len(matches)
            if source_match_count != expected["expected_source_match_count"]:
                raise ValueError(f"combatants source match count mismatch: {design_id}")
            observed_paths: set[str] = set()
            for match in matches:
                if match.path in observed_paths:
                    raise ValueError(f"duplicate combatants raw match path: {match.path}")
                observed_paths.add(match.path)
                source_actor_id, _outer_path = _outer_actor(payload, match.path)
                persisted = actor_index.get(source_actor_id)
                if persisted is None:
                    raise ValueError(f"combatants nested actor is not persisted: {source_actor_id}")
                selected_fields = _extract_contract_fields(
                    match.value,
                    scope=scope,
                    contracts=contracts_by_group[group],
                )
                linked_source_actors.add(source_actor_id)
                output_rows.append(
                    _observation_row(
                        design_id=design_id,
                        entity_type=str(entity_type),
                        payload_hash=_PAYLOAD_HASH,
                        report_id=report_id,
                        encounter_id=encounter_id,
                        actor_id=str(persisted["actor_id"]),
                        source_actor_id=source_actor_id,
                        raw_path=match.path,
                        selected_fields=selected_fields,
                    )
                )

        observations[design_id] = output_rows
        receipt_rows.append(
            {
                "design_id": design_id,
                "design_type": row["design_type"],
                "target_entity_type": entity_type,
                "selected_field_count": row["selected_field_count"],
                "source_match_count": source_match_count,
                "output_observation_count": len(output_rows),
                "deduplicated_source_match_count": duplicate_count,
                "all_selected_field_types_verified": True,
                "all_actor_links_verified": True,
                "all_record_hashes_created": True,
                "core_entity_mutation_performed": False,
            }
        )

    total_source_matches = sum(row["source_match_count"] for row in receipt_rows)
    total_observations = sum(row["output_observation_count"] for row in receipt_rows)
    if total_source_matches != sum(
        expected["expected_source_match_count"] for expected in _EXPECTED_DESIGNS.values()
    ):
        raise ValueError("combatants aggregate source match count mismatch")
    if len(linked_source_actors) != 11:
        raise ValueError("combatants linked actor set mismatch")
    if actor_name_match_count != 11:
        raise ValueError("combatants actor nickname validation count mismatch")
    summary = {
        "design_count": len(receipt_rows),
        "selected_field_contract_count": 37,
        "source_match_count": total_source_matches,
        "output_observation_count": total_observations,
        "linked_actor_count": len(linked_source_actors),
        "actor_name_exact_match_count": actor_name_match_count,
        "deduplicated_source_match_count": sum(
            row["deduplicated_source_match_count"] for row in receipt_rows
        ),
    }
    return observations, receipt_rows, summary


def extract_observed_combatants_info_candidates(
    design_path: Path,
    *,
    capture_path: Path,
    route_inventory_path: Path,
    raw_root: Path,
    database_path: Path,
    extraction_output_path: Path,
) -> dict[str, Any]:
    """Run the exact offline candidate extractor and return a scalar-free receipt."""
    design = _load_object(design_path, "combatants-info mapping design")
    designs = _validate_design(design)
    structural = review_observed_report_slice_capture(
        capture_path,
        route_inventory_path=route_inventory_path,
        raw_root=raw_root,
    )
    endpoint_rows = {
        row["endpoint_kind"]: row
        for raw_row in _required_list(structural.get("endpoints"), "structural endpoints")
        for row in [_required_object(raw_row, "structural endpoints[]")]
    }
    endpoint = endpoint_rows.get(_ENDPOINT_KIND)
    if endpoint is None:
        raise ValueError("structural review is missing combatants-info")
    if endpoint.get("route_template") != _ROUTE_TEMPLATE:
        raise ValueError("combatants structural route mismatch")
    if endpoint.get("payload_hash") != _PAYLOAD_HASH:
        raise ValueError("combatants structural payload hash mismatch")
    if endpoint.get("schema_fingerprint") != _SCHEMA_FINGERPRINT:
        raise ValueError("combatants structural fingerprint mismatch")

    capture = _load_object(capture_path, "observed report slice capture")
    capture_row = _capture_endpoint(capture)
    route_context = _load_observation_context(capture_row, raw_root=raw_root)
    database_context = _load_database_context(
        database_path,
        source_report_id=route_context["source_report_id"],
        source_encounter_id=route_context["source_encounter_id"],
    )
    payload = _load_verified_payload(endpoint, raw_root=raw_root)
    observations, receipt_rows, extraction_summary = extract_combatants_info_candidate_payload(
        payload,
        designs,
        report_id=database_context["report_id"],
        encounter_id=database_context["encounter_id"],
        actor_index=database_context["actors"],
    )

    private_payload = {
        "schema_version": _EXTRACTION_SCHEMA_VERSION,
        "extraction_kind": "observed_combatants_info_candidate_extraction_batch",
        "extraction_version": _EXTRACTION_VERSION,
        "source_code": _SOURCE_CODE,
        "source_payload_hash": _PAYLOAD_HASH,
        "schema_fingerprint": _SCHEMA_FINGERPRINT,
        "raw_id": route_context["raw_id"],
        "observation_id": route_context["observation_id"],
        "source_report_id": route_context["source_report_id"],
        "source_encounter_id": route_context["source_encounter_id"],
        "report_id": database_context["report_id"],
        "encounter_id": database_context["encounter_id"],
        "observations": observations,
        "summary": extraction_summary,
    }
    private_body = _serialize(private_payload)
    _write_atomic(extraction_output_path, private_body)

    checks = {
        "exact_mapping_design_verified": True,
        "exact_raw_archive_verified": True,
        "exact_observation_manifest_verified": True,
        "route_context_verified": True,
        "persisted_report_reference_verified": True,
        "persisted_encounter_reference_verified": True,
        "all_actor_stable_ids_verified": True,
        "all_actor_names_exact_match": True,
        "all_selected_field_types_verified": True,
        "all_source_match_counts_verified": True,
        "all_record_hashes_created": True,
        "core_entity_mutation_not_performed": True,
    }
    return {
        "schema_version": _EXTRACTION_SCHEMA_VERSION,
        "extraction_kind": "observed_combatants_info_candidate_extraction",
        "extraction_version": _EXTRACTION_VERSION,
        "generated_at": _generated_at(),
        "source_design_name": design_path.name,
        "source_capture_name": capture_path.name,
        "source_payload_hash": _PAYLOAD_HASH,
        "schema_fingerprint": _SCHEMA_FINGERPRINT,
        "private_extraction_file": extraction_output_path.name,
        "private_extraction_sha256": hashlib.sha256(private_body).hexdigest(),
        "design_results": receipt_rows,
        "integrity_checks": checks,
        "decision_boundary": {
            "status": "candidate_extracted",
            "automatic_persistence": False,
            "candidate_mapping_files_ready": False,
            "actor_merge_verified_for_exact_payload": True,
            "route_context_verified_for_exact_payload": True,
            "companion_addon_provenance_verified": False,
            "nested_collection_semantics_verified": False,
            "can_promote": False,
            "combatants_info_enrichment_available": False,
            "normalization_allowed": False,
            "mechanic_semantics_verified": False,
            "planner_scoring_allowed": False,
            "ready_for_manual_candidate_extraction_validation": True,
            "private_extraction_contains_source_scalar_values": True,
        },
        "summary": {
            **extraction_summary,
            "exact_raw_archive_count": 1,
            "integrity_check_count": len(checks),
            "all_integrity_checks_passed": True,
            "contains_source_scalar_values": False,
            "private_extraction_contains_source_scalar_values": True,
            "candidate_mapping_files_ready": False,
            "automatic_persistence": False,
            "ready_for_manual_candidate_extraction_validation": True,
            "combatants_info_enrichment_available": False,
            "normalization_allowed": False,
            "planner_scoring_allowed": False,
        },
    }
