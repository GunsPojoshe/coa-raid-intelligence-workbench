from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any

_IDENTIFIER = r"[A-Za-z_$][A-Za-z0-9_$]*"
_IDENTIFIER_CHARS = r"A-Za-z0-9_$"
_MARKERS = {
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
    "fetch",
    "XMLHttpRequest",
}


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class StructuralIndex:
    pairs: dict[int, int]
    excluded_spans: tuple[tuple[int, int], ...]


def scan_pairs(text: str) -> StructuralIndex:
    pairs: dict[int, int] = {}
    excluded: list[tuple[int, int]] = []
    stacks: dict[str, list[int]] = {"(": [], "[": [], "{": []}
    closing = {")": "(", "]": "[", "}": "{"}
    mode = "code"
    quote = ""
    excluded_start = -1
    index = 0
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if mode == "line_comment":
            if char in "\r\n":
                excluded.append((excluded_start, index))
                mode = "code"
        elif mode == "block_comment":
            if char == "*" and next_char == "/":
                excluded.append((excluded_start, index + 2))
                mode = "code"
                index += 1
        elif mode == "string":
            if char == "\\":
                index += 1
            elif char == quote:
                excluded.append((excluded_start, index + 1))
                mode = "code"
        elif char == "/" and next_char == "/":
            mode = "line_comment"
            excluded_start = index
            index += 1
        elif char == "/" and next_char == "*":
            mode = "block_comment"
            excluded_start = index
            index += 1
        elif char in "'\"`":
            mode, quote = "string", char
            excluded_start = index
        elif char in stacks:
            stacks[char].append(index)
        elif char in closing and stacks[closing[char]]:
            pairs[stacks[closing[char]].pop()] = index
        index += 1
    if mode != "code" and excluded_start >= 0:
        excluded.append((excluded_start, len(text)))
    return StructuralIndex(pairs=pairs, excluded_spans=tuple(excluded))


def _in_excluded(position: int, index: StructuralIndex) -> bool:
    return any(start <= position < end for start, end in index.excluded_spans)


def exact_symbol_positions(
    text: str,
    symbol: str,
    maximum: int,
    structural_index: StructuralIndex | None = None,
) -> tuple[list[int], bool]:
    if not symbol or maximum < 1:
        raise ValueError("symbol and positive maximum are required")
    pattern = re.compile(
        rf"(?<![{_IDENTIFIER_CHARS}]){re.escape(symbol)}(?![{_IDENTIFIER_CHARS}])"
    )
    positions: list[int] = []
    truncated = False
    for match in pattern.finditer(text):
        if structural_index is not None and _in_excluded(match.start(), structural_index):
            continue
        if len(positions) == maximum:
            truncated = True
            break
        positions.append(match.start())
    return positions, truncated


def _first_body(
    text: str,
    index: StructuralIndex,
    start: int,
    limit: int,
) -> tuple[int, int] | None:
    stop = min(len(text), start + min(limit, 4096))
    opening = text.find("{", start, stop)
    while opening >= 0 and _in_excluded(opening, index):
        opening = text.find("{", opening + 1, stop)
    if opening < 0 or opening not in index.pairs:
        return None
    end = index.pairs[opening] + 1
    if end - start > limit:
        return None
    return start, end


def _expression_end(text: str, start: int, limit: int) -> int:
    stop = min(len(text), start + limit)
    semicolon = text.find(";", start, stop)
    newline = text.find("\n", start, stop)
    candidates = [item + 1 for item in (semicolon, newline) if item >= 0]
    return min(candidates) if candidates else stop


def _markers(value: str) -> list[str]:
    observed: list[str] = []
    for marker in sorted(_MARKERS):
        if marker in {"JSON.stringify", "Content-Type", "XMLHttpRequest"}:
            present = marker in value
        else:
            present = bool(re.search(rf"\b{re.escape(marker)}\b", value))
        if present:
            observed.append(marker)
    return observed


