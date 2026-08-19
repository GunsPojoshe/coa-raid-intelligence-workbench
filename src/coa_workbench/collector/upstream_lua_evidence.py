from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

UPSTREAM_LUA_EVIDENCE_VERSION = "upstream-lua-evidence-v1"
_PUBLIC_CODE_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,63}$")
_REVISION_RE = re.compile(r"^[0-9a-fA-F]{7,64}$")
_API_NAMESPACE_RE = re.compile(r"\b(C_[A-Za-z0-9_]+)\b")
_NAMESPACE_CALL_RE = re.compile(
    r"\b(?:_G\.)?(C_[A-Za-z0-9_]+)\s*[\.:]\s*([A-Za-z_][A-Za-z0-9_]*)\s*\("
)
_GLOBAL_CALL_RE = re.compile(
    r"\b((?:Get|Unit|Is|Can|Check|Notify|Clear|Logging|Read|Set|Create)"
    r"[A-Z][A-Za-z0-9_]*)\s*\("
)
_REGISTER_EVENT_RE = re.compile(
    r"\b(?:ALC\.)?RegisterEvent\s*\(\s*['\"]([A-Z][A-Z0-9_]+)['\"]"
)
_PCALL_REGISTER_EVENT_RE = re.compile(
    r"\bpcall\s*\(\s*ALC\.RegisterEvent\s*,\s*['\"]([A-Z][A-Z0-9_]+)['\"]"
)
_EVENT_LIKE_LITERAL_RE = re.compile(r"['\"]([A-Z][A-Z0-9_]{2,})['\"]")
_STREAM_LITERAL_RE = re.compile(r"\bstream\s*=\s*['\"]([^'\"]+)['\"]")
_EVENT_TYPE_LITERAL_RE = re.compile(r"\bevent_type\s*=\s*['\"]([^'\"]+)['\"]")
_TRANSPORT_LITERAL_RE = re.compile(r"['\"]([^'\"\r\n]*\[\[ALC_[^'\"\r\n]*)['\"]")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _long_bracket_close(text: str, start: int) -> tuple[str, int] | None:
    if start >= len(text) or text[start] != "[":
        return None
    cursor = start + 1
    while cursor < len(text) and text[cursor] == "=":
        cursor += 1
    if cursor >= len(text) or text[cursor] != "[":
        return None
    equals = text[start + 1 : cursor]
    return "]" + equals + "]", cursor + 1


def _strip_lua_comments(text: str) -> str:
    """Remove Lua line/long comments while preserving strings and line structure."""

    out: list[str] = []
    cursor = 0
    length = len(text)
    while cursor < length:
        char = text[cursor]

        if char in {'"', "'"}:
            quote = char
            out.append(char)
            cursor += 1
            while cursor < length:
                current = text[cursor]
                out.append(current)
                cursor += 1
                if current == "\\" and cursor < length:
                    out.append(text[cursor])
                    cursor += 1
                elif current == quote:
                    break
            continue

        if char == "[":
            long_string = _long_bracket_close(text, cursor)
            if long_string is not None:
                close, content_start = long_string
                close_at = text.find(close, content_start)
                if close_at == -1:
                    out.append(text[cursor:])
                    break
                end = close_at + len(close)
                out.append(text[cursor:end])
                cursor = end
                continue

        if text.startswith("--", cursor):
            possible_long = _long_bracket_close(text, cursor + 2)
            if possible_long is not None:
                close, content_start = possible_long
                close_at = text.find(close, content_start)
                end = length if close_at == -1 else close_at + len(close)
                removed = text[cursor:end]
                out.extend("\n" if current == "\n" else " " for current in removed)
                cursor = end
                continue

            line_end = text.find("\n", cursor)
            if line_end == -1:
                out.extend(" " for _ in text[cursor:])
                break
            out.extend(" " for _ in text[cursor:line_end])
            out.append("\n")
            cursor = line_end + 1
            continue

        out.append(char)
        cursor += 1

    return "".join(out)


def _strip_lua_strings(text: str) -> str:
    """Mask Lua quoted/long strings so identifier regexes do not inspect string contents."""

    out: list[str] = []
    cursor = 0
    length = len(text)
    while cursor < length:
        char = text[cursor]
        if char in {'"', "'"}:
            quote = char
            out.append(" ")
            cursor += 1
            while cursor < length:
                current = text[cursor]
                if current == "\n":
                    out.append("\n")
                else:
                    out.append(" ")
                cursor += 1
                if current == "\\" and cursor < length:
                    out.append("\n" if text[cursor] == "\n" else " ")
                    cursor += 1
                elif current == quote:
                    break
            continue

        if char == "[":
            long_string = _long_bracket_close(text, cursor)
            if long_string is not None:
                close, content_start = long_string
                close_at = text.find(close, content_start)
                end = length if close_at == -1 else close_at + len(close)
                removed = text[cursor:end]
                out.extend("\n" if current == "\n" else " " for current in removed)
                cursor = end
                continue

        out.append(char)
        cursor += 1

    return "".join(out)


def _sorted_unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted(set(values)))


@dataclass(frozen=True, slots=True)
class LuaFileEvidence:
    relative_path: str
    sha256: str
    api_namespaces: tuple[str, ...]
    api_calls: tuple[str, ...]
    registered_events: tuple[str, ...]
    event_like_literals: tuple[str, ...]
    stream_literals: tuple[str, ...]
    event_type_literals: tuple[str, ...]
    transport_literals: tuple[str, ...]

    def public_summary(self) -> dict[str, object]:
        return asdict(self)


