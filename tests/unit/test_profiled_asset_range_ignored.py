from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from coa_workbench.collector.guild_identity_asset_profiled_recovery import (
    _validate_diagnostic,
)


def _write_json(path: Path, payload: dict[str, object]) -> bytes:
    body = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    path.write_bytes(body)
    return body


def _diagnostic_packet(
    tmp_path: Path, *, return_code: int
) -> tuple[dict[str, object], dict[str, object], bytes, Path, Path]:
    public_recovery_path = tmp_path / "recovery.json"
    public_recovery_body = _write_json(public_recovery_path, {"kind": "public"})
    private_recovery_path = tmp_path / "recovery.private.json"
    private_recovery_body = _write_json(private_recovery_path, {"kind": "private"})

    private_diagnostic: dict[str, object] = {
        "schema_version": 1,
        "diagnostic_kind": "guild_identity_asset_transport_diagnostic_private",
        "diagnostic_version": "guild-identity-asset-transport-diagnostic-v1",
        "target_guild_label": "Argentum",
        "candidate_source_guild_id": 15,
        "asset_url": "https://coa.ascensionlogs.gg/_app/chunk.js",
        "selected_profile": "http1_1",
        "summary": {"contains_source_scalar_values": True},
    }
    private_diagnostic_body = (
        json.dumps(private_diagnostic, indent=2, sort_keys=True) + "\n"
    ).encode()

    public_diagnostic: dict[str, object] = {
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
                "return_code": return_code,
                "http_status": 200,
                "probe_bytes": 3881146,
                "transport_reached": True,
                "failure_class": None,
            }
        ],
        "probe": {"max_probe_bytes": 2097152},
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
    return (
        public_diagnostic,
        private_diagnostic,
        private_diagnostic_body,
        public_recovery_path,
        private_recovery_path,
    )


def test_completed_range_ignored_diagnostic_is_accepted(tmp_path: Path) -> None:
    (
        public_diagnostic,
        private_diagnostic,
        private_diagnostic_body,
        public_recovery_path,
        private_recovery_path,
    ) = _diagnostic_packet(tmp_path, return_code=0)

    selected_profile, guild_id, asset_url, _, _ = _validate_diagnostic(
        public_diagnostic,
        private_diagnostic,
        private_diagnostic_body=private_diagnostic_body,
        public_recovery_path=public_recovery_path,
        private_recovery_path=private_recovery_path,
        expected_guild_label="Argentum",
    )

    assert selected_profile == "http1_1"
    assert guild_id == 15
    assert asset_url.endswith("/_app/chunk.js")


def test_range_ignored_diagnostic_rejects_unexpected_curl_failure(
    tmp_path: Path,
) -> None:
    (
        public_diagnostic,
        private_diagnostic,
        private_diagnostic_body,
        public_recovery_path,
        private_recovery_path,
    ) = _diagnostic_packet(tmp_path, return_code=18)

    with pytest.raises(ValueError, match="curl code 0 or 63"):
        _validate_diagnostic(
            public_diagnostic,
            private_diagnostic,
            private_diagnostic_body=private_diagnostic_body,
            public_recovery_path=public_recovery_path,
            private_recovery_path=private_recovery_path,
            expected_guild_label="Argentum",
        )