def _parameter_count(prefix: str) -> int | None:
    match = re.search(r"\(([^()]*)\)\s*(?:=>|\{)", prefix)
    if not match:
        match = re.search(rf"\b{_IDENTIFIER}\s*=>", prefix)
        return 1 if match else None
    body = match.group(1).strip()
    if not body:
        return 0
    return len([item for item in body.split(",") if item.strip()])


def _candidate(
    text: str,
    index: StructuralIndex,
    *,
    kind: str,
    start: int,
    prefix_end: int,
    max_span_chars: int,
    binding_scope: str,
    alias_target: str | None = None,
) -> dict[str, Any]:
    body = (
        None
        if kind == "alias_assignment"
        else _first_body(text, index, prefix_end, max_span_chars)
    )
    end = body[1] if body else _expression_end(text, start, max_span_chars)
    value = text[start:end]
    prefix = text[start:min(end, prefix_end + 256)]
    return {
        "kind": kind,
        "binding_scope": binding_scope,
        "start": start,
        "end": end,
        "span": value,
        "span_sha256": _sha256(value),
        "character_count": len(value),
        "prefix_sha256": _sha256(prefix),
        "parameter_count": _parameter_count(prefix),
        "async_candidate": bool(re.search(r"\basync\b", prefix)),
        "marker_classes": _markers(value),
        "alias_target": alias_target,
        "alias_target_sha256": _sha256(alias_target) if alias_target else None,
    }


