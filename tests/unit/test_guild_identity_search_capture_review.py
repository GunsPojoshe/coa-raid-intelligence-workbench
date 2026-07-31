from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import pytest

from coa_workbench.collector.guild_identity_search_capture_review import (
    review_guild_identity_search_capture,
)


def _write_json(path: Path, payload: object) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    path.write_bytes(body)
    return body


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _fixture(tmp_path: Path) -> dict[str, Path | str]:
    source_id = "source-42"
    payload = {
        "guilds": [
            {
                "id": source_id,
                "name": "Argentum",
            }
        ],
        "success": True,
    }
    payload_body = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    payload_hash = _sha256(payload_body)
    capture = {
        "raw_id": "raw-capture-1",
        "observation_id": "observation-1",
        "payload_hash": payload_hash,
        "schema_fingerprint": "schema-fingerprint-1",
        "bytes_uncompressed": len(payload_body),
    }

    raw_root = tmp_path / "data" / "raw"
    folder = (
        raw_root
        / "source=ascension_logs"
        / "year=2026"
        / "month=07"
        / "endpoint=guild_identity_search_access_diagnostic"
    )
    folder.mkdir(parents=True)
    payload_path = folder / f"{payload_hash}.json.gz"
    with payload_path.open("wb") as stream:
        with gzip.GzipFile(fileobj=stream, mode="wb", mtime=0) as compressed:
            compressed.write(payload_body)
    _write_json(
        folder / f"{payload_hash}.content.json",
        {
            "schema_version": 1,
            "raw_id": capture["raw_id"],
            "source_code": "ascension_logs",
            "endpoint_code": "guild_identity_search_access_diagnostic",
            "request_key": "GET:/api/guilds/search?keys=limit,q#fixture",
            "payload_hash": payload_hash,
            "payload_path": payload_path.relative_to(raw_root).as_posix(),
            "compression": "gzip",
            "bytes_uncompressed": len(payload_body),
            "content_type": "application/json; charset=utf-8",
            "schema_fingerprint": capture["schema_fingerprint"],
        },
    )

    private_probe_path = tmp_path / "private-search-probe.json"
    private_probe_body = _write_json(
        private_probe_path,
        {
            "schema_version": 1,
            "probe_kind": "guild_identity_search_probe_private",
            "probe_version": "guild-identity-search-probe-v1",
            "target_guild_label": "Argentum",
            "candidate_source_guild_id": source_id,
        },
    )

    private_diagnostic_path = tmp_path / "private-access-diagnostic.json"
    private_diagnostic_body = _write_json(
        private_diagnostic_path,
        {
            "schema_version": 1,
            "diagnostic_kind": "guild_identity_search_access_diagnostic_private",
            "diagnostic_version": "guild-identity-search-access-diagnostic-v1",
            "target_guild_label": "Argentum",
            "source_private_probe_sha256": _sha256(private_probe_body),
            "selected_profile": "spa_fetch_context",
            "attempts": [
                {
                    "profile": "minimal_http1_1",
                    "return_code": 0,
                    "http_status": 403,
                    "response_candidate": False,
                    "capture": {
                        "raw_id": "denied-raw",
                        "observation_id": "denied-observation",
                        "payload_hash": "0" * 64,
                        "schema_fingerprint": "denied-schema",
                        "bytes_uncompressed": 56,
                    },
                    "body": {"error": "forbidden"},
                },
                {
                    "profile": "spa_fetch_context",
                    "return_code": 0,
                    "http_status": 200,
                    "content_type": "application/json; charset=utf-8",
                    "response_candidate": True,
                    "capture": capture,
                    "body": payload,
                },
            ],
        },
    )

    public_diagnostic_path = tmp_path / "public-access-diagnostic.json"
    _write_json(
        public_diagnostic_path,
        {
            "schema_version": 1,
            "diagnostic_kind": "guild_identity_search_access_diagnostic",
            "diagnostic_version": "guild-identity-search-access-diagnostic-v1",
            "source_private_diagnostic_sha256": _sha256(private_diagnostic_body),
            "target": {
                "guild_label": "Argentum",
                "request_url_published": False,
                "source_guild_id_published": False,
            },
            "summary": {
                "all_integrity_checks_passed": True,
                "contains_source_scalar_values": False,
                "contains_error_text": False,
                "selected_access_profile": "spa_fetch_context",
            },
            "decision_boundary": {
                "ready_for_profiled_guild_search_probe": True,
                "selected_access_profile": "spa_fetch_context",
                "guild_api_route_semantics_verified": False,
                "independent_source_identity_verified": False,
                "guild_identity_verified": False,
                "ready_for_guild_filtering": False,
                "ready_for_full_guild_crawl": False,
                "planner_scoring_allowed": False,
            },
            "attempts": [
                {
                    "profile": "minimal_http1_1",
                    "return_code": 0,
                    "http_status": 403,
                    "response_candidate": False,
                    "capture": {
                        "raw_id": "denied-raw",
                        "observation_id": "denied-observation",
                        "payload_hash": "0" * 64,
                        "schema_fingerprint": "denied-schema",
                        "bytes_uncompressed": 56,
                    },
                },
                {
                    "profile": "spa_fetch_context",
                    "return_code": 0,
                    "http_status": 200,
                    "response_candidate": True,
                    "capture": capture,
                },
            ],
        },
    )

    return {
        "source_id": source_id,
        "payload_path": payload_path,
        "public_diagnostic_path": public_diagnostic_path,
        "private_diagnostic_path": private_diagnostic_path,
        "private_probe_path": private_probe_path,
        "raw_root": raw_root,
        "private_output_path": tmp_path / "private-review.json",
        "receipt_output_path": tmp_path / "public-review.json",
    }


