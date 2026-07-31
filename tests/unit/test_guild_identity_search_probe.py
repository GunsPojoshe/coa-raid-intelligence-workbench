from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from coa_workbench.collector.guild_identity_search_probe import (
    capture_guild_identity_search_probe,
)


def _write_json(path: Path, payload: dict[str, object]) -> bytes:
    body = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    path.write_bytes(body)
    return body


def _recovery_pair(
    tmp_path: Path,
    *,
    include_search_route: bool = True,
) -> tuple[Path, Path]:
    private_path = tmp_path / "profiled.private.json"
    private_payload: dict[str, object] = {
        "schema_version": 1,
        "recovery_kind": "guild_identity_asset_profiled_recovery_private",
        "recovery_version": "guild-identity-asset-profiled-recovery-v1",
        "target_guild_label": "Argentum",
        "candidate_source_guild_id": 15,
        "selected_transport_profile": "http1_1",
    }
    private_body = _write_json(private_path, private_payload)

    shapes = ["/api/guilds/progression", "/api/guilds/search?q=<value>"]
    if include_search_route:
        shapes.append("/api/guilds/search?q=<value>&limit=<value>")
    public_path = tmp_path / "profiled.json"
    public_payload: dict[str, object] = {
        "schema_version": 1,
        "recovery_kind": "guild_identity_asset_profiled_recovery",
        "recovery_version": "guild-identity-asset-profiled-recovery-v1",
        "source_private_recovery_sha256": hashlib.sha256(private_body).hexdigest(),
        "target": {
            "guild_label": "Argentum",
            "source_guild_id_published": False,
            "asset_url_published": False,
        },
        "summary": {
            "all_integrity_checks_passed": True,
            "contains_source_scalar_values": False,
            "asset_download_completed": True,
        },
        "route_inventory": {"guild_api_route_shapes": shapes},
        "decision_boundary": {
            "guild_api_route_candidates_observed": True,
            "ready_for_guild_api_route_review": True,
            "guild_api_route_semantics_verified": False,
            "independent_source_identity_verified": False,
            "guild_identity_verified": False,
            "ready_for_guild_filtering": False,
            "ready_for_full_guild_crawl": False,
            "planner_scoring_allowed": False,
        },
    }
    _write_json(public_path, public_payload)
    return public_path, private_path


class _Archive:
    def capture_bytes(self, body: bytes, **_kwargs):
        payload_hash = hashlib.sha256(body).hexdigest()
        return SimpleNamespace(
            raw_id=f"raw-{payload_hash[:8]}",
            observation_id=f"obs-{payload_hash[:8]}",
            payload_hash=payload_hash,
            schema_fingerprint="schema-fingerprint",
            bytes_uncompressed=len(body),
        )


def _registry():
    return SimpleNamespace(
        base_url="https://coa.ascensionlogs.gg",
        source_code="ascension_logs",
    )


def _runner_for(payload: object, commands: list[list[str]]):
    def runner(command, **_kwargs):
        commands.append(list(command))
        output_path = Path(command[command.index("--output") + 1])
        output_path.write_text(json.dumps(payload), encoding="utf-8")
        return SimpleNamespace(
            returncode=0,
            stdout="200\napplication/json",
            stderr="",
        )

    return runner


