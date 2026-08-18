from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from coa_workbench.collector.guild_identity_search_access_diagnostic import (
    capture_guild_identity_search_access_diagnostic,
)
from coa_workbench.collector.raw_archive import RawArchive
from coa_workbench.collector.source_registry import SourceRegistry


def _canonical_body(payload: object) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _registry() -> SourceRegistry:
    return SourceRegistry(
        schema_version=1,
        source_code="test_source",
        base_url="https://example.test",
        status="candidate",
        truth_role="observation",
        routes=(),
        principles=(),
        prohibited_assumptions=(),
    )


def _write_inputs(tmp_path: Path) -> tuple[Path, Path]:
    private_payload = {
        "schema_version": 1,
        "probe_kind": "guild_identity_search_probe_private",
        "probe_version": "guild-identity-search-probe-v1",
        "target_guild_label": "Argentum",
        "request_url": (
            "https://example.test/api/guilds/search?q=Argentum&limit=25"
        ),
        "transport": {
            "profile": "http1_1",
            "http_status": 403,
            "failure_class": "http_status_failure",
        },
        "summary": {
            "response_completed": False,
            "contains_source_scalar_values": True,
        },
    }
    private_body = _canonical_body(private_payload)
    private_path = tmp_path / "search.private.json"
    private_path.write_bytes(private_body)

    public_payload = {
        "schema_version": 1,
        "probe_kind": "guild_identity_search_probe",
        "probe_version": "guild-identity-search-probe-v1",
        "source_private_probe_sha256": _sha256(private_body),
        "target": {
            "guild_label": "Argentum",
            "source_guild_id_published": False,
            "request_url_published": False,
        },
        "request": {
            "route_template": "/api/guilds/search",
            "query_keys": ["q", "limit"],
            "transport_profile": "http1_1",
            "redirects_allowed": False,
            "credentials_supplied": False,
        },
        "response": {
            "completed": False,
            "http_status": 403,
            "failure_class": "http_status_failure",
            "capture": None,
        },
        "decision_boundary": {
            "guild_api_route_candidates_observed": True,
            "guild_api_route_semantics_verified": False,
            "independent_source_identity_verified": False,
            "guild_identity_verified": False,
            "ready_for_guild_filtering": False,
            "ready_for_full_guild_crawl": False,
            "planner_scoring_allowed": False,
        },
        "summary": {
            "all_integrity_checks_passed": True,
            "response_completed": False,
            "contains_source_scalar_values": False,
            "contains_error_text": False,
        },
    }
    public_path = tmp_path / "search.json"
    public_path.write_bytes(_canonical_body(public_payload))
    return public_path, private_path


class _FakeRunner:
    def __init__(self, responses: list[tuple[int, int, str, bytes]]) -> None:
        self.responses = list(responses)
        self.commands: list[list[str]] = []

    def __call__(self, command: list[str], **_kwargs: object) -> SimpleNamespace:
        self.commands.append(command)
        return_code, status, content_type, body = self.responses.pop(0)
        output_path = Path(command[command.index("--output") + 1])
        output_path.write_bytes(body)
        return SimpleNamespace(
            returncode=return_code,
            stdout=f"{status}\n{content_type}",
            stderr="",
        )


def _run(
    tmp_path: Path,
    runner: _FakeRunner,
    *,
    public_path: Path | None = None,
    private_path: Path | None = None,
) -> dict[str, object]:
    if public_path is None or private_path is None:
        public_path, private_path = _write_inputs(tmp_path)
    return capture_guild_identity_search_access_diagnostic(
        _registry(),
        RawArchive(tmp_path / "raw"),
        public_search_probe_path=public_path,
        private_search_probe_path=private_path,
        private_output_path=tmp_path / "diagnostic.private.json",
        receipt_output_path=tmp_path / "diagnostic.json",
        curl_executable="curl",
        timeout_seconds=60,
        max_bytes=256 * 1024,
        runner=runner,
    )


def test_http_403_body_is_classified_without_publishing_error_text(
    tmp_path: Path,
) -> None:
    denied = json.dumps({"error": "Authentication required"}).encode()
    runner = _FakeRunner(
        [
            (0, 403, "application/json", denied),
            (0, 403, "application/json", denied),
            (0, 403, "application/json", denied),
        ]
    )

    receipt = _run(tmp_path, runner)

    summary = receipt["summary"]
    boundary = receipt["decision_boundary"]
    assert summary["all_integrity_checks_passed"] is True
    assert summary["attempt_count"] == 3
    assert summary["denial_categories"] == ["authentication_required"]
    assert boundary["guild_search_denial_category_observed"] is True
    assert boundary["ready_for_profiled_guild_search_probe"] is False
    assert boundary["guild_identity_verified"] is False

    public_text = (tmp_path / "diagnostic.json").read_text(encoding="utf-8")
    assert "Authentication required" not in public_text
    assert "example.test" not in public_text
    assert '"contains_source_scalar_values": false' in public_text


def test_browser_like_profile_can_be_selected_without_promoting_identity(
    tmp_path: Path,
) -> None:
    denied = json.dumps({"error": "Forbidden"}).encode()
    success = json.dumps(
        {"guilds": [{"id": 123456, "name": "Argentum"}]}
    ).encode()
    runner = _FakeRunner(
        [
            (0, 403, "application/json", denied),
            (0, 200, "application/json", success),
        ]
    )

    receipt = _run(tmp_path, runner)

    summary = receipt["summary"]
    boundary = receipt["decision_boundary"]
    assert summary["attempt_count"] == 2
    assert summary["selected_access_profile"] == "spa_fetch_context"
    assert boundary["guild_search_access_profile_candidate_observed"] is True
    assert boundary["ready_for_profiled_guild_search_probe"] is True
    assert boundary["guild_api_route_semantics_verified"] is False
    assert boundary["guild_identity_verified"] is False
    assert boundary["ready_for_guild_filtering"] is False

    public_text = (tmp_path / "diagnostic.json").read_text(encoding="utf-8")
    assert "123456" not in public_text
    assert '"contains_error_text": false' in public_text

    for command in runner.commands:
        assert command[command.index("--max-redirs") + 1] == "0"
        assert command[command.index("--retry") + 1] == "0"
        joined = "\n".join(command).casefold()
        assert "authorization:" not in joined
        assert "cookie:" not in joined


def test_private_probe_hash_mismatch_blocks_network(tmp_path: Path) -> None:
    public_path, private_path = _write_inputs(tmp_path)
    private_path.write_text("{}\n", encoding="utf-8")
    runner = _FakeRunner([])

    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        _run(
            tmp_path,
            runner,
            public_path=public_path,
            private_path=private_path,
        )

    assert runner.commands == []


def test_access_diagnostic_rejects_unbounded_response_limit(tmp_path: Path) -> None:
    public_path, private_path = _write_inputs(tmp_path)

    with pytest.raises(ValueError, match="between 64 KiB and 1 MiB"):
        capture_guild_identity_search_access_diagnostic(
            _registry(),
            RawArchive(tmp_path / "raw"),
            public_search_probe_path=public_path,
            private_search_probe_path=private_path,
            private_output_path=tmp_path / "diagnostic.private.json",
            receipt_output_path=tmp_path / "diagnostic.json",
            curl_executable="curl",
            max_bytes=2 * 1024 * 1024,
            runner=_FakeRunner([]),
        )