def extract_lua_file_evidence(
    content: bytes,
    *,
    relative_path: str,
) -> LuaFileEvidence:
    if not relative_path or relative_path.startswith("/") or "\\" in relative_path:
        raise ValueError("relative_path must be a public POSIX-style relative path")
    if any(part in {"", ".", ".."} for part in relative_path.split("/")):
        raise ValueError("relative_path contains an unsafe path segment")

    text = content.decode("utf-8", errors="replace")
    uncommented = _strip_lua_comments(text)
    identifiers_only = _strip_lua_strings(uncommented)

    api_namespaces = _sorted_unique(_API_NAMESPACE_RE.findall(identifiers_only))
    namespace_calls = (
        f"{namespace}.{function}"
        for namespace, function in _NAMESPACE_CALL_RE.findall(identifiers_only)
    )
    global_calls = _GLOBAL_CALL_RE.findall(identifiers_only)
    api_calls = _sorted_unique((*namespace_calls, *global_calls))

    registered_events = _sorted_unique(
        (*_REGISTER_EVENT_RE.findall(uncommented), *_PCALL_REGISTER_EVENT_RE.findall(uncommented))
    )

    return LuaFileEvidence(
        relative_path=relative_path,
        sha256=_sha256_bytes(content),
        api_namespaces=api_namespaces,
        api_calls=api_calls,
        registered_events=registered_events,
        event_like_literals=_sorted_unique(_EVENT_LIKE_LITERAL_RE.findall(uncommented)),
        stream_literals=_sorted_unique(_STREAM_LITERAL_RE.findall(uncommented)),
        event_type_literals=_sorted_unique(_EVENT_TYPE_LITERAL_RE.findall(uncommented)),
        transport_literals=_sorted_unique(_TRANSPORT_LITERAL_RE.findall(uncommented)),
    )


def review_lua_source_tree(
    source_root: Path,
    *,
    source_code: str,
    revision: str,
    max_files: int = 1000,
    max_file_bytes: int = 2_000_000,
) -> dict[str, object]:
    if not _PUBLIC_CODE_RE.fullmatch(source_code):
        raise ValueError("source_code must be a lowercase public-safe code")
    if not _REVISION_RE.fullmatch(revision):
        raise ValueError("revision must be a 7-64 character hexadecimal revision")
    if max_files < 1 or max_file_bytes < 1:
        raise ValueError("review bounds must be positive")

    root = source_root.resolve()
    if not root.is_dir():
        raise ValueError("source_root must be an existing directory")

    files: list[LuaFileEvidence] = []
    for candidate in sorted(root.rglob("*.lua")):
        if not candidate.is_file():
            continue
        resolved = candidate.resolve()
        try:
            relative = resolved.relative_to(root).as_posix()
        except ValueError as exc:
            raise ValueError("source file resolves outside source_root") from exc
        content = resolved.read_bytes()
        if len(content) > max_file_bytes:
            raise ValueError(f"Lua source exceeds max_file_bytes: {relative}")
        files.append(extract_lua_file_evidence(content, relative_path=relative))
        if len(files) > max_files:
            raise ValueError("Lua source tree exceeds max_files")

    aggregate_api_namespaces = _sorted_unique(
        value for file in files for value in file.api_namespaces
    )
    aggregate_api_calls = _sorted_unique(value for file in files for value in file.api_calls)
    aggregate_registered_events = _sorted_unique(
        value for file in files for value in file.registered_events
    )
    aggregate_event_like_literals = _sorted_unique(
        value for file in files for value in file.event_like_literals
    )
    aggregate_stream_literals = _sorted_unique(
        value for file in files for value in file.stream_literals
    )
    aggregate_event_type_literals = _sorted_unique(
        value for file in files for value in file.event_type_literals
    )
    aggregate_transport_literals = _sorted_unique(
        value for file in files for value in file.transport_literals
    )

    return {
        "review_version": UPSTREAM_LUA_EVIDENCE_VERSION,
        "source": {
            "source_code": source_code,
            "revision": revision.lower(),
            "file_count": len(files),
            "source_root_included": False,
            "source_text_included": False,
            "network_requests_performed": False,
        },
        "aggregate": {
            "api_namespaces": list(aggregate_api_namespaces),
            "api_calls": list(aggregate_api_calls),
            "registered_events": list(aggregate_registered_events),
            "event_like_literals": list(aggregate_event_like_literals),
            "stream_literals": list(aggregate_stream_literals),
            "event_type_literals": list(aggregate_event_type_literals),
            "transport_literals": list(aggregate_transport_literals),
        },
        "files": [file.public_summary() for file in files],
        "interpretation": {
            "inventory_is_semantic_proof": False,
            "comments_are_parsed_for_executable_facts": False,
            "identifiers_are_not_gameplay_mechanics": True,
            "backend_semantics_require_corroboration": True,
        },
    }


def write_upstream_lua_review(path: Path, review: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(review, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


__all__ = [
    "UPSTREAM_LUA_EVIDENCE_VERSION",
    "LuaFileEvidence",
    "extract_lua_file_evidence",
    "review_lua_source_tree",
    "write_upstream_lua_review",
]
