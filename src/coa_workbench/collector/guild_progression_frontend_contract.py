from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .guild_progression_callsite_contract import load_asset, load_json, property_names, sha256, write_json

REVIEW_KIND = "guild_progression_frontend_request_contract"
REVIEW_VERSION = "guild-progression-frontend-request-contract-v1"
API_BASE_URL = "https://coa.ascensionlogs.gg/api"
LEGACY_PREFIX = "/api/guilds/progression"

_IDENTIFIER = r"[A-Za-z_$][A-Za-z0-9_$]*"
_REQUEST_METHODS = "get|post|put|patch|delete"
_FORBIDDEN_PUBLIC_FIELDS = {
    "raw_context",
    "raw_excerpt",
    "raw_javascript",
    "raw_payload",
    "source_guild_id",
    "source_report_id",
    "private_query",
    "request_body",
}


def _find_api_client(text: str) -> str:
    base_bindings = re.findall(
        rf'(?P<name>{_IDENTIFIER})=["\']{re.escape(API_BASE_URL)}["\']',
        text,
    )
    if len(base_bindings) != 1:
        raise ValueError("expected exactly one API base URL binding")
    clients = re.findall(
        rf'(?P<client>{_IDENTIFIER})={_IDENTIFIER}\.create\(\{{baseURL:{re.escape(base_bindings[0])},',
        text,
    )
    if len(clients) != 1:
        raise ValueError("expected exactly one API client binding")
    return clients[0]


def _template_route(argument: str, prefix: str) -> str | None:
    if argument.startswith(('"', "'")):
        route = argument[1:-1]
    elif argument.startswith("`"):
        route = argument[1:-1]
        for expression in re.findall(r"\$\{([^{}]+)\}", route):
            bindings = re.findall(
                rf'\(\{{(?P<name>{_IDENTIFIER}):{re.escape(expression)}\}}\)=',
                prefix[-4096:],
            )
            name = bindings[-1] if bindings else "path_param"
            route = route.replace("${" + expression + "}", "{" + name + "}")
    else:
        return None
    if not route.startswith("/guilds/progression"):
        return None
    return "/api" + route


def _initializer(prefix: str, identifier: str) -> str:
    matches = list(re.finditer(rf'(?<![\w$.]){re.escape(identifier)}=', prefix))
    if not matches:
        raise ValueError(f"unable to locate params initializer for {identifier}")
    start = matches[-1].end()
    depth = 0
    for index in range(start, len(prefix)):
        char = prefix[index]
        if char in "([{":
            depth += 1
        elif char in ")]}" and depth:
            depth -= 1
        elif char in {",", ";"} and depth == 0:
            return prefix[start:index]
    return prefix[start:]


def _parameter_contract(prefix: str, options: str) -> tuple[list[str], bool]:
    params = re.search(rf'params:(?P<id>{_IDENTIFIER})\b', options)
    if params is None:
        return [], True
    identifier = params.group("id")
    window = prefix[-1800:]
    expression = _initializer(window, identifier)
    keys = set(re.findall(r'(?<=[{,])([A-Za-z_$][A-Za-z0-9_$]*):', expression))
    keys.update(
        re.findall(rf'\b{re.escape(identifier)}\.([A-Za-z_$][A-Za-z0-9_$]*)=', window)
    )
    return sorted(keys), bool(re.search(r'\?\{\}:', expression))


