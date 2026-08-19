from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from coa_workbench.collector.upstream_lua_evidence import (
    _NAMESPACE_CALL_RE,
    _strip_lua_comments,
    _strip_lua_strings,
    _sorted_unique,
)

UPSTREAM_LUA_LINEAGE_VERSION = "upstream-lua-lineage-v1"
_PUBLIC_CODE_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,63}$")
_REVISION_RE = re.compile(r"^[0-9a-fA-F]{7,64}$")
_FUNCTION_RE = re.compile(
    r"\b(?:local\s+function\s+([A-Za-z_][A-Za-z0-9_]*)|"
    r"function\s+([A-Za-z_][A-Za-z0-9_.:]*))\s*\("
)
_BLOCK_TOKEN_RE = re.compile(r"\b(function|if|for|while|repeat|end|until)\b")
_TABLE_ASSIGN_RE = re.compile(r"\b(?:local\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\{")
_MEMBER_TABLE_RE = re.compile(
    r"\b([A-Za-z_][A-Za-z0-9_]*)((?:\.[A-Za-z_][A-Za-z0-9_]*)+)\s*=\s*\{"
)
_MEMBER_RE = re.compile(
    r"\b([A-Za-z_][A-Za-z0-9_]*)((?:\.[A-Za-z_][A-Za-z0-9_]*)+)\s*=\s*([^\n;]+)"
)
_RETURN_VAR_RE = re.compile(r"\breturn\s+([A-Za-z_][A-Za-z0-9_]*)\b")
_RETURN_TABLE_RE = re.compile(r"\breturn\s*\{")
_DIRECT_BINDING_RE = re.compile(
    r"\blocal\s+([A-Za-z_][A-Za-z0-9_]*(?:\s*,\s*[A-Za-z_][A-Za-z0-9_]*)*)"
    r"\s*=\s*((?:_G\.)?C_[A-Za-z0-9_]+\s*[\.:]\s*[A-Za-z_][A-Za-z0-9_]*|"
    r"(?:Get|Unit|Is|Can|Check|Notify|Clear|Logging|Read|Set|Create)[A-Z][A-Za-z0-9_]*)\s*\("
)
_PCALL_BINDING_RE = re.compile(
    r"\blocal\s+([A-Za-z_][A-Za-z0-9_]*(?:\s*,\s*[A-Za-z_][A-Za-z0-9_]*)*)"
    r"\s*=\s*pcall\s*\(\s*((?:_G\.)?C_[A-Za-z0-9_]+\s*[\.:]\s*[A-Za-z_][A-Za-z0-9_]*)"
)
_LOCAL_CALL_BINDING_RE = re.compile(
    r"\blocal\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([A-Za-z_][A-Za-z0-9_.:]*)\s*\("
)
_SIMPLE_CALL_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_.:]*)\s*\(")
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_QUALIFIED_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+$")
_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", re.DOTALL)
_STRING_KEY_RE = re.compile(r"^\[\s*['\"]([^'\"]+)['\"]\s*\]\s*=\s*(.*)$", re.DOTALL)
_STRING_LITERAL_RE = re.compile(r"^['\"]([^'\"]+)['\"]$")
_GLOBAL_CALL_RE = re.compile(
    r"^((?:Get|Unit|Is|Can|Check|Notify|Clear|Logging|Read|Set|Create)"
    r"[A-Z][A-Za-z0-9_]*)\s*\("
)


def _canonical_call(value: str) -> str:
    value = re.sub(r"\s+", "", value).replace(":", ".")
    return value[3:] if value.startswith("_G.") else value


def _line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def _matching_function_end(masked: str, start: int) -> int:
    stack: list[str] = []
    for match in _BLOCK_TOKEN_RE.finditer(masked, start):
        token = match.group(1)
        if token in {"function", "if", "for", "while", "repeat"}:
            stack.append(token)
        elif token == "until":
            if stack and stack[-1] == "repeat":
                stack.pop()
        elif token == "end" and stack and stack[-1] != "repeat":
            stack.pop()
            if not stack:
                return match.end()
    raise ValueError("unterminated Lua function block")


def _function_blocks(text: str) -> tuple[tuple[str, int, str], ...]:
    masked = _strip_lua_strings(text)
    blocks: list[tuple[str, int, str]] = []
    for match in _FUNCTION_RE.finditer(masked):
        name = match.group(1) or match.group(2)
        end = _matching_function_end(masked, match.start())
        blocks.append((name, match.start(), text[match.start() : end]))
    return tuple(blocks)


def _matching_brace(text: str, start: int) -> int:
    if text[start] != "{":
        raise ValueError("table constructor must start with '{'")
    depth = 1
    quote: str | None = None
    escaped = False
    for index in range(start + 1, len(text)):
        char = text[index]
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in {'"', "'"}:
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
    raise ValueError("unterminated Lua table constructor")


def _split_table_items(text: str) -> tuple[tuple[str, int], ...]:
    items: list[tuple[str, int]] = []
    start = 0
    braces = brackets = parens = 0
    quote: str | None = None
    escaped = False
    for index, char in enumerate(text):
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in {'"', "'"}:
            quote = char
        elif char == "{":
            braces += 1
        elif char == "}":
            braces -= 1
        elif char == "[":
            brackets += 1
        elif char == "]":
            brackets -= 1
        elif char == "(":
            parens += 1
        elif char == ")":
            parens -= 1
        elif char in {",", ";"} and braces == brackets == parens == 0:
            items.append((text[start:index], start))
            start = index + 1
    items.append((text[start:], start))
    return tuple(items)


@dataclass(frozen=True, slots=True)
class FieldExpression:
    field_path: str
    value_expression: str
    line: int


@dataclass(frozen=True, slots=True)
class FieldLineage:
    record_code: str
    field_path: str
    source_kind: str
    source_identifier: str | None
    function_name: str
    root_variable: str
    line: int
    via_functions: tuple[str, ...]

    def public_summary(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class _FunctionShape:
    name: str
    bindings: dict[str, str]
    local_calls: dict[str, str]
    tables: dict[str, tuple[FieldExpression, ...]]
    returns: tuple[str, ...]


def _table_fields(
    table_text: str,
    *,
    absolute_start: int,
    full_text: str,
    prefix: tuple[str, ...] = (),
) -> tuple[FieldExpression, ...]:
    fields: list[FieldExpression] = []
    for raw_item, offset in _split_table_items(table_text[1:-1]):
        item = raw_item.strip()
        match = _KEY_RE.match(item) or _STRING_KEY_RE.match(item)
        if not item or match is None:
            continue
        key, value = match.group(1), match.group(2).strip()
        path = (*prefix, key)
        item_start = absolute_start + 1 + offset + len(raw_item) - len(raw_item.lstrip())
        if value.startswith("{"):
            try:
                close = _matching_brace(value, 0)
            except ValueError:
                close = -1
            if close == len(value) - 1:
                fields.extend(
                    _table_fields(
                        value,
                        absolute_start=item_start + item.find("{"),
                        full_text=full_text,
                        prefix=path,
                    )
                )
                continue
        fields.append(FieldExpression(".".join(path), value, _line_number(full_text, item_start)))
    return tuple(fields)


def _function_shape(name: str, body: str, start: int, full_text: str) -> _FunctionShape:
    masked = _strip_lua_strings(body)
    bindings: dict[str, str] = {}
    for match in _DIRECT_BINDING_RE.finditer(masked):
        call = _canonical_call(match.group(2))
        for variable in match.group(1).split(","):
            bindings[variable.strip()] = call
    for match in _PCALL_BINDING_RE.finditer(masked):
        call = _canonical_call(match.group(2))
        variables = [item.strip() for item in match.group(1).split(",")]
        for variable in variables[1:]:
            bindings[variable] = call

    local_calls: dict[str, str] = {}
    for match in _LOCAL_CALL_BINDING_RE.finditer(masked):
        variable, call = match.group(1), _canonical_call(match.group(2))
        if not call.startswith("C_") and call not in bindings.values():
            local_calls[variable] = call

    tables: dict[str, tuple[FieldExpression, ...]] = {}
    occupied: list[tuple[int, int]] = []
    for match in _TABLE_ASSIGN_RE.finditer(body):
        open_at = match.end() - 1
        if any(left <= open_at < right for left, right in occupied):
            continue
        close_at = _matching_brace(body, open_at)
        occupied.append((open_at, close_at + 1))
        tables[match.group(1)] = _table_fields(
            body[open_at : close_at + 1],
            absolute_start=start + open_at,
            full_text=full_text,
        )

    returned_fields: list[FieldExpression] = []
    for match in _RETURN_TABLE_RE.finditer(body):
        open_at = match.end() - 1
        if any(left <= open_at < right for left, right in occupied):
            continue
        close_at = _matching_brace(body, open_at)
        occupied.append((open_at, close_at + 1))
        returned_fields.extend(
            _table_fields(
                body[open_at : close_at + 1],
                absolute_start=start + open_at,
                full_text=full_text,
            )
        )
    if returned_fields:
        tables["@return"] = tuple(returned_fields)

    member_table_starts = {match.start() for match in _MEMBER_TABLE_RE.finditer(body)}
    for match in _MEMBER_TABLE_RE.finditer(body):
        open_at = match.end() - 1
        close_at = _matching_brace(body, open_at)
        root = match.group(1)
        if root not in tables:
            continue
        prefix = tuple(part for part in match.group(2).split(".") if part)
        tables[root] = (
            *tables[root],
            *_table_fields(
                body[open_at : close_at + 1],
                absolute_start=start + open_at,
                full_text=full_text,
                prefix=prefix,
            ),
        )
    for match in _MEMBER_RE.finditer(body):
        if match.start() in member_table_starts:
            continue
        root = match.group(1)
        if root not in tables:
            continue
        value = match.group(3).strip()
        if value.startswith("{"):
            continue
        path = ".".join(part for part in match.group(2).split(".") if part)
        tables[root] = (
            *tables[root],
            FieldExpression(path, value, _line_number(full_text, start + match.start())),
        )

    returns = [
        value
        for value in _RETURN_VAR_RE.findall(masked)
        if value not in {"nil", "true", "false"}
    ]
    if returned_fields:
        returns.append("@return")
    return _FunctionShape(name, bindings, local_calls, tables, _sorted_unique(returns))


def _resolve_function(expression: str, functions: dict[str, _FunctionShape]) -> str | None:
    match = _SIMPLE_CALL_RE.match(expression.strip())
    if match is None:
        return None
    called = match.group(1).replace(":", ".")
    if called in functions:
        return called
    short = called.rsplit(".", 1)[-1]
    matches = [name for name in functions if name.rsplit(".", 1)[-1] == short]
    return matches[0] if len(matches) == 1 else None


def _record_code(shape: _FunctionShape, root: str) -> str:
    for field in shape.tables.get(root, ()):
        if field.field_path == "stream":
            match = _STRING_LITERAL_RE.match(field.value_expression)
            if match:
                return match.group(1)
    short = shape.name.rsplit(".", 1)[-1].casefold()
    return "ci" if root == "ci" or short.endswith("ci") else "unknown"


def _expand_helper(
    helper: str,
    functions: dict[str, _FunctionShape],
    *,
    record_code: str,
    prefix: str,
    via: tuple[str, ...],
    seen: frozenset[tuple[str, str]],
) -> tuple[FieldLineage, ...]:
    shape = functions[helper]
    if len(shape.returns) != 1 or shape.returns[0] not in shape.tables:
        return ()
    return _lineage(
        shape,
        shape.returns[0],
        functions,
        record_code=record_code,
        prefix=prefix,
        via=via,
        seen=seen,
    )


def _lineage(
    shape: _FunctionShape,
    root: str,
    functions: dict[str, _FunctionShape],
    *,
    record_code: str,
    prefix: str = "",
    via: tuple[str, ...] = (),
    seen: frozenset[tuple[str, str]] = frozenset(),
) -> tuple[FieldLineage, ...]:
    identity = (shape.name, root)
    if identity in seen:
        return ()
    seen = seen | {identity}
    output: list[FieldLineage] = []
    for field in shape.tables.get(root, ()):
        path = f"{prefix}.{field.field_path}" if prefix else field.field_path
        expression = field.value_expression.strip()
        source_kind, source_identifier = "unresolved", None
        masked = _strip_lua_strings(expression)
        namespace = _NAMESPACE_CALL_RE.search(masked)
        global_call = _GLOBAL_CALL_RE.match(masked)
        if namespace is not None:
            source_kind = "api_call"
            source_identifier = _canonical_call(f"{namespace.group(1)}.{namespace.group(2)}")
        elif global_call is not None:
            source_kind, source_identifier = "api_call", global_call.group(1)
        elif _IDENTIFIER_RE.fullmatch(expression) and expression in shape.bindings:
            source_kind, source_identifier = "api_binding", shape.bindings[expression]
        elif _IDENTIFIER_RE.fullmatch(expression) and expression in shape.tables:
            nested = _lineage(
                shape,
                expression,
                functions,
                record_code=record_code,
                prefix=path,
                via=via,
                seen=seen,
            )
            if nested:
                output.extend(nested)
                continue
        else:
            helper = _resolve_function(expression, functions)
            if helper is None and _IDENTIFIER_RE.fullmatch(expression):
                bound = shape.local_calls.get(expression)
                if bound:
                    helper = _resolve_function(bound + "()", functions)
            if helper is not None:
                nested = _expand_helper(
                    helper,
                    functions,
                    record_code=record_code,
                    prefix=path,
                    via=(*via, shape.name),
                    seen=seen,
                )
                if nested:
                    output.extend(nested)
                    continue
                source_kind, source_identifier = "local_function", helper
            elif _QUALIFIED_RE.fullmatch(expression):
                root_name = expression.split(".", 1)[0]
                if root_name in shape.bindings:
                    source_kind = "api_binding_member"
                    source_identifier = shape.bindings[root_name]
            elif _STRING_LITERAL_RE.fullmatch(expression):
                source_kind = "literal"
        output.append(
            FieldLineage(
                record_code,
                path,
                source_kind,
                source_identifier,
                shape.name,
                root,
                field.line,
                (*via, shape.name),
            )
        )
    return tuple(output)


def extract_lua_file_lineage(content: bytes, *, relative_path: str) -> dict[str, object]:
    if not relative_path or relative_path.startswith("/") or "\\" in relative_path:
        raise ValueError("relative_path must be a public POSIX-style relative path")
    if any(part in {"", ".", ".."} for part in relative_path.split("/")):
        raise ValueError("relative_path contains an unsafe path segment")

    text = _strip_lua_comments(content.decode("utf-8", errors="replace"))
    functions = {
        name: _function_shape(name, body, start, text)
        for name, start, body in _function_blocks(text)
    }
    records: list[dict[str, object]] = []
    collected: list[FieldLineage] = []
    for shape in functions.values():
        for root in sorted(shape.tables):
            record_code = _record_code(shape, root)
            if record_code == "unknown":
                continue
            resolved = _lineage(shape, root, functions, record_code=record_code)
            collected.extend(resolved)
            records.append(
                {
                    "record_code": record_code,
                    "function_name": shape.name,
                    "root_variable": root,
                    "field_paths": sorted({item.field_path for item in resolved}),
                }
            )

    unique = {
        (
            item.record_code,
            item.field_path,
            item.source_kind,
            item.source_identifier,
            item.function_name,
            item.root_variable,
            item.line,
            item.via_functions,
        ): item
        for item in collected
    }
    ordered = sorted(
        unique.values(),
        key=lambda item: (
            item.record_code,
            item.field_path,
            item.function_name,
            item.line,
            item.source_kind,
            item.source_identifier or "",
        ),
    )
    return {
        "relative_path": relative_path,
        "sha256": hashlib.sha256(content).hexdigest(),
        "function_count": len(functions),
        "records": records,
        "field_lineage": [
            {**item.public_summary(), "source_file": relative_path} for item in ordered
        ],
    }


def review_lua_lineage_tree(
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

    files: list[dict[str, object]] = []
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
        files.append(extract_lua_file_lineage(content, relative_path=relative))
        if len(files) > max_files:
            raise ValueError("Lua source tree exceeds max_files")

    lineage = [item for file in files for item in file["field_lineage"]]
    return {
        "review_version": UPSTREAM_LUA_LINEAGE_VERSION,
        "source": {
            "source_code": source_code,
            "revision": revision.lower(),
            "file_count": len(files),
            "source_root_included": False,
            "source_text_included": False,
            "network_requests_performed": False,
        },
        "aggregate": {
            "record_codes": list(_sorted_unique(item["record_code"] for item in lineage)),
            "source_identifiers": list(
                _sorted_unique(
                    item["source_identifier"]
                    for item in lineage
                    if item["source_identifier"] is not None
                )
            ),
            "lineage_count": len(lineage),
        },
        "field_lineage": sorted(
            lineage,
            key=lambda item: (
                item["record_code"],
                item["field_path"],
                item["source_file"],
                item["line"],
            ),
        ),
        "files": files,
        "interpretation": {
            "lineage_is_static_structural_evidence": True,
            "lineage_is_runtime_value_proof": False,
            "lineage_is_backend_semantic_proof": False,
            "lineage_is_gameplay_semantic_proof": False,
        },
    }


def write_lua_lineage_review(path: Path, review: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(review, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


__all__ = [
    "UPSTREAM_LUA_LINEAGE_VERSION",
    "FieldLineage",
    "extract_lua_file_lineage",
    "review_lua_lineage_tree",
    "write_lua_lineage_review",
]
