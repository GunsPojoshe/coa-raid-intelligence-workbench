from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .guild_progression_callsite_contract import MARKERS, METHODS, sha256

_IDENTIFIER = r"[A-Za-z_$][A-Za-z0-9_$]*"
_MEMBER_CHAIN = re.compile(rf"({_IDENTIFIER}(?:\s*\.\s*{_IDENTIFIER})*)\s*$")
_METHOD_LITERAL = re.compile(
    r"\bmethod\s*:\s*['\"](GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)['\"]",
    re.IGNORECASE,
)
_DECLARATION = re.compile(rf"\b(?:const|let|var)\s+({_IDENTIFIER})\s*=\s*$")
_ASSIGNMENT = re.compile(rf"({_IDENTIFIER}(?:\s*\.\s*{_IDENTIFIER})*)\s*=\s*$")
_PROPERTY = re.compile(rf"(?:({_IDENTIFIER})|['\"]([^'\"]+)['\"])\s*:\s*$")
_FUNCTION_PREFIX = re.compile(
    rf"(?:\bfunction(?:\s+{_IDENTIFIER})?\s*\([^)]*\)"
    rf"|\([^)]*\)\s*=>|{_IDENTIFIER}\s*=>"
    rf"|{_IDENTIFIER}\s*\([^)]*\))\s*$"
)
_ARROW_OBJECT_PREFIX = re.compile(rf"(?:\([^)]*\)|{_IDENTIFIER})\s*=>\s*\(\s*$")


@dataclass(frozen=True, slots=True)
class StringSpan:
    start: int
    end: int
    quote: str


@dataclass(frozen=True, slots=True)
class StructuralIndex:
    pairs: dict[int, int]
    string_spans: tuple[StringSpan, ...]


def scan_structure(text: str) -> StructuralIndex:
    pairs: dict[int, int] = {}
    spans: list[StringSpan] = []
    stacks: dict[str, list[int]] = {"(": [], "[": [], "{": []}
    closing = {")": "(", "]": "[", "}": "{"}
    mode = "code"
    quote = ""
    string_start = -1
    index = 0
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if mode == "line_comment":
            mode = "code" if char in "\r\n" else mode
        elif mode == "block_comment":
            if char == "*" and next_char == "/":
                mode = "code"
                index += 1
        elif mode == "string":
            if char == "\\":
                index += 1
            elif char == quote:
                spans.append(StringSpan(string_start, index + 1, quote))
                mode = "code"
        elif char == "/" and next_char == "/":
            mode = "line_comment"
            index += 1
        elif char == "/" and next_char == "*":
            mode = "block_comment"
            index += 1
        elif char in "'\"`":
            mode, quote, string_start = "string", char, index
        elif char in stacks:
            stacks[char].append(index)
        elif char in closing and stacks[closing[char]]:
            pairs[stacks[closing[char]].pop()] = index
        index += 1
    return StructuralIndex(pairs, tuple(spans))


def string_span_for(position: int, spans: tuple[StringSpan, ...]) -> StringSpan:
    for span in spans:
        if span.start < position < span.end:
            return span
    raise ValueError("progression route is not inside a string literal")


def openers_of(
    text: str,
    index: StructuralIndex,
    position: int,
    opener: str,
) -> list[int]:
    return sorted(
        (
            start
            for start, end in index.pairs.items()
            if start < position < end and text[start] == opener
        ),
        reverse=True,
    )


def property_markers(value: str) -> list[str]:
    return sorted(
        key
        for key in MARKERS
        if re.search(rf"(?:\b{re.escape(key)}\b|['\"]{re.escape(key)}['\"])\s*:", value)
    )


def assignment_candidate(text: str, span: StringSpan) -> dict[str, Any]:
    prefix = text[max(0, span.start - 320) : span.start]
    if match := _DECLARATION.search(prefix):
        symbol = match.group(1)
        return {
            "kind": "variable_declaration",
            "symbol": symbol,
            "symbol_sha256": sha256(symbol.encode()),
            "property_sha256": None,
        }
    if match := _PROPERTY.search(prefix):
        name = match.group(1) or match.group(2)
        return {
            "kind": "url_property_value" if name == "url" else "object_property_value",
            "symbol": None,
            "symbol_sha256": None,
            "property_sha256": sha256(name.encode()),
        }
    if match := _ASSIGNMENT.search(prefix):
        symbol = re.sub(r"\s+", "", match.group(1))
        return {
            "kind": "assignment_expression",
            "symbol": symbol,
            "symbol_sha256": sha256(symbol.encode()),
            "property_sha256": None,
        }
    return {
        "kind": "none",
        "symbol": None,
        "symbol_sha256": None,
        "property_sha256": None,
    }


def function_candidate(
    text: str,
    index: StructuralIndex,
    position: int,
) -> dict[str, Any]:
    for opening in openers_of(text, index, position, "{")[:12]:
        prefix = text[max(0, opening - 480) : opening]
        match = _FUNCTION_PREFIX.search(prefix)
        kind = "block_function"
        if not match:
            match = _ARROW_OBJECT_PREFIX.search(prefix)
            kind = "concise_arrow_object_return"
        if match:
            closing = index.pairs[opening] + 1
            value = text[opening:closing]
            return {
                "observed": True,
                "kind": kind,
                "span_sha256": sha256(value.encode()),
                "character_count": len(value),
                "prefix_sha256": sha256(match.group(0).encode()),
                "private_prefix": match.group(0),
            }
    return {
        "observed": False,
        "kind": "none",
        "span_sha256": None,
        "character_count": 0,
        "prefix_sha256": None,
        "private_prefix": None,
    }


def _callee_before(text: str, opening: int) -> str | None:
    match = _MEMBER_CHAIN.search(text[max(0, opening - 320) : opening])
    return re.sub(r"\s+", "", match.group(1)) if match else None


def call_candidates(
    text: str,
    index: StructuralIndex,
    position: int,
    string_span: StringSpan,
    max_depth: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for depth, opening in enumerate(openers_of(text, index, position, "(")[:max_depth], 1):
        callee = _callee_before(text, opening)
        if not callee:
            continue
        closing = index.pairs[opening] + 1
        value = text[opening:closing]
        terminal = callee.rsplit(".", 1)[-1]
        member_method = terminal.upper() if "." in callee and terminal.upper() in METHODS else None
        if callee == "fetch":
            call_class = "fetch_call"
        elif member_method:
            call_class = "http_member_call"
        else:
            call_class = "generic_helper_call"
        methods = {item.upper() for item in _METHOD_LITERAL.findall(value)}
        evidence: set[str] = set()
        if member_method:
            methods.add(member_method)
            evidence.add("member_method_name")
        if _METHOD_LITERAL.search(value):
            evidence.add("method_property_literal")
        if call_class == "fetch_call" and not methods:
            methods.add("GET")
            evidence.add("fetch_default_method")
        nested = any(
            opening < child < string_span.start < index.pairs[child] < closing
            for bracket in ("{", "[")
            for child in openers_of(text, index, position, bracket)
        )
        rows.append(
            {
                "depth": depth,
                "callee": callee,
                "callee_sha256": sha256(callee.encode()),
                "class": call_class,
                "span_sha256": sha256(value.encode()),
                "character_count": len(value),
                "methods": sorted(methods),
                "method_evidence": sorted(evidence),
                "direct_argument": not nested,
                "property_markers": property_markers(value),
                "start": opening,
                "end": closing,
            }
        )
    return rows


def private_excerpt(text: str, start: int, end: int, chars: int) -> tuple[str, int, int]:
    left, right = max(0, start - chars), min(len(text), end + chars)
    return text[left:right], left, right
