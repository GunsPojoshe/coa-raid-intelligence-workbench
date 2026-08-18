from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any

_IDENTIFIER_CHARS = r"A-Za-z0-9_$"
_DIRECT_TRANSPORT_MARKERS = {"fetch", "XMLHttpRequest"}
_REQUEST_SHAPE_MARKERS = {
    "body",
    "data",
    "headers",
    "method",
    "params",
    "query",
    "searchParams",
    "url",
    "JSON.stringify",
    "Content-Type",
}


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class StructuralIndex:
    excluded_spans: tuple[tuple[int, int], ...]


def scan_excluded_spans(text: str) -> StructuralIndex:
    excluded: list[tuple[int, int]] = []
    mode = "code"
    quote = ""
    start = -1
    index = 0
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if mode == "line_comment":
            if char in "\r\n":
                excluded.append((start, index))
                mode = "code"
        elif mode == "block_comment":
            if char == "*" and next_char == "/":
                excluded.append((start, index + 2))
                mode = "code"
                index += 1
        elif mode == "string":
            if char == "\\":
                index += 1
            elif char == quote:
                excluded.append((start, index + 1))
                mode = "code"
        elif char == "/" and next_char == "/":
            mode = "line_comment"
            start = index
            index += 1
        elif char == "/" and next_char == "*":
            mode = "block_comment"
            start = index
            index += 1
        elif char in "'\"`":
            mode = "string"
            quote = char
            start = index
        index += 1
    if mode != "code" and start >= 0:
        excluded.append((start, len(text)))
    return StructuralIndex(excluded_spans=tuple(excluded))


def _in_excluded(position: int, index: StructuralIndex) -> bool:
    return any(start <= position < end for start, end in index.excluded_spans)


def exact_symbol_positions(
    text: str,
    symbol: str,
    maximum: int,
    structural_index: StructuralIndex,
) -> tuple[list[int], bool]:
    if not symbol or maximum < 1:
        raise ValueError("symbol and positive maximum are required")
    pattern = re.compile(
        rf"(?<![{_IDENTIFIER_CHARS}]){re.escape(symbol)}(?![{_IDENTIFIER_CHARS}])"
    )
    positions: list[int] = []
    truncated = False
    for match in pattern.finditer(text):
        if _in_excluded(match.start(), structural_index):
            continue
        if len(positions) == maximum:
            truncated = True
            break
        positions.append(match.start())
    return positions, truncated


def _markers(value: str, markers: set[str]) -> list[str]:
    observed: list[str] = []
    for marker in sorted(markers):
        if marker in {"JSON.stringify", "Content-Type", "XMLHttpRequest"}:
            present = marker in value
        else:
            present = bool(re.search(rf"\b{re.escape(marker)}\b", value))
        if present:
            observed.append(marker)
    return observed


def _next_code_character(text: str, start: int) -> str:
    index = start
    while index < len(text) and text[index].isspace():
        index += 1
    return text[index : index + 1]


def _previous_code_character(text: str, start: int) -> str:
    index = start - 1
    while index >= 0 and text[index].isspace():
        index -= 1
    return text[index : index + 1]


def _reference_kind(
    text: str,
    start: int,
    end: int,
    definition_spans: tuple[tuple[int, int], ...],
) -> str:
    if any(
        definition_start <= start < definition_end
        for definition_start, definition_end in definition_spans
    ):
        return "definition_candidate"
    next_character = _next_code_character(text, end)
    previous_character = _previous_code_character(text, start)
    if next_character == "(":
        return "invocation"
    if next_character == "=":
        return "assignment_target"
    if next_character == ":":
        return "object_key"
    if previous_character == "." or next_character == ".":
        return "member_reference"
    return "identifier_reference"


