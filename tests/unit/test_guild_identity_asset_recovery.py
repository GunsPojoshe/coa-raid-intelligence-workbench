from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from coa_workbench.collector import guild_identity_asset_recovery as module


def _write_json(path: Path, payload: dict[str, object]) -> bytes:
    body = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    path.write_bytes(body)
    return body


def _discoveries(tmp_path: Path) -> tuple[Path, Path]:
    private_path = tmp_path / "routes.private.json"
    private_payload: dict[str, object] = {
        "schema_version": 1,
        "discovery_kind": "guild_identity_route_discovery_private",
        "discovery_version": "guild-identity-route-discovery-v2",
        "target_guild_label": "Argentum",
        "candidate_source_guild_id": 15,
        "page_capture": {
            "assets": [
                {
                    "url": "https://coa.ascensionlogs.gg/_app/chunk.js",
                    "content_type": "application/javascript",
                    "capture": None,
                    "error": "read timeout after 90 seconds (attempt 2/2)",
                }
            ]
        },
        "summary": {
            "failed_asset_count": 1,
            "contains_source_scalar_values": True,
        },
    }
    private_body = _write_json(private_path, private_payload)

    public_path = tmp_path / "routes.json"
    public_payload: dict[str, object] = {
        "schema_version": 1,
        "discovery_kind": "guild_identity_route_discovery",
        "discovery_version": "guild-identity-route-discovery-v2",
        "source_private_discovery_sha256": hashlib.sha256(private_body).hexdigest(),
        "target": {
            "guild_label": "Argentum",
            "source_guild_id_published": False,
        },
        "asset_failure_summary": {
            "failed_asset_count": 1,
            "failure_class_counts": {"timeout": 1},
            "contains_asset_urls": False,
            "contains_error_text": False,
        },
        "summary": {
            "failed_asset_count": 1,
            "all_integrity_checks_passed": True,
            "contains_source_scalar_values": False,
        },
        "decision_boundary": {
            "snapshot_internal_identity_consistent": True,
            "guild_api_route_candidates_observed": False,
            "guild_api_route_semantics_verified": False,
            "independent_source_identity_verified": False,
            "guild_identity_verified": False,
            "ready_for_guild_api_route_review": False,
            "ready_for_guild_filtering": False,
            "ready_for_full_guild_crawl": False,
            "planner_scoring_allowed": False,
        },
    }
    _write_json(public_path, public_payload)
    return public_path, private_path


class _Archive:
    def capture_bytes(self, body: bytes, **_kwargs):
        return SimpleNamespace(payload_hash=hashlib.sha256(body).hexdigest())


def _registry():
    return SimpleNamespace(
        base_url="https://coa.ascensionlogs.gg",
        source_code="ascension_logs",
    )


def test_recovery_redacts_guild_id_and_preserves_boundaries(tmp_path: Path) -> None:
    public_path, private_path = _discoveries(tmp_path)

    def runner(command, **_kwargs):
        output_path = Path(command[command.index("--output") + 1])
        output_path.write_bytes(
            b'const guildRoute = "/api/guilds/15/reports";'
            b'const publicRoute = "/api/reports/public";'
        )
        return SimpleNamespace(returncode=0, stdout="200", stderr="")

    receipt = module.recover_guild_identity_asset(
        _registry(),
        _Archive(),
        public_route_discovery_path=public_path,
        private_route_discovery_path=private_path,
        private_output_path=tmp_path / "recovery.private.json",
        receipt_output_path=tmp_path / "recovery.json",
        curl_executable="curl.exe",
        runner=runner,
    )

    assert receipt["route_inventory"]["guild_api_route_shapes"] == [
        "/api/guilds/{guild_id}/reports"
    ]
    assert "/15/" not in json.dumps(receipt["route_inventory"])
    assert receipt["target"]["source_guild_id_published"] is False
    assert receipt["target"]["asset_url_published"] is False
    assert receipt["summary"]["contains_source_scalar_values"] is False
    assert receipt["decision_boundary"]["ready_for_guild_api_route_review"] is True
    assert receipt["decision_boundary"]["guild_api_route_semantics_verified"] is False
    assert receipt["decision_boundary"]["independent_source_identity_verified"] is False
    assert receipt["decision_boundary"]["guild_identity_verified"] is False
    assert receipt["decision_boundary"]["ready_for_guild_filtering"] is False

    private_payload = json.loads((tmp_path / "recovery.private.json").read_text())
    assert private_payload["candidate_source_guild_id"] == 15
    assert private_payload["asset_url"].endswith("/_app/chunk.js")
    assert private_payload["summary"]["contains_source_scalar_values"] is True


def test_recovery_records_transport_timeout_without_promoting(tmp_path: Path) -> None:
    public_path, private_path = _discoveries(tmp_path)

    def runner(_command, **_kwargs):
        return SimpleNamespace(returncode=28, stdout="000", stderr="timed out")

    receipt = module.recover_guild_identity_asset(
        _registry(),
        _Archive(),
        public_route_discovery_path=public_path,
        private_route_discovery_path=private_path,
        private_output_path=tmp_path / "recovery.private.json",
        receipt_output_path=tmp_path / "recovery.json",
        curl_executable="curl.exe",
        runner=runner,
    )

    assert receipt["transport"]["failure_class"] == "timeout"
    assert receipt["transport"]["contains_error_text"] is False
    assert receipt["summary"]["asset_download_completed"] is False
    assert receipt["decision_boundary"]["ready_for_guild_api_route_review"] is False
    assert receipt["decision_boundary"]["guild_identity_verified"] is False
    assert receipt["decision_boundary"]["ready_for_guild_filtering"] is False


def test_recovery_rejects_private_discovery_hash_mismatch(tmp_path: Path) -> None:
    public_path, private_path = _discoveries(tmp_path)
    private_path.write_text(private_path.read_text() + " ")

    with pytest.raises(ValueError, match="private route discovery SHA-256"):
        module.recover_guild_identity_asset(
            _registry(),
            _Archive(),
            public_route_discovery_path=public_path,
            private_route_discovery_path=private_path,
            private_output_path=tmp_path / "recovery.private.json",
            receipt_output_path=tmp_path / "recovery.json",
            curl_executable="curl.exe",
            runner=lambda *_args, **_kwargs: pytest.fail("runner must not be called"),
        )
