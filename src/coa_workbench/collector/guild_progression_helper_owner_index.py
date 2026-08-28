from __future__ import annotations

import hashlib
import re
from typing import Any, Mapping, Sequence

_IDENTIFIER = r"[A-Za-z_$][A-Za-z0-9_$]*"
_CHAIN = rf"{_IDENTIFIER}(?:\.{_IDENTIFIER})*"
_MEMBER_RECEIVER = re.compile(rf"(?P<owner>{_CHAIN})\s*\.\s*$")
_DEFINITION_CONTAINER_PATTERNS = (
    (
        "definition_class_container",
        re.compile(
            rf"\bclass\s+(?P<owner>{_IDENTIFIER})"
            rf"(?:\s+extends\s+{_CHAIN})?\s*\{{[^{{}}]*$"
        ),
    ),
    (
        "definition_assignment_container",
        re.compile(rf"(?P<owner>{_CHAIN})\s*=\s*\{{[^{{}}]*$"),
    ),
    (
        "definition_property_container",
        re.compile(rf"(?P<owner>{_IDENTIFIER})\s*:\s*\{{[^{{}}]*$"),
    ),
)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _owner_row(
    *,
    reference: Mapping[str, Any],
    owner: str,
    owner_start: int,
    owner_end: int,
    candidate_source: str,
) -> dict[str, Any]:
    if owner_end - owner_start != len(owner):
        raise ValueError("owner span length mismatch")
    depth = owner.count(".") + 1
    return {
        "reference_index": reference["reference_index"],
        "symbol_scope": reference["symbol_scope"],
        "reference_kind": reference["reference_kind"],
        "definition_candidate_overlap": reference["definition_candidate_overlap"],
        "candidate_source": candidate_source,
        "raw_owner_chain": owner,
        "owner_start": owner_start,
        "owner_end": owner_end,
        "owner_chain_sha256": _sha256(owner),
        "owner_chain_character_count": len(owner),
        "owner_chain_depth": depth,
        "source_reference_context_sha256": reference["context_sha256"],
    }


def _member_receiver_candidate(
    text: str,
    callee: str,
    reference: Mapping[str, Any],
    max_owner_prefix_chars: int,
) -> dict[str, Any] | None:
    terminal = callee.rsplit(".", 1)[-1]
    symbol = reference.get("raw_symbol")
    start = reference.get("start")
    end = reference.get("end")
    if not isinstance(symbol, str) or not isinstance(start, int) or not isinstance(end, int):
        raise ValueError("private reference symbol span is malformed")
    terminal_start = end - len(terminal) if reference.get("symbol_scope") == "full_chain" else start
    if terminal_start < 0 or terminal_start > len(text):
        raise ValueError("private reference terminal position is invalid")
    prefix_start = max(0, terminal_start - max_owner_prefix_chars)
    prefix = text[prefix_start:terminal_start]
    match = _MEMBER_RECEIVER.search(prefix)
    if match is None:
        return None
    owner = match.group("owner")
    owner_start = prefix_start + match.start("owner")
    owner_end = prefix_start + match.end("owner")
    source = (
        "full_chain_member_receiver"
        if reference.get("symbol_scope") == "full_chain"
        else "terminal_member_receiver"
    )
    return _owner_row(
        reference=reference,
        owner=owner,
        owner_start=owner_start,
        owner_end=owner_end,
        candidate_source=source,
    )


def _definition_container_candidates(
    text: str,
    reference: Mapping[str, Any],
    max_definition_container_chars: int,
) -> list[dict[str, Any]]:
    if reference.get("definition_candidate_overlap") is not True:
        return []
    start = reference.get("start")
    if not isinstance(start, int) or not 0 <= start <= len(text):
        raise ValueError("definition reference start is invalid")
    prefix_start = max(0, start - max_definition_container_chars)
    prefix = text[prefix_start:start]
    rows: list[dict[str, Any]] = []
    for source, pattern in _DEFINITION_CONTAINER_PATTERNS:
        match = pattern.search(prefix)
        if match is None:
            continue
        owner = match.group("owner")
        owner_start = prefix_start + match.start("owner")
        owner_end = prefix_start + match.end("owner")
        rows.append(
            _owner_row(
                reference=reference,
                owner=owner,
                owner_start=owner_start,
                owner_end=owner_end,
                candidate_source=source,
            )
        )
    return rows


