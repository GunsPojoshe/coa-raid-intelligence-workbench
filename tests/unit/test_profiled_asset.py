from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from coa_workbench.collector.guild_identity_asset_profiled_recovery import (
    recover_guild_identity_asset_profiled,
)


def _write_json(path: Path, payload: dict[str, object]) -> bytes:
    body = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    path.write_bytes(body)
    return body


def _route_discoveries(tmp_path: Path) -> tuple[Path, Path]:
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
                    "error": "read timeout after 90 seconds",
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


def _diagnostics(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    public_recovery_path = tmp_path / "recovery.json"
    public_recovery_body = _write_json(public_recovery_path, {"kind": "public"})
    private_recovery_path = tmp_path / "recovery.private.json"
    private_recovery_body = _write_json(private_recovery_path, {"kind": "private"})

    private_diagnostic_path = tmp_path / "diagnostic.private.json"
    private_diagnostic_payload: dict[str, object] = {
        "schema_version": 1,
        "diagnostic_kind": "guild_identity_asset_transport_diagnostic_private",
        "diagnostic_version": "guild-identity-asset-transport-diagnostic-v1",
        "target_guild_label": "Argentum",
        "candidate_source_guild_id": 15,
        "asset_url": "https://coa.ascensionlogs.gg/_app/chunk.js",
        "selected_profile": "http1_1",
        "summary": {"contains_source_scalar_values": True},
    }
    private_diagnostic_body = _write_json(
        private_diagnostic_path, private_diagnostic_payload
    )

    public_diagnostic_path = tmp_path / "diagnostic.json"
    public_diagnostic_payload: dict[str, object] = {
        "schema_version": 1,
        "diagnostic_kind": "guild_identity_asset_transport_diagnostic",
        "diagnostic_version": "guild-identity-asset-transport-diagnostic-v1",
        "source_private_diagnostic_sha256": hashlib.sha256(
            private_diagnostic_body
        ).hexdigest(),
        "source_public_recovery_sha256": hashlib.sha256(
            public_recovery_body
        ).hexdigest(),
        "source_private_recovery_sha256": hashlib.sha256(
            private_recovery_body
        ).hexdigest(),
        "target": {
            "guild_label": "Argentum",
            "source_guild_id_published": False,
            "asset_url_published": False,
        },
        "attempts": [
            {
                "profile": "http1_1",
                "return_code": 63,
                "http_status": 200,
                "probe_bytes": 1655578,
                "transport_reached": True,
                "failure_class": None,
            }
        ],
        "probe": {"max_probe_bytes": 1048576},
        "integrity_checks": {
            "asset_url_https": True,
            "asset_url_same_origin": True,
            "credentials_not_supplied": True,
            "private_asset_recovery_sha256_verified": True,
            "probe_size_bounded": False,
            "profile_attempt_count_bounded": True,
            "public_asset_recovery_verified": True,
            "public_receipt_scalar_boundary_preserved": True,
            "range_probe_used": True,
            "redirects_disabled": True,
        },
        "summary": {
            "all_integrity_checks_passed": False,
            "contains_error_text": False,
            "contains_source_scalar_values": False,
            "selected_profile": "http1_1",
            "transport_profile_candidate_observed": True,
        },
    }
    _write_json(public_diagnostic_path, public_diagnostic_payload)
    return (
        public_diagnostic_path,
        private_diagnostic_path,
        public_recovery_path,
        private_recovery_path,
    )


class _Archive:
    def capture_bytes(self, body: bytes, **_kwargs):
        return SimpleNamespace(payload_hash=hashlib.sha256(body).hexdigest())


def _registry():
    return SimpleNamespace(
        base_url="https://coa.ascensionlogs.gg",
        source_code="ascension_logs",
    )


def test_profiled_recovery_uses_selected_profile_and_redacts_routes(
    tmp_path: Path,
) -> None:
    public_routes, private_routes = _route_discoveries(tmp_path)
    (
        public_diagnostic,
        private_diagnostic,
        public_recovery,
        private_recovery,
    ) = _diagnostics(tmp_path)
    commands: list[list[str]] = []

    def runner(command, **_kwargs):
        commands.append(list(command))
        output_path = Path(command[command.index("--output") + 1])
        output_path.write_bytes(
            b'const guildRoute = "/api/guilds/15/reports";'
            b'const publicRoute = "/api/reports/public";'
        )
        return SimpleNamespace(returncode=0, stdout="200", stderr="")

    receipt = recover_guild_identity_asset_profiled(
        _registry(),
        _Archive(),
        public_diagnostic_path=public_diagnostic,
        private_diagnostic_path=private_diagnostic,
        public_recovery_path=public_recovery,
        private_recovery_path=private_recovery,
        public_route_discovery_path=public_routes,
        private_route_discovery_path=private_routes,
        private_output_path=tmp_path / "profiled.private.json",
        receipt_output_path=tmp_path / "profiled.json",
        curl_executable="curl.exe",
        runner=runner,
    )

    assert "--http1.1" in commands[0]
    assert receipt["transport"]["profile"] == "http1_1"
    assert receipt["route_inventory"]["guild_api_route_shapes"] == [
        "/api/guilds/{guild_id}/reports"
    ]
    assert receipt["summary"]["all_integrity_checks_passed"] is True
    assert receipt["decision_boundary"]["ready_for_guild_api_route_review"] is True
    assert receipt["decision_boundary"]["guild_identity_verified"] is False
    assert receipt["decision_boundary"]["ready_for_guild_filtering"] is False
    assert receipt["target"]["source_guild_id_published"] is False

    private_payload = json.loads((tmp_path / "profiled.private.json").read_text())
    assert private_payload["candidate_source_guild_id"] == 15
    assert private_payload["selected_transport_profile"] == "http1_1"


def test_profiled_recovery_rejects_private_diagnostic_hash_mismatch(
    tmp_path: Path,
) -> None:
    public_routes, private_routes = _route_discoveries(tmp_path)
    (
        public_diagnostic,
        private_diagnostic,
        public_recovery,
        private_recovery,
    ) = _diagnostics(tmp_path)
    private_diagnostic.write_text(private_diagnostic.read_text() + " ")

    with pytest.raises(ValueError, match="private transport diagnostic SHA-256"):
        recover_guild_identity_asset_profiled(
            _registry(),
            _Archive(),
            public_diagnostic_path=public_diagnostic,
            private_diagnostic_path=private_diagnostic,
            public_recovery_path=public_recovery,
            private_recovery_path=private_recovery,
            public_route_discovery_path=public_routes,
            private_route_discovery_path=private_routes,
            private_output_path=tmp_path / "profiled.private.json",
            receipt_output_path=tmp_path / "profiled.json",
            curl_executable="curl.exe",
            runner=lambda *_args, **_kwargs: pytest.fail("runner must not be called"),
        )
