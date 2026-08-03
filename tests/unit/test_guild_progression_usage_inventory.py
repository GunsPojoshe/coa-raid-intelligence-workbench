from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import pytest

from coa_workbench.collector.guild_progression_usage_inventory import (
    inventory_guild_progression_usage_context,
)


def _body(payload: object) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _inputs(tmp_path: Path, javascript: bytes) -> tuple[Path, Path, Path]:
    raw_root = tmp_path / "raw"
    payload_hash = _sha256(javascript)
    folder = (
        raw_root
        / "source=coa"
        / "year=2026"
        / "month=08"
        / "endpoint=guild_identity_asset_recovery"
    )
    folder.mkdir(parents=True)
    payload_path = folder / f"{payload_hash}.bin.gz"
    with payload_path.open("wb") as stream:
        with gzip.GzipFile(fileobj=stream, mode="wb", mtime=0) as compressed:
            compressed.write(javascript)
    manifest = {
        "schema_version": 1,
        "raw_id": "1" * 64,
        "source_code": "coa",
        "endpoint_code": "guild_identity_asset_recovery",
        "request_key": "GET:/asset.js",
        "payload_hash": payload_hash,
        "payload_path": payload_path.relative_to(raw_root).as_posix(),
        "compression": "gzip",
        "bytes_uncompressed": len(javascript),
        "content_type": "application/javascript",
        "schema_fingerprint": None,
    }
    (folder / f"{payload_hash}.content.json").write_bytes(_body(manifest))

    private = {
        "schema_version": 1,
        "recovery_kind": "guild_identity_asset_profiled_recovery_private",
        "recovery_version": "guild-identity-asset-profiled-recovery-v1",
        "target_guild_label": "Argentum",
        "asset_capture_payload_hash": payload_hash,
        "api_route_candidates": [
            "/api/guilds/progression",
            "/api/guilds/search?q=x",
            "/api/guilds/search?q=x&limit=1",
        ],
        "summary": {
            "asset_download_completed": True,
            "contains_source_scalar_values": True,
        },
    }
    private_path = tmp_path / "recovery.private.json"
    private_body = _body(private)
    private_path.write_bytes(private_body)

    checks = {f"check_{index}": True for index in range(15)}
    public = {
        "schema_version": 1,
        "recovery_kind": "guild_identity_asset_profiled_recovery",
        "recovery_version": "guild-identity-asset-profiled-recovery-v1",
        "source_private_recovery_sha256": _sha256(private_body),
        "target": {
            "guild_label": "Argentum",
            "asset_url_published": False,
            "source_guild_id_published": False,
        },
        "route_inventory": {
            "guild_api_route_shapes": [
                "/api/guilds/progression",
                "/api/guilds/search?q=<value>",
                "/api/guilds/search?q=<value>&limit=<value>",
            ]
        },
        "summary": {
            "all_integrity_checks_passed": True,
            "asset_download_completed": True,
            "contains_source_scalar_values": False,
            "guild_api_route_candidate_count": 3,
        },
        "integrity_checks": checks,
        "decision_boundary": {
            "guild_api_route_candidates_observed": True,
            "guild_api_route_semantics_verified": False,
            "ready_for_guild_api_route_review": True,
            "ready_for_full_guild_crawl": False,
            "planner_scoring_allowed": False,
        },
    }
    public_path = tmp_path / "recovery.json"
    public_path.write_bytes(_body(public))
    return public_path, private_path, raw_root


def _run(tmp_path: Path, javascript: bytes) -> dict[str, object]:
    public, private, raw_root = _inputs(tmp_path, javascript)
    return inventory_guild_progression_usage_context(
        public_recovery_path=public,
        private_recovery_path=private,
        raw_root=raw_root,
        private_output_path=tmp_path / "usage.private.json",
        receipt_output_path=tmp_path / "usage.json",
    )


