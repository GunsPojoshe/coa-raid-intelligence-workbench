from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.collector.upstream_lua_evidence import (
    extract_lua_file_evidence,
    review_lua_source_tree,
)


def test_extract_lua_file_evidence_ignores_comments_and_string_examples() -> None:
    content = b'''-- C_Fake.ShouldNotCount()\n-- ALC.RegisterEvent("COMMENT_EVENT", handler)\nlocal example = "C_String.NotACall()"\nlocal info = C_MythicPlus.GetActiveKeystoneInfo()\nlocal hero = C_Player:IsHero()\nlocal name = GetInstanceInfo()\nALC.RegisterEvent("PLAYER_REGEN_DISABLED", handler)\npcall(ALC.RegisterEvent, "MYTHIC_PLUS_STARTED", handler)\nlocal record = { stream = "keystone", event_type = "complete" }\nlocal marker = "[[ALC_KS_v1_%s_%s]]"\n'''

    evidence = extract_lua_file_evidence(content, relative_path="Capture/KeystoneScan.lua")

    assert evidence.api_namespaces == ("C_MythicPlus", "C_Player")
    assert evidence.api_calls == (
        "C_MythicPlus.GetActiveKeystoneInfo",
        "C_Player.IsHero",
        "GetInstanceInfo",
    )
    assert evidence.registered_events == ("MYTHIC_PLUS_STARTED", "PLAYER_REGEN_DISABLED")
    assert "COMMENT_EVENT" not in evidence.event_like_literals
    assert evidence.stream_literals == ("keystone",)
    assert evidence.event_type_literals == ("complete",)
    assert evidence.transport_literals == ("[[ALC_KS_v1_%s_%s]]",)


def test_extract_lua_file_evidence_ignores_long_comments_and_long_strings() -> None:
    content = b'''--[[\nC_MythicPlus.CommentOnly()\nALC.RegisterEvent("BLOCK_EVENT", handler)\n]]\nlocal example = [=[C_MythicPlus.StringOnly()]=]\nlocal active = C_Manastorm.IsInManastorm()\n'''

    evidence = extract_lua_file_evidence(content, relative_path="Capture/ManastormScan.lua")

    assert evidence.api_namespaces == ("C_Manastorm",)
    assert evidence.api_calls == ("C_Manastorm.IsInManastorm",)
    assert evidence.registered_events == ()
    assert "BLOCK_EVENT" not in evidence.event_like_literals


def test_review_lua_source_tree_is_deterministic_and_does_not_publish_local_root(
    tmp_path: Path,
) -> None:
    root = tmp_path / "Private Operator" / "AscensionLogsCompanion"
    (root / "Capture").mkdir(parents=True)
    (root / "Capture" / "B.lua").write_text(
        'ALC.RegisterEvent("UNIT_PET", handler)\nlocal x = UnitGUID("player")\n',
        encoding="utf-8",
    )
    (root / "Capture" / "A.lua").write_text(
        'local x = C_CharacterAdvancement.GetActiveSpecID()\n',
        encoding="utf-8",
    )

    review = review_lua_source_tree(
        root,
        source_code="ascension_logs_companion",
        revision="ABCDEF1",
    )

    assert review["source"] == {
        "source_code": "ascension_logs_companion",
        "revision": "abcdef1",
        "file_count": 2,
        "source_root_included": False,
        "source_text_included": False,
        "network_requests_performed": False,
    }
    assert [item["relative_path"] for item in review["files"]] == [
        "Capture/A.lua",
        "Capture/B.lua",
    ]
    assert review["aggregate"]["api_namespaces"] == ["C_CharacterAdvancement"]
    assert review["aggregate"]["registered_events"] == ["UNIT_PET"]
    assert review["interpretation"]["inventory_is_semantic_proof"] is False

    rendered = json.dumps(review, sort_keys=True)
    assert str(root) not in rendered
    assert "Private Operator" not in rendered


def test_review_lua_source_tree_requires_public_source_code_and_hex_revision(tmp_path: Path) -> None:
    root = tmp_path / "source"
    root.mkdir()

    with pytest.raises(ValueError, match="source_code"):
        review_lua_source_tree(root, source_code="Private Source", revision="abcdef1")

    with pytest.raises(ValueError, match="revision"):
        review_lua_source_tree(root, source_code="public_source", revision="main")


def test_extract_lua_file_evidence_rejects_unsafe_relative_path() -> None:
    with pytest.raises(ValueError, match="relative_path"):
        extract_lua_file_evidence(b"", relative_path="../private.lua")
