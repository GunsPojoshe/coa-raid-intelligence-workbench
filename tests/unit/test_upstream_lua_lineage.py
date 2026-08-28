from __future__ import annotations

from pathlib import Path

import pytest

from coa_workbench.collector.upstream_lua_lineage import (
    extract_lua_file_lineage,
    review_lua_lineage_tree,
)


def test_ci_instance_lineage_expands_helper_to_get_instance_info() -> None:
    content = b"""-- GetInstanceInfo() in comments must not count
local function instanceInfo()
    local name, instType, diffIdx, diffName, maxPlayers, playerDiff, isDynamic, mapId = GetInstanceInfo()
    local out = {
        name = name,
        instance_type = instType,
        difficulty_index = diffIdx,
        difficulty_name = diffName,
        player_difficulty = playerDiff,
        map_id = mapId,
    }
    return out
end
function L.buildLocalCI(sessionId)
    local ci = {
        schema_version = 7,
        instance = instanceInfo(),
    }
    return ci
end
"""
    review = extract_lua_file_lineage(content, relative_path="Capture/LocalScan.lua")
    by_path = {item["field_path"]: item for item in review["field_lineage"]}

    assert by_path["instance.difficulty_index"]["source_identifier"] == "GetInstanceInfo"
    assert by_path["instance.difficulty_name"]["source_identifier"] == "GetInstanceInfo"
    assert by_path["instance.player_difficulty"]["source_identifier"] == "GetInstanceInfo"
    assert by_path["instance.map_id"]["source_identifier"] == "GetInstanceInfo"
    assert by_path["instance.difficulty_index"]["record_code"] == "ci"
    assert by_path["instance.difficulty_index"]["via_functions"] == (
        "L.buildLocalCI",
        "instanceInfo",
    )


def test_telemetry_map_lineage_expands_return_table() -> None:
    content = b"""local function mapInfo()
    local name, instType, diffIdx, diffName = GetInstanceInfo()
    return {
        instance_name = name,
        instance_type = instType,
        difficulty_index = diffIdx,
        difficulty_name = diffName,
    }
end
function T.snapshot(reason)
    local payload = {
        stream = "telemetry",
        event_type = "encounter_snapshot",
        map = mapInfo(),
    }
    enqueuePayload(payload)
end
"""
    review = extract_lua_file_lineage(content, relative_path="Capture/Telemetry.lua")
    by_path = {item["field_path"]: item for item in review["field_lineage"]}

    assert by_path["map.difficulty_index"]["record_code"] == "telemetry"
    assert by_path["map.difficulty_index"]["source_identifier"] == "GetInstanceInfo"
    assert by_path["stream"]["source_kind"] == "literal"


def test_inline_helpers_and_post_constructor_assignments_are_visible() -> None:
    content = b"""local function playerInfo()
    local name = UnitName("player")
    return { name = name, guid = UnitGUID("player") }
end
local function primaryStat()
    local ok, stat = pcall(C_PrimaryStat.GetActivePrimaryStat, C_PrimaryStat)
    if not ok then return nil end
    return { id = stat }
end
function L.buildLocalCI()
    local ci = { player = playerInfo() }
    ci.primary_stat = primaryStat()
    return ci
end
"""
    review = extract_lua_file_lineage(content, relative_path="Capture/LocalScan.lua")
    by_path = {item["field_path"]: item for item in review["field_lineage"]}

    assert by_path["player.name"]["source_identifier"] == "UnitName"
    assert by_path["player.guid"]["source_identifier"] == "UnitGUID"
    assert by_path["primary_stat.id"]["source_identifier"] == (
        "C_PrimaryStat.GetActivePrimaryStat"
    )


def test_review_tree_does_not_publish_local_root(tmp_path: Path) -> None:
    root = tmp_path / "Private Operator" / "upstream"
    (root / "Capture").mkdir(parents=True)
    (root / "Capture" / "Telemetry.lua").write_text(
        'function T.snapshot()\nlocal payload = { stream = "telemetry", event_type = "x" }\nend\n',
        encoding="utf-8",
    )

    review = review_lua_lineage_tree(
        root,
        source_code="ascension_logs_companion",
        revision="ABCDEF1",
    )

    assert review["source"]["source_root_included"] is False
    assert review["source"]["network_requests_performed"] is False
    assert review["aggregate"]["record_codes"] == ["telemetry"]
    assert "Private Operator" not in str(review)
    assert review["interpretation"]["lineage_is_backend_semantic_proof"] is False


def test_extract_lua_file_lineage_rejects_unsafe_path() -> None:
    with pytest.raises(ValueError, match="relative_path"):
        extract_lua_file_lineage(b"", relative_path="../private.lua")