def _review(paths: dict[str, Path | str]) -> dict[str, object]:
    return review_guild_identity_search_capture(
        public_access_diagnostic_path=Path(paths["public_diagnostic_path"]),
        private_access_diagnostic_path=Path(paths["private_diagnostic_path"]),
        private_search_probe_path=Path(paths["private_probe_path"]),
        raw_root=Path(paths["raw_root"]),
        private_output_path=Path(paths["private_output_path"]),
        receipt_output_path=Path(paths["receipt_output_path"]),
    )


def test_review_promotes_only_one_to_one_identity_candidate(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)

    receipt = _review(paths)

    assert receipt["summary"]["all_integrity_checks_passed"] is True
    assert receipt["summary"]["route_shape_candidate"] is True
    assert receipt["summary"]["exact_label_object_count"] == 1
    assert receipt["summary"]["source_id_match_object_count"] == 1
    assert receipt["summary"]["one_to_one_identity_candidate"] is True
    boundary = receipt["decision_boundary"]
    assert boundary["ready_for_guild_identity_decision_review"] is True
    assert boundary["guild_identity_verified"] is False
    assert boundary["ready_for_guild_filtering"] is False
    public_text = Path(paths["receipt_output_path"]).read_text(encoding="utf-8")
    assert str(paths["source_id"]) not in public_text


def test_review_rejects_private_diagnostic_hash_mismatch(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    private_path = Path(paths["private_diagnostic_path"])
    private_path.write_bytes(private_path.read_bytes() + b"\n")

    with pytest.raises(ValueError, match="private access diagnostic SHA-256 mismatch"):
        _review(paths)


def test_review_rejects_tampered_archived_payload(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    payload_path = Path(paths["payload_path"])
    with payload_path.open("wb") as stream:
        with gzip.GzipFile(fileobj=stream, mode="wb", mtime=0) as compressed:
            compressed.write(b'{"guilds":[],"success":true}')

    with pytest.raises(ValueError, match="bound gzip payload SHA-256 mismatch"):
        _review(paths)
