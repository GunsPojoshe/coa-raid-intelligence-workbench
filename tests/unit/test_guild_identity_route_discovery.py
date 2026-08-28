from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from coa_workbench.collector import guild_identity_route_discovery as module


def _write_json(path: Path, payload: dict[str, object]) -> bytes:
    body = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    path.write_bytes(body)
    return body


def _reviews(tmp_path: Path) -> tuple[Path, Path]:
    private_path = tmp_path / "snapshot.private.json"
    private_payload: dict[str, object] = {
        "schema_version": 1,
        "review_kind": "guild_identity_snapshot_private_review",
        "review_version": "guild-identity-snapshot-review-v1",
        "target_guild_label": "Argentum",
        "candidate_source_guild_id": 15,
        "source_private_manifest_sha256": "a" * 64,
        "source_public_manifest_receipt_sha256": "b" * 64,
        "summary": {"contains_source_scalar_values": True},
        "decision_boundary": {
            "snapshot_internal_identity_consistent": True,
            "guild_identity_verified": False,
        },
    }
    private_body = _write_json(private_path, private_payload)

    public_path = tmp_path / "snapshot.json"
    public_payload: dict[str, object] = {
        "schema_version": 1,
        "review_kind": "guild_identity_snapshot_review",
        "review_version": "guild-identity-snapshot-review-v1",
        "source_private_review_sha256": hashlib.sha256(private_body).hexdigest(),
        "source_private_manifest_sha256": "a" * 64,
        "source_public_manifest_receipt_sha256": "b" * 64,
        "target": {
            "guild_label": "Argentum",
            "source_guild_id_published": False,
        },
        "summary": {
            "all_integrity_checks_passed": True,
            "contains_source_scalar_values": False,
        },
        "decision_boundary": {
            "snapshot_internal_identity_consistent": True,
            "ready_for_independent_source_identity_review": True,
            "independent_source_identity_verified": False,
            "guild_identity_verified": False,
            "ready_for_guild_filtering": False,
            "ready_for_full_guild_crawl": False,
            "planner_scoring_allowed": False,
        },
    }
    _write_json(public_path, public_payload)
    return public_path, private_path


def _capture_result(route_candidates: tuple[str, ...]) -> SimpleNamespace:
    page_capture = SimpleNamespace(payload_hash="c" * 64)
    asset_capture = SimpleNamespace(payload_hash="d" * 64)
    asset = SimpleNamespace(
        url="https://coa.ascensionlogs.gg/_app/chunk.js",
        status=200,
        capture=asset_capture,
        api_route_candidates=route_candidates,
        error=None,
    )
    return SimpleNamespace(
        status=200,
        capture=page_capture,
        assets=(asset,),
        embedded_json=(),
        error=None,
    )


def test_discovery_redacts_candidate_id_and_preserves_boundaries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    public_path, private_path = _reviews(tmp_path)
    result = _capture_result(("/api/guilds/15/reports", "/api/reports/public"))
    monkeypatch.setattr(module, "_capture_one_page", lambda **_kwargs: result)
    monkeypatch.setattr(module, "_archived_capture_route_candidates", lambda _capture: ())
    monkeypatch.setattr(
        module,
        "build_page_capture_to_dict",
        lambda _result: {"private": True},
    )

    receipt = module.discover_guild_identity_route_candidates(
        SimpleNamespace(base_url="https://coa.ascensionlogs.gg"),
        object(),
        public_snapshot_review_path=public_path,
        private_snapshot_review_path=private_path,
        private_output_path=tmp_path / "routes.private.json",
        receipt_output_path=tmp_path / "routes.json",
    )

    assert receipt["discovery_version"] == "guild-identity-route-discovery-v2"
    assert receipt["route_inventory"]["guild_api_route_shapes"] == [
        "/api/guilds/{guild_id}/reports"
    ]
    assert receipt["route_inventory"]["candidate_source_counts"] == {
        "page_html": 0,
        "embedded_json": 0,
        "assets": 2,
    }
    assert "/15/" not in json.dumps(receipt["route_inventory"])
    assert receipt["target"]["source_guild_id_published"] is False
    assert receipt["summary"]["contains_source_scalar_values"] is False
    assert receipt["decision_boundary"]["ready_for_guild_api_route_review"] is True
    assert receipt["decision_boundary"]["guild_api_route_semantics_verified"] is False
    assert receipt["decision_boundary"]["independent_source_identity_verified"] is False
    assert receipt["decision_boundary"]["guild_identity_verified"] is False
    assert receipt["decision_boundary"]["ready_for_guild_filtering"] is False

    private_payload = json.loads((tmp_path / "routes.private.json").read_text())
    assert private_payload["candidate_source_guild_id"] == 15
    assert private_payload["summary"]["contains_source_scalar_values"] is True


