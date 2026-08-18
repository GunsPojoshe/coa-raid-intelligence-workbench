from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .canonical import find_matches, pointer_get

_ALLOWED_JSON_TYPES = {"array", "boolean", "integer", "null", "number", "object", "string"}
_ALLOWED_STATUSES = {"candidate", "verified"}
_MAPPING_SCHEMA_VERSION = 1
_MISSING = object()


def _required_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"report mapping field {name} must be a non-empty string")
    return value


def _required_integer(value: object, name: str, *, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise ValueError(
            f"report mapping field {name} must be an integer greater than or equal to {minimum}"
        )
    return value


def _required_string_list(value: object, name: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ValueError(f"report mapping field {name} must be an array of non-empty strings")
    return tuple(value)


def _sha256(value: object, name: str) -> str:
    prepared = _required_string(value, name).casefold()
    if len(prepared) != 64 or any(char not in "0123456789abcdef" for char in prepared):
        raise ValueError(f"report mapping field {name} must be a SHA-256 hex digest")
    return prepared


def _json_type(value: Any) -> str:
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
    raise TypeError(f"unsupported JSON value type: {type(value).__name__}")


@dataclass(frozen=True, slots=True)
class ReportDiscoveryFieldContract:
    selector: str
    review_path: str
    types: tuple[str, ...]
    nullable: bool
    required: bool
    note: str | None = None

    @classmethod
    def from_dict(
        cls,
        payload: Mapping[str, Any],
        *,
        name: str,
    ) -> ReportDiscoveryFieldContract:
        selector = _required_string(payload.get("selector"), f"{name}.selector")
        review_path = _required_string(payload.get("review_path"), f"{name}.review_path")
        if not selector.startswith("/") or not review_path.startswith("/"):
            raise ValueError(f"report mapping field {name} selectors must be absolute paths")

        raw_types = payload.get("types")
        if not isinstance(raw_types, list) or not raw_types:
            raise ValueError(f"report mapping field {name}.types must be a non-empty array")
        types = tuple(sorted({_required_string(value, f"{name}.types[]") for value in raw_types}))
        invalid = set(types) - _ALLOWED_JSON_TYPES
        if invalid:
            raise ValueError(f"report mapping field {name} has invalid JSON types: {sorted(invalid)}")

        nullable = payload.get("nullable", False)
        required = payload.get("required", True)
        if not isinstance(nullable, bool) or not isinstance(required, bool):
            raise ValueError(f"report mapping field {name} nullable/required flags must be boolean")
        if nullable != ("null" in types):
            raise ValueError(f"report mapping field {name} nullable flag does not match its types")

        note = payload.get("note")
        if note is not None and (not isinstance(note, str) or not note):
            raise ValueError(f"report mapping field {name}.note must be a non-empty string")
        return cls(selector, review_path, types, nullable, required, note)


@dataclass(frozen=True, slots=True)
class ReportDiscoveryCollectionContract:
    path: str
    observed_occurrences: int
    required_keys: tuple[str, ...]
    fields: dict[str, ReportDiscoveryFieldContract]

    @classmethod
    def from_dict(
        cls,
        payload: Mapping[str, Any],
    ) -> ReportDiscoveryCollectionContract:
        path = _required_string(payload.get("path"), "collection.path")
        if not path.startswith("/"):
            raise ValueError("report mapping collection.path must be absolute")
        occurrences = _required_integer(
            payload.get("observed_occurrences"),
            "collection.observed_occurrences",
            minimum=1,
        )
        required_keys = _required_string_list(payload.get("required_keys"), "collection.required_keys")
        if len(set(required_keys)) != len(required_keys):
            raise ValueError("report mapping collection.required_keys must not contain duplicates")

        raw_fields = payload.get("fields")
        if not isinstance(raw_fields, dict) or not raw_fields:
            raise ValueError("report mapping collection.fields must be a non-empty object")
        fields = {
            _required_string(name, "collection.fields key"): ReportDiscoveryFieldContract.from_dict(
                spec,
                name=f"collection.fields.{name}",
            )
            for name, spec in raw_fields.items()
            if isinstance(spec, Mapping)
        }
        if len(fields) != len(raw_fields):
            raise ValueError("report mapping collection contains a non-object field contract")
        return cls(path, occurrences, required_keys, fields)


@dataclass(frozen=True, slots=True)
class ReportDiscoveryMappingContract:
    mapping_id: str
    source_code: str
    mapping_version: str
    status: str
    route_template: str
    schema_fingerprint: str
    reviewed_payload_hash: str
    review_summary_schema_version: int
    provenance_type: str
    required_top_level: tuple[str, ...]
    collection: ReportDiscoveryCollectionContract
    deferred_scopes: tuple[str, ...]
    review_notes: tuple[str, ...]
    reviewed_by: str | None = None
    reviewed_at: str | None = None

    @property
    def production_ready(self) -> bool:
        return self.status == "verified"

    def require_verified(self) -> None:
        if not self.production_ready:
            raise ValueError(f"report discovery mapping {self.mapping_id!r} is not verified")

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ReportDiscoveryMappingContract:
        if payload.get("mapping_schema_version") != _MAPPING_SCHEMA_VERSION:
            raise ValueError("unsupported report discovery mapping schema version")

        status = _required_string(payload.get("status"), "status")
        if status not in _ALLOWED_STATUSES:
            raise ValueError(f"unsupported report discovery mapping status: {status}")
        route_template = _required_string(payload.get("route_template"), "route_template")
        if route_template != "/api/reports/public":
            raise ValueError("report discovery route_template must be /api/reports/public")

        raw_collection = payload.get("collection")
        if not isinstance(raw_collection, Mapping):
            raise ValueError("report mapping collection must be an object")

        deferred = _required_string_list(payload.get("deferred_scopes", []), "deferred_scopes")
        if any(not scope.startswith("/") for scope in deferred):
            raise ValueError("report mapping deferred scopes must be absolute paths")
        notes = _required_string_list(payload.get("review_notes", []), "review_notes")

        reviewed_by = payload.get("reviewed_by")
        reviewed_at = payload.get("reviewed_at")
        if status == "verified":
            reviewed_by = _required_string(reviewed_by, "reviewed_by")
            reviewed_at = _required_string(reviewed_at, "reviewed_at")
        elif reviewed_by is not None or reviewed_at is not None:
            raise ValueError("candidate report mappings must not contain verification metadata")

        return cls(
            mapping_id=_required_string(payload.get("mapping_id"), "mapping_id"),
            source_code=_required_string(payload.get("source_code"), "source_code"),
            mapping_version=_required_string(payload.get("mapping_version"), "mapping_version"),
            status=status,
            route_template=route_template,
            schema_fingerprint=_sha256(payload.get("schema_fingerprint"), "schema_fingerprint"),
            reviewed_payload_hash=_sha256(payload.get("reviewed_payload_hash"), "reviewed_payload_hash"),
            review_summary_schema_version=_required_integer(
                payload.get("review_summary_schema_version"),
                "review_summary_schema_version",
                minimum=1,
            ),
            provenance_type=_required_string(payload.get("provenance_type"), "provenance_type"),
            required_top_level=_required_string_list(
                payload.get("required_top_level"),
                "required_top_level",
            ),
            collection=ReportDiscoveryCollectionContract.from_dict(raw_collection),
            deferred_scopes=deferred,
            review_notes=notes,
            reviewed_by=reviewed_by,
            reviewed_at=reviewed_at,
        )

    @classmethod
    def from_path(cls, path: Path) -> ReportDiscoveryMappingContract:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("report discovery mapping file must contain a JSON object")
        return cls.from_dict(payload)

    def validate_against_summary(self, summary: Mapping[str, Any]) -> dict[str, Any]:
        errors: list[str] = []
        if summary.get("summary_kind") != "report_discovery_mapping_summary":
            errors.append("summary_kind mismatch")
        if summary.get("schema_version") != self.review_summary_schema_version:
            errors.append("summary schema version mismatch")

        payload = summary.get("payload")
        decision = summary.get("candidate_decision")
        item_shape = summary.get("report_item_shape")
        totals = summary.get("summary")
        if not isinstance(payload, Mapping):
            errors.append("summary has no payload")
            payload = {}
        if not isinstance(decision, Mapping):
            errors.append("summary has no candidate_decision")
            decision = {}
        if not isinstance(item_shape, Mapping):
            errors.append("summary has no report_item_shape")
            item_shape = {}
        if not isinstance(totals, Mapping):
            errors.append("summary has no summary totals")
            totals = {}

        if payload.get("payload_hash") != self.reviewed_payload_hash:
            errors.append("reviewed payload hash mismatch")
        if payload.get("schema_fingerprint") != self.schema_fingerprint:
            errors.append("schema fingerprint mismatch")
        if not set(self.required_top_level).issubset(set(payload.get("top_level_keys", []))):
            errors.append("required top-level keys are not present")
        if totals.get("contains_source_scalar_values") is not False:
            errors.append("summary privacy gate is not satisfied")
        if decision.get("unique_report_like_collection") is not True:
            errors.append("summary does not contain one unique report-like collection")
        if decision.get("report_item_selector") != self.collection.path:
            errors.append("report collection selector mismatch")
        if decision.get("can_promote") is not False:
            errors.append("candidate summary unexpectedly allows promotion")
        if item_shape.get("path") != self.collection.path:
            errors.append("report item shape path mismatch")
        if item_shape.get("occurrence_count") != self.collection.observed_occurrences:
            errors.append("report item occurrence count mismatch")
        if set(item_shape.get("required_keys", [])) != set(self.collection.required_keys):
            errors.append("report required keys mismatch")

        raw_fields = item_shape.get("fields")
        fields_by_path = {
            str(item.get("path")): item
            for item in raw_fields
            if isinstance(raw_fields, list)
            and isinstance(item, Mapping)
            and isinstance(item.get("path"), str)
        }
        for name, field in self.collection.fields.items():
            shape = fields_by_path.get(field.review_path)
            if not isinstance(shape, Mapping):
                errors.append(f"collection.fields.{name}: review path not found")
                continue
            if set(shape.get("types", [])) != set(field.types):
                errors.append(f"collection.fields.{name}: type mismatch")
            if shape.get("nullable") is not field.nullable:
                errors.append(f"collection.fields.{name}: nullable mismatch")
            if field.required and shape.get("observed_on_all_items") is not True:
                errors.append(f"collection.fields.{name}: required field not observed on all items")

        if errors:
            raise ValueError("report mapping summary validation failed: " + "; ".join(errors))
        return {
            "mapping_id": self.mapping_id,
            "mapping_version": self.mapping_version,
            "status": self.status,
            "schema_fingerprint": self.schema_fingerprint,
            "reviewed_payload_hash": self.reviewed_payload_hash,
            "collection_path": self.collection.path,
            "observed_occurrences": self.collection.observed_occurrences,
            "field_count": len(self.collection.fields),
            "deferred_scope_count": len(self.deferred_scopes),
            "production_ready": self.production_ready,
        }

    def validate_against_payload(
        self,
        payload: Any,
        *,
        payload_hash: str,
        schema_fingerprint: str,
        route: str | None,
    ) -> dict[str, Any]:
        errors: list[str] = []
        if payload_hash != self.reviewed_payload_hash:
            errors.append("reviewed payload hash mismatch")
        if schema_fingerprint != self.schema_fingerprint:
            errors.append("schema fingerprint mismatch")
        if route != self.route_template:
            errors.append(f"route mismatch: expected={self.route_template} actual={route}")
        if not isinstance(payload, dict):
            errors.append("payload root is not an object")
        elif not set(self.required_top_level).issubset(payload):
            errors.append("payload is missing required top-level keys")

        matches = find_matches(payload, self.collection.path)
        if len(matches) != self.collection.observed_occurrences:
            errors.append(
                "report occurrence mismatch: "
                f"mapping={self.collection.observed_occurrences} payload={len(matches)}"
            )

        extracted_value_count = 0
        nullable_value_count = 0
        for match in matches:
            if not isinstance(match.value, dict):
                errors.append(f"report item is not an object at {match.path}")
                continue
            missing_keys = sorted(set(self.collection.required_keys) - set(match.value))
            if missing_keys:
                errors.append(f"report item is missing required keys at {match.path}")
            for name, field in self.collection.fields.items():
                value = pointer_get(match.value, field.selector, _MISSING)
                if value is _MISSING:
                    if field.required:
                        errors.append(f"collection.fields.{name}: required selector missing at {match.path}")
                    continue
                value_type = _json_type(value)
                if value_type not in field.types:
                    errors.append(
                        f"collection.fields.{name}: extracted type {value_type} is not allowed at {match.path}"
                    )
                if value is None:
                    nullable_value_count += 1
                    if not field.nullable:
                        errors.append(f"collection.fields.{name}: null from non-nullable field at {match.path}")
                extracted_value_count += 1

        if errors:
            raise ValueError("report raw payload validation failed: " + "; ".join(errors))
        return {
            "mapping_id": self.mapping_id,
            "reviewed_payload_hash": self.reviewed_payload_hash,
            "schema_fingerprint": self.schema_fingerprint,
            "route_template": self.route_template,
            "route_matched": True,
            "collection_path": self.collection.path,
            "report_item_count": len(matches),
            "field_contract_count": len(self.collection.fields),
            "extracted_value_count": extracted_value_count,
            "nullable_value_count": nullable_value_count,
            "raw_payload_validated": True,
            "production_ready": self.production_ready,
        }
