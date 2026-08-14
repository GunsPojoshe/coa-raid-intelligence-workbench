from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Mapping

from coa_workbench.collector.json_structure import (
    SCHEMA_PATH_NORMALIZATION,
    json_structure_fingerprint,
)
from coa_workbench.normalizer.canonical import (
    CanonicalBatch,
    NormalizationMapping,
    find_matches,
    normalize_payload,
)

COMPATIBLE_NORMALIZATION_VERSION = "verified-field-contract-compatible-v1"


def _object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def _array(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    return value


def _contract_type(value: Any) -> str:
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
    return type(value).__name__


@dataclass(frozen=True, slots=True)
class CompatibleNormalizationResult:
    batch: CanonicalBatch
    source_structure_fingerprint: str
    verified_field_contract_count: int
    ignored_additive_fields_allowed: bool = True

    def public_summary(self) -> dict[str, Any]:
        return {
            "compatibility_version": COMPATIBLE_NORMALIZATION_VERSION,
            "schema_path_normalization": SCHEMA_PATH_NORMALIZATION,
            "mapping_id": self.batch.mapping_id,
            "mapping_version": self.batch.mapping_version,
            "source_structure_fingerprint": self.source_structure_fingerprint,
            "verified_field_contract_count": self.verified_field_contract_count,
            "counts": self.batch.counts(),
            "ignored_additive_fields_allowed": self.ignored_additive_fields_allowed,
            "contains_source_scalar_values": False,
            "mechanic_semantics_verified": False,
        }


def _validate_field_contracts(
    payload: Any,
    mapping_payload: Mapping[str, Any],
) -> int:
    contracts = _array(mapping_payload.get("field_contracts"), "field_contracts")
    for index, raw_contract in enumerate(contracts):
        contract = _object(raw_contract, f"field_contracts[{index}]")
        if contract.get("semantic_status") != "verified_parser_field":
            raise ValueError(
                f"field_contracts[{index}] is not a verified parser field"
            )
        review_path = str(contract.get("review_path") or "")
        review_scope = str(contract.get("review_scope") or "")
        if not review_path or not review_scope:
            raise ValueError(
                f"field_contracts[{index}] must define review_path and review_scope"
            )
        declared_types = {str(value) for value in _array(contract.get("types"), "types")}
        if not declared_types:
            raise ValueError(f"field_contracts[{index}] has no declared JSON types")

        field_matches = find_matches(payload, review_path)
        scope_matches = find_matches(payload, review_scope)
        required = contract.get("required") is True
        nullable = contract.get("nullable") is True

        if required and len(field_matches) != len(scope_matches):
            raise ValueError(
                f"required parser field occurrence mismatch at {review_path}: "
                f"field={len(field_matches)} scope={len(scope_matches)}"
            )
        observed_types = {_contract_type(match.value) for match in field_matches}
        unknown_types = sorted(observed_types - declared_types)
        if unknown_types:
            raise ValueError(
                f"parser field type mismatch at {review_path}: "
                f"observed={unknown_types} declared={sorted(declared_types)}"
            )
        if not nullable and "null" in observed_types:
            raise ValueError(f"non-null parser field observed null at {review_path}")
    return len(contracts)


def normalize_verified_compatible_payload(
    payload: Any,
    mapping_payload: Mapping[str, Any],
) -> CompatibleNormalizationResult:
    """Normalize an additive-compatible payload using only manually verified field contracts.

    This deliberately does not treat a whole-payload schema fingerprint mismatch as a parser
    failure when all promoted selectors still satisfy their reviewed type/nullability contracts.
    Removed or changed mapped fields fail closed. Additive upstream fields remain ignored.
    """
    if mapping_payload.get("status") != "verified":
        raise ValueError("compatible normalization requires a verified mapping")
    if mapping_payload.get("mechanic_semantics_verified") is not False:
        raise ValueError("compatible normalization does not promote mechanic semantics")

    verified_count = _validate_field_contracts(payload, mapping_payload)
    runtime_fingerprint = json_structure_fingerprint(payload)
    mapping = NormalizationMapping.from_dict(mapping_payload)
    runtime_mapping = replace(mapping, schema_fingerprint=runtime_fingerprint)
    batch = normalize_payload(
        payload,
        runtime_mapping,
        schema_fingerprint=runtime_fingerprint,
    )
    return CompatibleNormalizationResult(
        batch=batch,
        source_structure_fingerprint=runtime_fingerprint,
        verified_field_contract_count=verified_count,
    )


__all__ = [
    "COMPATIBLE_NORMALIZATION_VERSION",
    "CompatibleNormalizationResult",
    "normalize_verified_compatible_payload",
]
