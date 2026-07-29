from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

_ALLOWED_JSON_TYPES = {"array", "boolean", "integer", "null", "number", "object", "string"}
_ALLOWED_STATUSES = {"candidate", "verified"}
_ALLOWED_ENDPOINT_KINDS = {"character", "talent_grid"}
_MAPPING_SCHEMA_VERSION = 1


def _required_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"Armory mapping field {name} must be a non-empty string")
    return value


def _required_integer(value: object, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"Armory mapping field {name} must be a non-negative integer")
    return value


def _sha256(value: object, name: str) -> str:
    prepared = _required_string(value, name).casefold()
    if len(prepared) != 64 or any(char not in "0123456789abcdef" for char in prepared):
        raise ValueError(f"Armory mapping field {name} must be a SHA-256 hex digest")
    return prepared


@dataclass(frozen=True, slots=True)
class ArmoryFieldContract:
    selector: str
    review_path: str
    types: tuple[str, ...]
    nullable: bool
    required: bool
    note: str | None = None

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any], *, name: str) -> ArmoryFieldContract:
        selector = _required_string(payload.get("selector"), f"{name}.selector")
        review_path = _required_string(payload.get("review_path"), f"{name}.review_path")
        if not review_path.startswith("/"):
            raise ValueError(f"Armory mapping field {name}.review_path must be an absolute path")
        raw_types = payload.get("types")
        if not isinstance(raw_types, list) or not raw_types:
            raise ValueError(f"Armory mapping field {name}.types must be a non-empty array")
        types = tuple(sorted({_required_string(value, f"{name}.types[]") for value in raw_types}))
        invalid = set(types) - _ALLOWED_JSON_TYPES
        if invalid:
            raise ValueError(f"Armory mapping field {name} has invalid JSON types: {sorted(invalid)}")
        nullable = payload.get("nullable", False)
        required = payload.get("required", True)
        if not isinstance(nullable, bool) or not isinstance(required, bool):
            raise ValueError(f"Armory mapping field {name} nullable/required flags must be boolean")
        if nullable != ("null" in types):
            raise ValueError(f"Armory mapping field {name} nullable flag does not match its types")
        note = payload.get("note")
        if note is not None and (not isinstance(note, str) or not note):
            raise ValueError(f"Armory mapping field {name}.note must be a non-empty string")
        return cls(selector, review_path, types, nullable, required, note)


@dataclass(frozen=True, slots=True)
class ArmoryCollectionContract:
    path: str
    observed_occurrences: int
    fields: dict[str, ArmoryFieldContract]

    @classmethod
    def from_dict(
        cls,
        payload: Mapping[str, Any],
        *,
        name: str,
    ) -> ArmoryCollectionContract:
        path = _required_string(payload.get("path"), f"collections.{name}.path")
        if not path.startswith("/"):
            raise ValueError(f"Armory collection {name} path must be absolute")
        occurrences = _required_integer(
            payload.get("observed_occurrences"),
            f"collections.{name}.observed_occurrences",
        )
        raw_fields = payload.get("fields")
        if not isinstance(raw_fields, dict) or not raw_fields:
            raise ValueError(f"Armory collection {name} must contain fields")
        fields = {
            _required_string(field_name, f"collections.{name}.fields key"): ArmoryFieldContract.from_dict(
                field_payload,
                name=f"collections.{name}.fields.{field_name}",
            )
            for field_name, field_payload in raw_fields.items()
            if isinstance(field_payload, Mapping)
        }
        if len(fields) != len(raw_fields):
            raise ValueError(f"Armory collection {name} contains a non-object field contract")
        return cls(path, occurrences, fields)