def analyze_frontend_contract(text: str) -> dict[str, Any]:
    text = text.replace("\\/", "/")
    client = _find_api_client(text)

    exact_prefix_literal = rf'(["\']){re.escape(LEGACY_PREFIX)}\1'
    prefix_positions = [match.start() for match in re.finditer(exact_prefix_literal, text)]
    cache_occurrences = sum(
        'noCacheEndpoints:[' in text[max(0, position - 800) : position]
        for position in prefix_positions
    )

    route_argument = r'(?P<route>"[^"\n]*"|\'[^\'\n]*\'|`[^`\n]*`)'
    request_pattern = re.compile(
        rf'\b{re.escape(client)}\.(?P<method>{_REQUEST_METHODS})\('
        rf'{route_argument},(?P<options>\{{params:{_IDENTIFIER}\}})\)'
    )
    calls: list[dict[str, Any]] = []
    for match in request_pattern.finditer(text):
        prefix = text[max(0, match.start() - 5000) : match.start()]
        route = _template_route(match.group("route"), prefix)
        if route is None:
            continue
        parameter_keys, empty_branch = _parameter_contract(prefix, match.group("options"))
        calls.append(
            {
                "method": match.group("method").upper(),
                "route_template": route,
                "parameter_keys": parameter_keys,
                "explicit_empty_parameter_branch_observed": empty_branch,
            }
        )
    if not calls:
        raise ValueError("no direct guild progression API calls observed")

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in calls:
        grouped.setdefault((row["method"], row["route_template"]), []).append(row)
    requests: list[dict[str, Any]] = []
    for (method, route), rows in sorted(grouped.items()):
        requests.append(
            {
                "method": method,
                "route_template": route,
                "occurrence_count": len(rows),
                "parameter_key_sets": [
                    list(keys) for keys in sorted({tuple(row["parameter_keys"]) for row in rows})
                ],
                "explicit_empty_parameter_branch_observed": any(
                    row["explicit_empty_parameter_branch_observed"] for row in rows
                ),
            }
        )

    methods = sorted({row["method"] for row in calls})
    rankings = next(
        (
            row
            for row in requests
            if row["method"] == "GET"
            and row["route_template"] == "/api/guilds/progression/rankings"
        ),
        None,
    )
    return {
        "api_base_url": API_BASE_URL,
        "api_client_binding_observed": True,
        "legacy_prefix_literal_occurrence_count": len(prefix_positions),
        "legacy_prefix_cache_exclusion_occurrence_count": cache_occurrences,
        "legacy_prefix_direct_request_occurrence_count": sum(
            row["route_template"] == LEGACY_PREFIX for row in calls
        ),
        "direct_progression_request_count": len(calls),
        "direct_progression_methods": methods,
        "direct_requests": requests,
        "post_request_observed": "POST" in methods,
        "bounded_rankings_get_contract_observed": bool(
            rankings and rankings["explicit_empty_parameter_branch_observed"]
        ),
    }


def review_guild_progression_frontend_contract(
    *,
    private_recovery_path: Path,
    raw_root: Path,
    receipt_output_path: Path,
) -> dict[str, Any]:
    recovery, recovery_body = load_json(private_recovery_path, "private asset recovery")
    summary = recovery.get("summary")
    if not isinstance(summary, dict) or summary.get("asset_download_completed") is not True:
        raise ValueError("private recovery does not prove asset download completion")
    payload_hash = recovery.get("asset_capture_payload_hash")
    if not isinstance(payload_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", payload_hash):
        raise ValueError("private recovery asset hash is missing or malformed")
    asset, _ = load_asset(raw_root, payload_hash)
    analysis = analyze_frontend_contract(asset.decode("utf-8", errors="ignore"))

    expected = {
        "legacy_prefix_literal_occurrence_count": 1,
        "legacy_prefix_cache_exclusion_occurrence_count": 1,
        "legacy_prefix_direct_request_occurrence_count": 0,
        "direct_progression_request_count": 4,
        "direct_progression_methods": ["GET"],
        "post_request_observed": False,
        "bounded_rankings_get_contract_observed": True,
    }
    for field, value in expected.items():
        if analysis[field] != value:
            raise ValueError(f"frontend progression contract mismatch: {field}")

    receipt = {
        "schema_version": 1,
        "review_kind": REVIEW_KIND,
        "review_version": REVIEW_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_private_recovery_name": private_recovery_path.name,
        "source_private_recovery_sha256": sha256(recovery_body),
        "source_asset_sha256": payload_hash,
        "frontend_contract": analysis,
        "summary": {
            "legacy_progression_prefix_is_cache_exclusion_only": True,
            "legacy_progression_prefix_is_direct_endpoint": False,
            "direct_progression_request_count": analysis["direct_progression_request_count"],
            "direct_progression_methods": analysis["direct_progression_methods"],
            "post_request_observed": False,
            "bounded_rankings_get_contract_observed": True,
            "ready_for_bounded_progression_rankings_probe": True,
            "ready_for_bounded_legacy_progression_prefix_probe": False,
            "network_requests_performed": False,
            "contains_raw_javascript": False,
            "contains_private_source_scalar_values": False,
        },
        "decision_boundary": {
            "status": "frontend_progression_request_contract_reviewed",
            "historical_helper_chain_superseded": True,
            "ready_for_bounded_progression_rankings_probe": True,
            "ready_for_bounded_legacy_progression_prefix_probe": False,
            "guild_api_route_semantics_verified": False,
            "pagination_semantics_verified": False,
            "termination_semantics_verified": False,
            "completeness_verified": False,
            "ready_for_full_guild_crawl": False,
            "planner_scoring_allowed": False,
        },
    }
    if property_names(receipt) & _FORBIDDEN_PUBLIC_FIELDS:
        raise ValueError("public frontend progression contract contains forbidden fields")
    write_json(receipt_output_path, receipt)
    return receipt


__all__ = ["analyze_frontend_contract", "review_guild_progression_frontend_contract"]