def owner_candidates(
    text: str,
    callee: str,
    references: Sequence[Mapping[str, Any]],
    *,
    max_owner_prefix_chars: int = 512,
    max_definition_container_chars: int = 2048,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not 64 <= max_owner_prefix_chars <= 4096:
        raise ValueError("max_owner_prefix_chars must be between 64 and 4096")
    if not 128 <= max_definition_container_chars <= 8192:
        raise ValueError("max_definition_container_chars must be between 128 and 8192")
    if not callee or not re.fullmatch(_CHAIN, callee):
        raise ValueError("callee is missing or malformed")

    rows: list[dict[str, Any]] = []
    seen: set[tuple[int, str, str]] = set()
    for reference in references:
        member = _member_receiver_candidate(
            text,
            callee,
            reference,
            max_owner_prefix_chars,
        )
        candidates = ([] if member is None else [member]) + _definition_container_candidates(
            text,
            reference,
            max_definition_container_chars,
        )
        for row in candidates:
            key = (
                int(row["reference_index"]),
                str(row["candidate_source"]),
                str(row["owner_chain_sha256"]),
            )
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)

    rows.sort(
        key=lambda row: (
            int(row["reference_index"]),
            str(row["candidate_source"]),
            int(row["owner_start"]),
        )
    )
    for index, row in enumerate(rows, 1):
        row["candidate_index"] = index

    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row["owner_chain_sha256"]), []).append(row)

    groups: list[dict[str, Any]] = []
    for group_index, owner_hash in enumerate(sorted(grouped), 1):
        members = grouped[owner_hash]
        raw_values = {str(row["raw_owner_chain"]) for row in members}
        if len(raw_values) != 1:
            raise ValueError("owner hash collision or inconsistent owner candidate")
        owner = next(iter(raw_values))
        definition_count = sum(
            row["definition_candidate_overlap"] is True for row in members
        )
        non_definition_count = len(members) - definition_count
        groups.append(
            {
                "owner_group_index": group_index,
                "raw_owner_chain": owner,
                "owner_chain_sha256": owner_hash,
                "owner_chain_character_count": len(owner),
                "owner_chain_depth": owner.count(".") + 1,
                "occurrence_count": len(members),
                "reference_indexes": sorted(
                    {int(row["reference_index"]) for row in members}
                ),
                "candidate_sources": sorted(
                    {str(row["candidate_source"]) for row in members}
                ),
                "definition_candidate_count": definition_count,
                "non_definition_candidate_count": non_definition_count,
                "cross_definition_reference_binding_observed": (
                    definition_count > 0 and non_definition_count > 0
                ),
            }
        )

    evidence = {
        "reference_count": len(references),
        "owner_candidate_occurrence_count": len(rows),
        "unique_owner_group_count": len(groups),
        "definition_owner_candidate_occurrence_count": sum(
            row["definition_candidate_overlap"] is True for row in rows
        ),
        "member_receiver_candidate_occurrence_count": sum(
            str(row["candidate_source"]).endswith("member_receiver") for row in rows
        ),
        "definition_container_candidate_occurrence_count": sum(
            str(row["candidate_source"]).startswith("definition_")
            and str(row["candidate_source"]).endswith("_container")
            for row in rows
        ),
        "references_without_owner_candidate_count": len(references)
        - len({int(row["reference_index"]) for row in rows}),
        "owner_candidate_source_classes": sorted(
            {str(row["candidate_source"]) for row in rows}
        ),
        "owner_chain_depths_observed": sorted(
            {int(row["owner_chain_depth"]) for row in rows}
        ),
        "cross_definition_reference_owner_group_count": sum(
            group["cross_definition_reference_binding_observed"] is True
            for group in groups
        ),
        "owner_evidence_observed": bool(rows),
    }
    return rows, {"groups": groups, "evidence": evidence}


__all__ = ["owner_candidates"]