@dataclass(frozen=True, slots=True)
class ArmoryMappingContract:
    mapping_id: str
    source_code: str
    mapping_version: str
    status: str
    endpoint_kind: str
    route_template: str
    schema_fingerprint: str
    reviewed_payload_hash: str
    review_packet_schema_version: int
    provenance_type: str
    singletons: dict[str, ArmoryFieldContract]
    collections: dict[str, ArmoryCollectionContract]
    deferred_scopes: tuple[str, ...]
    review_notes: tuple[str, ...]
    reviewed_by: str | None = None
    reviewed_at: str | None = None

    @property
    def production_ready(self) -> bool:
        return self.status == "verified"

    def require_verified(self) -> None:
        if not self.production_ready:
            raise ValueError(f"Armory mapping {self.mapping_id!r} is not verified")

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ArmoryMappingContract:
        if payload.get("mapping_schema_version") != _MAPPING_SCHEMA_VERSION:
            raise ValueError("unsupported Armory mapping schema version")
        status = _required_string(payload.get("status"), "status")
        if status not in _ALLOWED_STATUSES:
            raise ValueError(f"unsupported Armory mapping status: {status}")
        endpoint_kind = _required_string(payload.get("endpoint_kind"), "endpoint_kind")
        if endpoint_kind not in _ALLOWED_ENDPOINT_KINDS:
            raise ValueError(f"unsupported Armory endpoint kind: {endpoint_kind}")
        route_template = _required_string(payload.get("route_template"), "route_template")
        if not route_template.startswith("/api/armory/"):
            raise ValueError("Armory route_template must be an /api/armory/ route")

        raw_singletons = payload.get("singletons", {})
        raw_collections = payload.get("collections", {})
        if not isinstance(raw_singletons, dict) or not isinstance(raw_collections, dict):
            raise ValueError("Armory mapping singletons and collections must be objects")
        singletons = {
            _required_string(name, "singletons key"): ArmoryFieldContract.from_dict(
                spec,
                name=f"singletons.{name}",
            )
            for name, spec in raw_singletons.items()
            if isinstance(spec, Mapping)
        }
        if len(singletons) != len(raw_singletons):
            raise ValueError("Armory mapping contains a non-object singleton contract")
        collections = {
            _required_string(name, "collections key"): ArmoryCollectionContract.from_dict(
                spec,
                name=name,
            )
            for name, spec in raw_collections.items()
            if isinstance(spec, Mapping)
        }
        if len(collections) != len(raw_collections):
            raise ValueError("Armory mapping contains a non-object collection contract")
        if not singletons and not collections:
            raise ValueError("Armory mapping must contain at least one field contract")

        raw_deferred = payload.get("deferred_scopes", [])
        raw_notes = payload.get("review_notes", [])
        if not isinstance(raw_deferred, list) or not isinstance(raw_notes, list):
            raise ValueError("Armory mapping deferred_scopes and review_notes must be arrays")
        deferred_scopes = tuple(_required_string(value, "deferred_scopes[]") for value in raw_deferred)
        if any(not value.startswith("/") for value in deferred_scopes):
            raise ValueError("Armory mapping deferred scopes must be absolute paths")
        review_notes = tuple(_required_string(value, "review_notes[]") for value in raw_notes)

        reviewed_by = payload.get("reviewed_by")
        reviewed_at = payload.get("reviewed_at")
        if status == "verified":
            reviewed_by = _required_string(reviewed_by, "reviewed_by")
            reviewed_at = _required_string(reviewed_at, "reviewed_at")
        elif reviewed_by is not None or reviewed_at is not None:
            raise ValueError("candidate Armory mappings must not contain verification metadata")

        return cls(
            mapping_id=_required_string(payload.get("mapping_id"), "mapping_id"),
            source_code=_required_string(payload.get("source_code"), "source_code"),
            mapping_version=_required_string(payload.get("mapping_version"), "mapping_version"),
            status=status,
            endpoint_kind=endpoint_kind,
            route_template=route_template,
            schema_fingerprint=_sha256(payload.get("schema_fingerprint"), "schema_fingerprint"),
            reviewed_payload_hash=_sha256(
                payload.get("reviewed_payload_hash"),
                "reviewed_payload_hash",
            ),
            review_packet_schema_version=_required_integer(
                payload.get("review_packet_schema_version"),
                "review_packet_schema_version",
            ),
            provenance_type=_required_string(payload.get("provenance_type"), "provenance_type"),
            singletons=singletons,
            collections=collections,
            deferred_scopes=deferred_scopes,
            review_notes=review_notes,
            reviewed_by=reviewed_by,
            reviewed_at=reviewed_at,
        )

    @classmethod
    def from_path(cls, path: Path) -> ArmoryMappingContract:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Armory mapping file must contain a JSON object")
        return cls.from_dict(payload)

    def validate_against_review_packet(self, packet: Mapping[str, Any]) -> dict[str, Any]:
        errors: list[str] = []
        if packet.get("review_kind") != "armory_mapping_review":
            errors.append("review_kind mismatch")
        if packet.get("schema_version") != self.review_packet_schema_version:
            errors.append("review packet schema version mismatch")
        summary = packet.get("summary")
        if not isinstance(summary, Mapping):
            errors.append("review packet has no summary")
        else:
            if summary.get("contains_source_scalar_values") is not False:
                errors.append("review packet must not contain source scalar values")
            if summary.get("ready_for_manual_mapping_review") is not True:
                errors.append("review packet is not ready for manual mapping review")

        raw_endpoints = packet.get("endpoints")
        endpoint = None
        if isinstance(raw_endpoints, list):
            endpoint = next(
                (
                    value
                    for value in raw_endpoints
                    if isinstance(value, Mapping)
                    and value.get("endpoint_kind") == self.endpoint_kind
                ),
                None,
            )
        if not isinstance(endpoint, Mapping):
            errors.append(f"review packet has no endpoint {self.endpoint_kind}")
            endpoint = {}
        if endpoint.get("schema_fingerprint") != self.schema_fingerprint:
            errors.append("schema fingerprint mismatch")
        if endpoint.get("payload_hash") != self.reviewed_payload_hash:
            errors.append("reviewed payload hash mismatch")

        raw_shapes = endpoint.get("field_shapes")
        shape_by_path = {
            str(value.get("path")): value
            for value in raw_shapes
            if isinstance(raw_shapes, list)
            and isinstance(value, Mapping)
            and isinstance(value.get("path"), str)
        }

        field_count = 0

        def validate_field(name: str, contract: ArmoryFieldContract) -> None:
            nonlocal field_count
            field_count += 1
            shape = shape_by_path.get(contract.review_path)
            if not isinstance(shape, Mapping):
                errors.append(f"{name}: review path not found: {contract.review_path}")
                return
            type_counts = shape.get("type_counts")
            observed_types = set(type_counts) if isinstance(type_counts, Mapping) else set()
            if observed_types != set(contract.types):
                errors.append(
                    f"{name}: type mismatch mapping={sorted(contract.types)} "
                    f"review={sorted(observed_types)}"
                )
            if shape.get("nullable") is not contract.nullable:
                errors.append(f"{name}: nullable mismatch")

        for name, contract in self.singletons.items():
            validate_field(f"singletons.{name}", contract)
        for collection_name, collection in self.collections.items():
            collection_shape = shape_by_path.get(collection.path)
            if not isinstance(collection_shape, Mapping):
                errors.append(f"collections.{collection_name}: path not found: {collection.path}")
            elif collection_shape.get("occurrence_count") != collection.observed_occurrences:
                errors.append(
                    f"collections.{collection_name}: occurrence mismatch "
                    f"mapping={collection.observed_occurrences} "
                    f"review={collection_shape.get('occurrence_count')}"
                )
            for field_name, contract in collection.fields.items():
                validate_field(f"collections.{collection_name}.fields.{field_name}", contract)

        if errors:
            raise ValueError("Armory mapping review validation failed: " + "; ".join(errors))
        return {
            "mapping_id": self.mapping_id,
            "mapping_version": self.mapping_version,
            "status": self.status,
            "endpoint_kind": self.endpoint_kind,
            "schema_fingerprint": self.schema_fingerprint,
            "reviewed_payload_hash": self.reviewed_payload_hash,
            "singleton_count": len(self.singletons),
            "collection_count": len(self.collections),
            "field_count": field_count,
            "review_packet_schema_version": self.review_packet_schema_version,
            "production_ready": self.production_ready,
        }