def test_search_probe_observes_one_to_one_identity_candidate_without_public_scalars(
    tmp_path: Path,
) -> None:
    public_recovery, private_recovery = _recovery_pair(tmp_path)
    commands: list[list[str]] = []
    public_output = tmp_path / "probe.json"
    private_output = tmp_path / "probe.private.json"

    receipt = capture_guild_identity_search_probe(
        _registry(),
        _Archive(),
        public_profiled_recovery_path=public_recovery,
        private_profiled_recovery_path=private_recovery,
        private_output_path=private_output,
        receipt_output_path=public_output,
        curl_executable="curl.exe",
        runner=_runner_for(
            {
                "success": True,
                "guilds": [
                    {"id": 15, "name": "Argentum", "memberCount": 42},
                ],
            },
            commands,
        ),
    )

    assert "--http1.1" in commands[0]
    assert "q=Argentum" in commands[0][-1]
    assert "limit=25" in commands[0][-1]
    assert receipt["response"]["completed"] is True
    assert receipt["match_review"]["exact_label_object_count"] == 1
    assert receipt["match_review"]["source_id_match_object_count"] == 1
    assert receipt["match_review"]["one_to_one_identity_candidate"] is True
    assert receipt["decision_boundary"]["ready_for_guild_search_mapping_review"] is True
    assert receipt["decision_boundary"]["independent_source_identity_candidate_observed"] is True
    assert receipt["decision_boundary"]["independent_source_identity_verified"] is False
    assert receipt["decision_boundary"]["guild_identity_verified"] is False
    assert receipt["decision_boundary"]["ready_for_guild_filtering"] is False
    assert receipt["summary"]["contains_source_scalar_values"] is False
    assert receipt["target"]["source_guild_id_published"] is False
    assert "id_like_values" not in receipt["match_review"]

    private_payload = json.loads(private_output.read_text(encoding="utf-8"))
    assert private_payload["candidate_source_guild_id"] == 15
    assert private_payload["matched_objects"][0]["id_like_values"] == {"id": 15}


def test_search_probe_preserves_review_boundary_for_mismatched_id(
    tmp_path: Path,
) -> None:
    public_recovery, private_recovery = _recovery_pair(tmp_path)
    receipt = capture_guild_identity_search_probe(
        _registry(),
        _Archive(),
        public_profiled_recovery_path=public_recovery,
        private_profiled_recovery_path=private_recovery,
        private_output_path=tmp_path / "probe.private.json",
        receipt_output_path=tmp_path / "probe.json",
        curl_executable="curl.exe",
        runner=_runner_for(
            {"guilds": [{"id": 99, "name": "Argentum"}]},
            [],
        ),
    )

    assert receipt["match_review"]["exact_label_object_count"] == 1
    assert receipt["match_review"]["source_id_match_object_count"] == 0
    assert receipt["match_review"]["one_to_one_identity_candidate"] is False
    assert receipt["decision_boundary"]["guild_search_route_semantics_candidate_observed"] is True
    assert receipt["decision_boundary"]["independent_source_identity_candidate_observed"] is False
    assert receipt["decision_boundary"]["guild_identity_verified"] is False


def test_search_probe_rejects_private_recovery_hash_mismatch_before_network(
    tmp_path: Path,
) -> None:
    public_recovery, private_recovery = _recovery_pair(tmp_path)
    private_recovery.write_text(private_recovery.read_text(encoding="utf-8") + " ")

    with pytest.raises(ValueError, match="private profiled recovery SHA-256 mismatch"):
        capture_guild_identity_search_probe(
            _registry(),
            _Archive(),
            public_profiled_recovery_path=public_recovery,
            private_profiled_recovery_path=private_recovery,
            private_output_path=tmp_path / "probe.private.json",
            receipt_output_path=tmp_path / "probe.json",
            curl_executable="curl.exe",
            runner=lambda *_args, **_kwargs: pytest.fail("runner must not be called"),
        )


def test_search_probe_rejects_unrecovered_search_limit_route_before_network(
    tmp_path: Path,
) -> None:
    public_recovery, private_recovery = _recovery_pair(
        tmp_path,
        include_search_route=False,
    )

    with pytest.raises(ValueError, match="bounded guild search route shape was not recovered"):
        capture_guild_identity_search_probe(
            _registry(),
            _Archive(),
            public_profiled_recovery_path=public_recovery,
            private_profiled_recovery_path=private_recovery,
            private_output_path=tmp_path / "probe.private.json",
            receipt_output_path=tmp_path / "probe.json",
            curl_executable="curl.exe",
            runner=lambda *_args, **_kwargs: pytest.fail("runner must not be called"),
        )
