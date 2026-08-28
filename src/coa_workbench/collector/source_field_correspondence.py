from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping

SOURCE_FIELD_CORRESPONDENCE_VERSION = "source-field-correspondence-v1"
DEFAULT_SERVER_ENDPOINT_CODES = (
    "report_detail_api",
    "report_encounters_api",
    "report_combatants_roster_api",
    "reports_public_api",
)
DEFAULT_FOCUS_TOKENS = ("difficulty", "instance", "map_id")
_PUBLIC_CODE_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be an array")
    return value


def _normalize_focus_tokens(values: Iterable[str]) -> tuple[str, ...]:
    tokens = tuple(
        sorted({str(value).strip().casefold() for value in values if str(value).strip()})
    )
    if not tokens:
        raise ValueError("at least one focus token is required")
    if any(not _PUBLIC_CODE_RE.fullmatch(token) for token in tokens):
        raise ValueError("focus tokens must be public-safe identifiers")
    return tokens


def _dot_segments(path: str) -> tuple[str, ...]:
    return tuple(part for part in str(path).split(".") if part)


def _pointer_segments(path: str) -> tuple[str, ...]:
    if not isinstance(path, str) or not path.startswith("/"):
        return ()
    if path == "/":
        return ()
    return tuple(
        part.replace("~1", "/").replace("~0", "~") for part in path[1:].split("/")
    )


def _segment_matches_focus(segment: str, tokens: tuple[str, ...]) -> bool:
    prepared = segment.casefold()
    return any(token in prepared for token in tokens)


def _focused_suffix(
    segments: tuple[str, ...],
    tokens: tuple[str, ...],
) -> tuple[str, ...] | None:
    for index, segment in enumerate(segments):
        if _segment_matches_focus(segment, tokens):
            return segments[index:]
    return None


def _normalize_types(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, (list, tuple, set)):
        return tuple(sorted({str(item) for item in value}))
    return (str(value),)


def _upstream_focus_fields(
    upstream_review: Mapping[str, Any],
    tokens: tuple[str, ...],
) -> list[dict[str, Any]]:
    fields: list[dict[str, Any]] = []
    for index, raw in enumerate(_list(upstream_review.get("field_lineage"), "field_lineage")):
        item = _mapping(raw, f"field_lineage[{index}]")
        field_path = str(item.get("field_path") or "")
        segments = _dot_segments(field_path)
        if not segments or _focused_suffix(segments, tokens) is None:
            continue
        fields.append(
            {
                "record_code": str(item.get("record_code") or "unknown"),
                "field_path": field_path,
                "source_kind": str(item.get("source_kind") or "unknown"),
                "source_identifier": (
                    None
                    if item.get("source_identifier") is None
                    else str(item.get("source_identifier"))
                ),
                "source_file": str(item.get("source_file") or ""),
                "line": item.get("line") if isinstance(item.get("line"), int) else None,
            }
        )
    unique = {
        (
            item["record_code"],
            item["field_path"],
            item["source_kind"],
            item["source_identifier"],
            item["source_file"],
            item["line"],
        ): item
        for item in fields
    }
    return sorted(
        unique.values(),
        key=lambda item: (
            item["record_code"],
            item["field_path"],
            item["source_file"],
            item["line"] or 0,
        ),
    )


def _server_focus_fields(
    server_path_types: Mapping[str, Mapping[str, Any]],
    tokens: tuple[str, ...],
) -> list[dict[str, Any]]:
    aggregate: dict[tuple[str, tuple[str, ...]], set[str]] = {}
    for endpoint_code_raw, path_map_raw in server_path_types.items():
        endpoint_code = str(endpoint_code_raw)
        if not _PUBLIC_CODE_RE.fullmatch(endpoint_code):
            raise ValueError(f"endpoint code is not public-safe: {endpoint_code}")
        path_map = _mapping(path_map_raw, f"server_path_types[{endpoint_code}]")
        for pointer, raw_types in path_map.items():
            suffix = _focused_suffix(_pointer_segments(str(pointer)), tokens)
            if suffix is None:
                continue
            aggregate.setdefault((endpoint_code, suffix), set()).update(
                _normalize_types(raw_types)
            )
    return [
        {
            "endpoint_code": endpoint_code,
            "focused_path_suffix": ".".join(suffix),
            "json_types": sorted(types),
        }
        for (endpoint_code, suffix), types in sorted(
            aggregate.items(), key=lambda item: (item[0][0], item[0][1])
        )
    ]


def _match_kind(upstream_path: str, server_suffix: str) -> str | None:
    upstream = _dot_segments(upstream_path)
    server = _dot_segments(server_suffix)
    if not upstream or not server:
        return None
    if len(server) >= len(upstream) and server[-len(upstream) :] == upstream:
        return "exact_suffix"
    if server[-1] == upstream[-1]:
        return "leaf_name"
    return None