def test_fetch_get_usage_is_scalar_free_and_keeps_gates_closed(tmp_path: Path) -> None:
    receipt = _run(
        tmp_path,
        b'const load=()=>fetch("/api/guilds/progression").then(x=>x.json());',
    )

    evidence = receipt["cross_occurrence_evidence"]
    summary = receipt["summary"]
    boundary = receipt["decision_boundary"]
    assert evidence["method_candidates"] == ["GET"]
    assert evidence["method_candidate_unambiguous"] is True
    assert summary["ready_for_guild_progression_usage_review"] is True
    assert summary["ready_for_bounded_progression_route_probe"] is False
    assert boundary["guild_api_route_semantics_verified"] is False
    assert boundary["pagination_semantics_verified"] is False
    assert boundary["ready_for_full_guild_crawl"] is False
    assert boundary["planner_scoring_allowed"] is False

    private_text = (tmp_path / "usage.private.json").read_text(encoding="utf-8")
    public_text = (tmp_path / "usage.json").read_text(encoding="utf-8")
    assert "const load" in private_text
    assert "const load" not in public_text
    assert '"raw_context_published": false' in public_text


def test_explicit_post_method_is_observed_without_promotion(tmp_path: Path) -> None:
    receipt = _run(
        tmp_path,
        b'fetch("/api/guilds/progression",{method:"POST",body:data});',
    )

    evidence = receipt["cross_occurrence_evidence"]
    assert evidence["method_candidates"] == ["POST"]
    assert evidence["method_candidate_unambiguous"] is True
    assert receipt["decision_boundary"]["ready_for_bounded_progression_route_probe"] is False


def test_generic_helper_remains_reviewable_but_method_unresolved(tmp_path: Path) -> None:
    receipt = _run(tmp_path, b'client("/api/guilds/progression",state);')

    evidence = receipt["cross_occurrence_evidence"]
    assert evidence["method_candidates"] == []
    assert evidence["method_candidate_unambiguous"] is False
    assert evidence["call_style_candidates"] == ["generic_helper_call"]
    assert receipt["summary"]["ready_for_guild_progression_usage_review"] is True


def test_private_recovery_hash_mismatch_blocks_inventory(tmp_path: Path) -> None:
    public, private, raw_root = _inputs(
        tmp_path,
        b'fetch("/api/guilds/progression")',
    )
    private.write_text("{}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="private profiled recovery SHA-256 mismatch"):
        inventory_guild_progression_usage_context(
            public_recovery_path=public,
            private_recovery_path=private,
            raw_root=raw_root,
            private_output_path=tmp_path / "usage.private.json",
            receipt_output_path=tmp_path / "usage.json",
        )


def test_archive_hash_mismatch_blocks_inventory(tmp_path: Path) -> None:
    public, private, raw_root = _inputs(
        tmp_path,
        b'fetch("/api/guilds/progression")',
    )
    payload = next(raw_root.glob("**/*.bin.gz"))
    payload.write_bytes(gzip.compress(b"changed", mtime=0))

    with pytest.raises(ValueError, match="payload SHA-256 mismatch"):
        inventory_guild_progression_usage_context(
            public_recovery_path=public,
            private_recovery_path=private,
            raw_root=raw_root,
            private_output_path=tmp_path / "usage.private.json",
            receipt_output_path=tmp_path / "usage.json",
        )


def test_missing_route_candidate_blocks_inventory(tmp_path: Path) -> None:
    public, private, raw_root = _inputs(tmp_path, b'const x="no route";')
    private_payload = json.loads(private.read_text(encoding="utf-8"))
    private_payload["api_route_candidates"] = ["/api/guilds/search?q=x"]
    private_body = _body(private_payload)
    private.write_bytes(private_body)
    public_payload = json.loads(public.read_text(encoding="utf-8"))
    public_payload["source_private_recovery_sha256"] = _sha256(private_body)
    public.write_bytes(_body(public_payload))

    with pytest.raises(ValueError, match="private recovery does not contain"):
        inventory_guild_progression_usage_context(
            public_recovery_path=public,
            private_recovery_path=private,
            raw_root=raw_root,
            private_output_path=tmp_path / "usage.private.json",
            receipt_output_path=tmp_path / "usage.json",
        )