def definition_candidates(
    text: str,
    callee: str,
    *,
    max_symbol_occurrences: int = 500,
    max_candidates: int = 50,
    max_span_chars: int = 131072,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not 1 <= max_candidates <= 200:
        raise ValueError("max_candidates must be between 1 and 200")
    if not 1024 <= max_span_chars <= 1048576:
        raise ValueError("max_span_chars must be between 1024 and 1048576")
    index = scan_pairs(text)
    terminal = callee.rsplit(".", 1)[-1]
    full_positions, full_positions_truncated = exact_symbol_positions(
        text,
        callee,
        max_symbol_occurrences,
        index,
    )
    if terminal == callee:
        terminal_positions = full_positions
        terminal_positions_truncated = full_positions_truncated
    else:
        terminal_positions, terminal_positions_truncated = exact_symbol_positions(
            text,
            terminal,
            max_symbol_occurrences,
            index,
        )

    escaped_full = re.escape(callee)
    escaped_terminal = re.escape(terminal)
    assignment_kind = (
        "function_assignment" if callee == terminal else "member_function_assignment"
    )
    patterns: list[tuple[str, str, re.Pattern[str]]] = [
        (
            "function_declaration",
            "terminal_symbol",
            re.compile(rf"\b(?:async\s+)?function\s+{escaped_terminal}\s*\("),
        ),
        (
            "variable_function_assignment",
            "terminal_symbol",
            re.compile(
                rf"\b(?:const|let|var)\s+{escaped_terminal}\s*=\s*"
                rf"(?:async\s*)?(?:function\b|\([^;{{}}]*\)\s*=>|{_IDENTIFIER}\s*=>)"
            ),
        ),
        (
            assignment_kind,
            "full_chain",
            re.compile(
                rf"(?<![{_IDENTIFIER_CHARS}]){escaped_full}\s*=\s*"
                rf"(?:async\s*)?(?:function\b|\([^;{{}}]*\)\s*=>|{_IDENTIFIER}\s*=>)"
            ),
        ),
        (
            "object_property_function",
            "terminal_symbol",
            re.compile(
                rf"(?:\b{escaped_terminal}\b|['\"]{escaped_terminal}['\"])\s*:\s*"
                rf"(?:async\s*)?(?:function\b|\([^;{{}}]*\)\s*=>|{_IDENTIFIER}\s*=>)"
            ),
        ),
        (
            "method_definition",
            "terminal_symbol",
            re.compile(rf"\b(?:async\s+)?{escaped_terminal}\s*\([^;{{}}]*\)\s*\{{"),
        ),
    ]
    alias_patterns: list[tuple[str, re.Pattern[str]]] = []
    if callee == terminal:
        alias_patterns.extend(
            [
                (
                    "terminal_symbol",
                    re.compile(
                        rf"\b(?:const|let|var)\s+{escaped_terminal}\s*=\s*"
                        rf"({_IDENTIFIER}(?:\.{_IDENTIFIER})*)\s*[;,]"
                    ),
                ),
                (
                    "full_chain",
                    re.compile(
                        rf"(?<![{_IDENTIFIER_CHARS}]){escaped_full}\s*=\s*"
                        rf"({_IDENTIFIER}(?:\.{_IDENTIFIER})*)\s*[;,]"
                    ),
                ),
            ]
        )
    else:
        alias_patterns.append(
            (
                "full_chain",
                re.compile(
                    rf"(?<![{_IDENTIFIER_CHARS}]){escaped_full}\s*=\s*"
                    rf"({_IDENTIFIER}(?:\.{_IDENTIFIER})*)\s*[;,]"
                ),
            )
        )

    matches: list[tuple[int, str, str, re.Match[str], str | None]] = []
    per_pattern_limit = max_candidates + 1
    for kind, binding_scope, pattern in patterns:
        observed = 0
        for match in pattern.finditer(text):
            if _in_excluded(match.start(), index):
                continue
            prefix = text[max(0, match.start() - 64) : match.start()]
            if kind == "method_definition" and re.search(r"\bfunction\s+$", prefix):
                continue
            if kind == "function_assignment" and re.search(
                r"\b(?:const|let|var)\s+$",
                prefix,
            ):
                continue
            matches.append((match.start(), kind, binding_scope, match, None))
            observed += 1
            if observed == per_pattern_limit:
                break
    for binding_scope, pattern in alias_patterns:
        observed = 0
        for match in pattern.finditer(text):
            if _in_excluded(match.start(), index):
                continue
            prefix = text[max(0, match.start() - 64) : match.start()]
            if binding_scope == "full_chain" and callee == terminal and re.search(
                r"\b(?:const|let|var)\s+$",
                prefix,
            ):
                continue
            alias = match.group(1)
            if alias == callee or alias == terminal:
                continue
            matches.append(
                (match.start(), "alias_assignment", binding_scope, match, alias)
            )
            observed += 1
            if observed == per_pattern_limit:
                break

    matches.sort(key=lambda item: (item[0], item[1], item[2]))
    candidate_scan_truncated = len(matches) > max_candidates
    selected = matches[:max_candidates]
    rows: list[dict[str, Any]] = []
    seen: set[tuple[int, str, str]] = set()
    for _, kind, binding_scope, match, alias in selected:
        key = (match.start(), kind, binding_scope)
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            _candidate(
                text,
                index,
                kind=kind,
                start=match.start(),
                prefix_end=match.end(),
                max_span_chars=max_span_chars,
                binding_scope=binding_scope,
                alias_target=alias,
            )
        )
    rows.sort(key=lambda row: (row["start"], row["kind"]))
    evidence = {
        "full_chain_occurrence_count_observed": len(full_positions),
        "full_chain_occurrence_scan_truncated": full_positions_truncated,
        "terminal_symbol_occurrence_count_observed": len(terminal_positions),
        "terminal_symbol_occurrence_scan_truncated": terminal_positions_truncated,
        "definition_candidate_count": len(rows),
        "definition_candidate_scan_truncated": candidate_scan_truncated,
        "definition_kinds": sorted({str(row["kind"]) for row in rows}),
        "binding_scopes": sorted({str(row["binding_scope"]) for row in rows}),
        "alias_candidate_count": sum(row["kind"] == "alias_assignment" for row in rows),
        "marker_classes": sorted(
            {marker for row in rows for marker in row["marker_classes"]}
        ),
    }
    return rows, evidence
