from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from coa_workbench.collector import guild_identity_asset_transport_diagnostic as module


def _write_json(path: Path, payload: dict[str, object]) -> bytes:
    body = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    path.write_bytes(body)
    return body


def _recoveries(tmp_path: Path) -> tuple[Path, Path]:
    private_path = tmp_path / "recovery.private.json"
    private_payload: dict[str, object] = {
        "schema_version": 1,
        "recovery_kind": "guild_identity_asset_recovery_private",
        "recovery_version": "guild-identity-asset-recovery-v1",
        "target_guild_label": "Argentum",
        "candidate_source_guild_id": 15,
        "asset_url": "https://coa.ascensionlogs.gg/_app/chunk.js",
        "curl_return_code": 35,
        "http_status": 0,
        "failure_class": "network_or_tls_failure",
        "summary": {
            "asset_download_completed": False,
            "contains_source_scalar_values": True,
        },
    }
    private_body = _write_json(private_path, private_payload)

    public_path = tmp_path / "recovery.json"
    public_payload: dict[str, object] = {
        "schema_version": 1,
        "recovery_kind": "guild_identity_asset_recovery",
        "recovery_version": "guild-identity-asset-recovery-v1",
        "source_private_recovery_sha256": hashlib.sha256(private_body).hexdigest(),
        "target": {
            "guild_label": "Argentum",
            "source_guild_id_published": False,
            "asset_url_published": False,
        },
        "transport": {
            "kind": "curl",
            "return_code": 35,
            "http_status": 0,
            "failure_class": "network_or_tls_failure",
            "redirects_allowed": False,
            "credentials_supplied": False,
            "contains_error_text": False,
        },
        "summary": {
            "asset_download_completed": False,
            "asset_bytes": 0,
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


def _registry():
    return SimpleNamespace(base_url="https://coa.ascensionlogs.gg")


def test_diagnostic_selects_first_profile_that_reaches_http(tmp_path: Path) -> None:
    public_path, private_path = _recoveries(tmp_path)
    calls: list[list[str]] = []

    def runner(command, **_kwargs):
        calls.append(command)
        assert "--location" not in command
        assert "--cookie" not in command
        assert "--header" not in command
        assert command[command.index("--proto") + 1] == "=https"
        assert command[command.index("--max-redirs") + 1] == "0"
        assert command[command.index("--range") + 1] == "0-0"
        if len(calls) == 1:
            return SimpleNamespace(returncode=35, stdout="000", stderr="TLS failure")
        output_path = Path(command[command.index("--output") + 1])
        output_path.write_bytes(b"x")
        return SimpleNamespace(returncode=0, stdout="206", stderr="")

    receipt = module.diagnose_guild_identity_asset_transport(
        _registry(),
        public_recovery_path=public_path,
        private_recovery_path=private_path,
        private_output_path=tmp_path / "diagnostic.private.json",
        receipt_output_path=tmp_path / "diagnostic.json",
        curl_executable="curl.exe",
        runner=runner,
    )

    assert receipt["summary"]["selected_profile"] == "ipv4_http1_1"
    assert receipt["summary"]["attempt_count"] == 2
    assert receipt["attempts"][0]["failure_class"] == "tls_handshake_failure"
    assert receipt["attempts"][1]["transport_reached"] is True
    assert receipt["target"]["source_guild_id_published"] is False
    assert receipt["target"]["asset_url_published"] is False
    assert receipt["summary"]["contains_source_scalar_values"] is False
    assert receipt["summary"]["contains_error_text"] is False
    assert receipt["decision_boundary"]["ready_for_profiled_asset_recovery"] is True
    assert receipt["decision_boundary"]["guild_identity_verified"] is False
    assert receipt["decision_boundary"]["ready_for_guild_filtering"] is False

    public_text = json.dumps(receipt)
    assert "/_app/chunk.js" not in public_text
    assert "TLS failure" not in public_text


def test_diagnostic_records_all_failed_profiles_without_promotion(tmp_path: Path) -> None:
    public_path, private_path = _recoveries(tmp_path)

    def runner(_command, **_kwargs):
        return SimpleNamespace(returncode=35, stdout="000", stderr="TLS failure")

    receipt = module.diagnose_guild_identity_asset_transport(
        _registry(),
        public_recovery_path=public_path,
        private_recovery_path=private_path,
        private_output_path=tmp_path / "diagnostic.private.json",
        receipt_output_path=tmp_path / "diagnostic.json",
        curl_executable="curl.exe",
        runner=runner,
    )

    assert receipt["summary"]["attempt_count"] == len(module._TRANSPORT_PROFILES)
    assert receipt["summary"]["selected_profile"] is None
    assert receipt["decision_boundary"]["ready_for_profiled_asset_recovery"] is False
    assert receipt["decision_boundary"]["guild_api_route_candidates_observed"] is False
    assert receipt["decision_boundary"]["guild_identity_verified"] is False
    assert all(
        attempt["failure_class"] == "tls_handshake_failure"
        for attempt in receipt["attempts"]
    )


def test_diagnostic_rejects_private_recovery_hash_mismatch(tmp_path: Path) -> None:
    public_path, private_path = _recoveries(tmp_path)
    private_path.write_text(private_path.read_text() + " ")

    with pytest.raises(ValueError, match="private asset recovery SHA-256"):
        module.diagnose_guild_identity_asset_transport(
            _registry(),
            public_recovery_path=public_path,
            private_recovery_path=private_path,
            private_output_path=tmp_path / "diagnostic.private.json",
            receipt_output_path=tmp_path / "diagnostic.json",
            curl_executable="curl.exe",
            runner=lambda *_args, **_kwargs: pytest.fail("runner must not be called"),
        )