def reference_candidates(
    text: str,
    callee: str,
    *,
    definition_spans: tuple[tuple[int, int], ...],
    route_template: str,
    max_symbol_occurrences: int = 500,
    max_reference_candidates: int = 500,
    private_context_chars: int = 1024,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not 1 <= max_symbol_occurrences <= 5000:
        raise ValueError("max_symbol_occurrences must be between 1 and 5000")
    if not 1 <= max_reference_candidates <= 2000:
        raise ValueError("max_reference_candidates must be between 1 and 2000")
    if not 128 <= private_context_chars <= 8192:
        raise ValueError("private_context_chars must be between 128 and 8192")
    if not callee:
        raise ValueError("callee is required")

    structural_index = scan_excluded_spans(text)
    terminal = callee.rsplit(".", 1)[-1]
    full_positions, full_truncated = exact_symbol_positions(
        text,
        callee,
        max_symbol_occurrences,
        structural_index,
    )
    if terminal == callee:
        terminal_positions = list(full_positions)
        terminal_truncated = full_truncated
    else:
        terminal_positions, terminal_truncated = exact_symbol_positions(
            text,
            terminal,
            max_symbol_occurrences,
            structural_index,
        )

    full_spans = tuple((position, position + len(callee)) for position in full_positions)
    terminal_only_positions = [
        position
        for position in terminal_positions
        if not any(start <= position < end for start, end in full_spans)
    ]
    selected: list[tuple[str, str, int]] = [
        ("full_chain", callee, position) for position in full_positions
    ]
    selected.extend(
        ("terminal_symbol", terminal, position) for position in terminal_only_positions
    )
    selected.sort(key=lambda item: (item[2], item[0]))
    reference_scan_truncated = len(selected) > max_reference_candidates
    selected = selected[:max_reference_candidates]

    rows: list[dict[str, Any]] = []
    for scope, symbol, position in selected:
        end = position + len(symbol)
        context_start = max(0, position - private_context_chars)
        context_end = min(len(text), end + private_context_chars)
        context = text[context_start:context_end]
        direct_transport_markers = _markers(context, _DIRECT_TRANSPORT_MARKERS)
        request_shape_markers = _markers(context, _REQUEST_SHAPE_MARKERS)
        kind = _reference_kind(text, position, end, definition_spans)
        rows.append(
            {
                "symbol_scope": scope,
                "raw_symbol": symbol,
                "start": position,
                "end": end,
                "reference_kind": kind,
                "context": context,
                "context_start": context_start,
                "context_end": context_end,
                "context_sha256": _sha256(context),
                "context_character_count": len(context),
                "definition_candidate_overlap": kind == "definition_candidate",
                "route_template_observed": route_template in context.replace("\\/", "/"),
                "direct_transport_markers": direct_transport_markers,
                "request_shape_markers": request_shape_markers,
            }
        )

    evidence = {
        "full_chain_occurrence_count_observed": len(full_positions),
        "full_chain_occurrence_scan_truncated": full_truncated,
        "terminal_symbol_occurrence_count_observed": len(terminal_positions),
        "terminal_symbol_occurrence_scan_truncated": terminal_truncated,
        "terminal_symbol_only_occurrence_count": len(terminal_only_positions),
        "unique_reference_candidate_count": len(rows),
        "reference_candidate_scan_truncated": reference_scan_truncated,
        "reference_kinds": sorted({str(row["reference_kind"]) for row in rows}),
        "symbol_scopes": sorted({str(row["symbol_scope"]) for row in rows}),
        "definition_overlap_count": sum(
            bool(row["definition_candidate_overlap"]) for row in rows
        ),
        "route_context_reference_count": sum(
            bool(row["route_template_observed"]) for row in rows
        ),
        "direct_transport_marker_classes": sorted(
            {
                marker
                for row in rows
                for marker in row["direct_transport_markers"]
            }
        ),
        "request_shape_marker_classes": sorted(
            {marker for row in rows for marker in row["request_shape_markers"]}
        ),
    }
    return rows, evidence


__all__ = ["reference_candidates"]