def build_source_field_correspondence_review_from_inputs(
    *,
    upstream_review: Mapping[str, Any],
    server_path_types: Mapping[str, Mapping[str, Any]],
    focus_tokens: Iterable[str] = DEFAULT_FOCUS_TOKENS,
    server_snapshot_counts: Mapping[str, int] | None = None,
) -> dict[str, Any]:
    tokens = _normalize_focus_tokens(focus_tokens)
    source = _mapping(upstream_review.get("source"), "upstream_review.source")
    upstream_fields = _upstream_focus_fields(upstream_review, tokens)
    server_fields = _server_focus_fields(server_path_types, tokens)

    candidates: list[dict[str, Any]] = []
    for upstream in upstream_fields:
        for server in server_fields:
            match_kind = _match_kind(
                upstream["field_path"], server["focused_path_suffix"]
            )
            if match_kind is None:
                continue
            candidates.append(
                {
                    "match_kind": match_kind,
                    "upstream_record_code": upstream["record_code"],
                    "upstream_field_path": upstream["field_path"],
                    "upstream_source_kind": upstream["source_kind"],
                    "upstream_source_identifier": upstream["source_identifier"],
                    "upstream_source_file": upstream["source_file"],
                    "upstream_line": upstream["line"],
                    "server_endpoint_code": server["endpoint_code"],
                    "server_focused_path_suffix": server["focused_path_suffix"],
                    "server_json_types": server["json_types"],
                }
            )

    candidates.sort(
        key=lambda item: (
            0 if item["match_kind"] == "exact_suffix" else 1,
            item["upstream_field_path"],
            item["server_endpoint_code"],
            item["server_focused_path_suffix"],
        )
    )
    counts = {"exact_suffix": 0, "leaf_name": 0}
    for item in candidates:
        counts[item["match_kind"]] += 1

    snapshot_counts = {
        str(key): int(value)
        for key, value in sorted((server_snapshot_counts or {}).items())
        if str(key) in server_path_types
    }
    return {
        "review_version": SOURCE_FIELD_CORRESPONDENCE_VERSION,
        "focus_tokens": list(tokens),
        "upstream_source": {
            "source_code": source.get("source_code"),
            "revision": source.get("revision"),
        },
        "server_schema": {
            "endpoint_codes": sorted(str(key) for key in server_path_types),
            "snapshot_counts": snapshot_counts,
        },
        "upstream_focus_fields": upstream_fields,
        "server_focus_fields": server_fields,
        "correspondence_candidates": candidates,
        "summary": {
            "upstream_focus_field_count": len(upstream_fields),
            "server_focus_field_count": len(server_fields),
            "exact_suffix_candidate_count": counts["exact_suffix"],
            "leaf_name_candidate_count": counts["leaf_name"],
        },
        "interpretation": {
            "candidate_matches_are_structural_only": True,
            "runtime_value_equivalence_verified": False,
            "backend_transformation_semantics_verified": False,
            "gameplay_semantics_verified": False,
            "numeric_cross_report_scoring_allowed": False,
            "planner_scoring_allowed": False,
        },
        "privacy": {
            "full_server_paths_included": False,
            "report_ids_included": False,
            "encounter_ids_included": False,
            "character_ids_included": False,
            "character_names_included": False,
            "difficulty_values_included": False,
            "raw_payloads_included": False,
            "private_hashes_included": False,
            "public_upstream_source_paths_included": True,
        },
        "public_release_safe": True,
    }


def load_server_schema_paths(
    database_path: Path,
    *,
    endpoint_codes: Iterable[str] = DEFAULT_SERVER_ENDPOINT_CODES,
) -> tuple[dict[str, dict[str, tuple[str, ...]]], dict[str, int]]:
    prepared = tuple(sorted({str(value) for value in endpoint_codes}))
    if not prepared:
        raise ValueError("at least one endpoint code is required")
    if any(not _PUBLIC_CODE_RE.fullmatch(value) for value in prepared):
        raise ValueError("endpoint codes must be public-safe")

    import duckdb

    placeholders = ",".join("?" for _ in prepared)
    query = f"""
        SELECT endpoint_code, path_types_json
        FROM source_schema_snapshot
        WHERE endpoint_code IN ({placeholders})
        ORDER BY endpoint_code, observed_at, snapshot_id
    """
    merged: dict[str, dict[str, set[str]]] = {endpoint: {} for endpoint in prepared}
    counts = {endpoint: 0 for endpoint in prepared}
    with duckdb.connect(str(database_path), read_only=True) as connection:
        rows = connection.execute(query, list(prepared)).fetchall()
    for endpoint_code_raw, path_types_json_raw in rows:
        endpoint_code = str(endpoint_code_raw)
        counts[endpoint_code] = counts.get(endpoint_code, 0) + 1
        parsed = json.loads(str(path_types_json_raw))
        if not isinstance(parsed, dict):
            raise ValueError("source_schema_snapshot.path_types_json must be an object")
        target = merged.setdefault(endpoint_code, {})
        for pointer, raw_types in parsed.items():
            target.setdefault(str(pointer), set()).update(_normalize_types(raw_types))
    rendered = {
        endpoint: {
            pointer: tuple(sorted(types)) for pointer, types in sorted(paths.items())
        }
        for endpoint, paths in sorted(merged.items())
    }
    return rendered, counts


def build_source_field_correspondence_review(
    database_path: Path,
    migrations_dir: Path,
    upstream_review_path: Path,
    *,
    endpoint_codes: Iterable[str] = DEFAULT_SERVER_ENDPOINT_CODES,
    focus_tokens: Iterable[str] = DEFAULT_FOCUS_TOKENS,
) -> dict[str, Any]:
    from coa_workbench.storage.migrations import apply_migrations

    apply_migrations(database_path, migrations_dir)
    upstream_raw = json.loads(upstream_review_path.read_text(encoding="utf-8"))
    upstream_review = _mapping(upstream_raw, "upstream review")
    server_path_types, counts = load_server_schema_paths(
        database_path,
        endpoint_codes=endpoint_codes,
    )
    return build_source_field_correspondence_review_from_inputs(
        upstream_review=upstream_review,
        server_path_types=server_path_types,
        focus_tokens=focus_tokens,
        server_snapshot_counts=counts,
    )


__all__ = [
    "DEFAULT_FOCUS_TOKENS",
    "DEFAULT_SERVER_ENDPOINT_CODES",
    "SOURCE_FIELD_CORRESPONDENCE_VERSION",
    "build_source_field_correspondence_review",
    "build_source_field_correspondence_review_from_inputs",
    "load_server_schema_paths",
]