def test_discovery_requires_private_review_hash_match(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    public_path, private_path = _reviews(tmp_path)
    private_path.write_text(private_path.read_text() + " ")
    monkeypatch.setattr(
        module,
        "_capture_one_page",
        lambda **_kwargs: pytest.fail("network capture must not run"),
    )

    with pytest.raises(ValueError, match="private snapshot review SHA-256"):
        module.discover_guild_identity_route_candidates(
            SimpleNamespace(base_url="https://coa.ascensionlogs.gg"),
            object(),
            public_snapshot_review_path=public_path,
            private_snapshot_review_path=private_path,
            private_output_path=tmp_path / "routes.private.json",
            receipt_output_path=tmp_path / "routes.json",
        )


def test_discovery_does_not_promote_without_guild_route_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    public_path, private_path = _reviews(tmp_path)
    result = _capture_result(("/api/reports/public",))
    monkeypatch.setattr(module, "_capture_one_page", lambda **_kwargs: result)
    monkeypatch.setattr(module, "_archived_capture_route_candidates", lambda _capture: ())
    monkeypatch.setattr(
        module,
        "build_page_capture_to_dict",
        lambda _result: {"private": True},
    )

    receipt = module.discover_guild_identity_route_candidates(
        SimpleNamespace(base_url="https://coa.ascensionlogs.gg"),
        object(),
        public_snapshot_review_path=public_path,
        private_snapshot_review_path=private_path,
        private_output_path=tmp_path / "routes.private.json",
        receipt_output_path=tmp_path / "routes.json",
    )

    assert receipt["decision_boundary"]["ready_for_guild_api_route_review"] is False
    assert receipt["decision_boundary"]["guild_identity_verified"] is False
    assert receipt["decision_boundary"]["ready_for_guild_filtering"] is False


def test_discovery_uses_page_routes_when_asset_capture_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    public_path, private_path = _reviews(tmp_path)
    page_capture = SimpleNamespace(payload_hash="c" * 64)
    failed_asset = SimpleNamespace(
        url="https://coa.ascensionlogs.gg/_app/chunk.js",
        status=None,
        capture=None,
        api_route_candidates=(),
        error=(
            "live read timeout after 30 seconds; "
            "archive has no verified route-bearing payload for the exact asset request"
        ),
    )
    result = SimpleNamespace(
        status=200,
        capture=page_capture,
        assets=(failed_asset,),
        embedded_json=(),
        error=None,
    )
    monkeypatch.setattr(module, "_capture_one_page", lambda **_kwargs: result)
    monkeypatch.setattr(
        module,
        "_archived_capture_route_candidates",
        lambda capture: ("/api/guilds/15/reports",) if capture is page_capture else (),
    )
    monkeypatch.setattr(
        module,
        "build_page_capture_to_dict",
        lambda _result: {"private": True},
    )

    receipt = module.discover_guild_identity_route_candidates(
        SimpleNamespace(base_url="https://coa.ascensionlogs.gg"),
        object(),
        public_snapshot_review_path=public_path,
        private_snapshot_review_path=private_path,
        private_output_path=tmp_path / "routes.private.json",
        receipt_output_path=tmp_path / "routes.json",
    )

    assert receipt["route_inventory"]["guild_api_route_shapes"] == [
        "/api/guilds/{guild_id}/reports"
    ]
    assert receipt["route_inventory"]["candidate_source_counts"] == {
        "page_html": 1,
        "embedded_json": 0,
        "assets": 0,
    }
    assert receipt["summary"]["captured_asset_count"] == 0
    assert receipt["summary"]["failed_asset_count"] == 1
    assert receipt["asset_failure_summary"] == {
        "failed_asset_count": 1,
        "failure_class_counts": {
            "archive_fallback_unavailable": 1,
            "timeout": 1,
        },
        "contains_error_text": False,
        "contains_asset_urls": False,
    }
    assert receipt["decision_boundary"]["ready_for_guild_api_route_review"] is True
    assert receipt["decision_boundary"]["guild_api_route_semantics_verified"] is False
    assert receipt["decision_boundary"]["guild_identity_verified"] is False
    assert receipt["decision_boundary"]["ready_for_guild_filtering"] is False
