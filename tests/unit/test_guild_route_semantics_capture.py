from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from coa_workbench.collector.guild_route_semantics_capture import (
    capture_guild_route_semantics,
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


def _write_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    contract_path = tmp_path / "full-crawl-contract.json"
    contract = {
        "schema_version": 1,
        "contract_kind": "guild_full_crawl_collection_contract",
        "contract_version": "guild-full-crawl-contract-v1",
        "target": {
            "guild_label": "Argentum",
            "source_guild_id_published": False,
            "report_ids_published": False,
        },
        "summary": {
            "all_integrity_checks_passed": True,
            "contains_source_scalar_values": False,
            "full_crawl_collection_contract_reviewed": True,
            "ready_for_bounded_route_semantics_capture": True,
            "guild_api_route_semantics_verified": False,
            "ready_for_full_guild_crawl": False,
            "planner_scoring_allowed": False,
        },
        "decision_boundary": {
            "full_crawl_collection_contract_reviewed": True,
            "ready_for_bounded_route_semantics_capture": True,
            "guild_api_route_semantics_verified": False,
            "automatic_full_guild_crawl_allowed": False,
            "ready_for_full_guild_crawl": False,
            "ready_for_multi_report_character_graph": False,
            "ready_for_performance_model": False,
            "ready_for_bis25_scoring": False,
            "planner_scoring_allowed": False,
        },
    }
    contract_path.write_bytes(_canonical_body(contract))

    private_access_path = tmp_path / "access.private.json"
    private_access = {
        "schema_version": 1,
        "diagnostic_kind": "guild_identity_search_access_diagnostic_private",
        "diagnostic_version": "guild-identity-search-access-diagnostic-v1",
        "target_guild_label": "Argentum",
        "request_url": (
            "https://example.test/api/guilds/search?q=Argentum&limit=25"
        ),
        "selected_profile": "spa_fetch_context",
        "attempts": [
            {
                "profile": "spa_fetch_context",
                "return_code": 0,
                "http_status": 200,
                "response_candidate": True,
                "body": {
                    "guilds": [
                        {
                            "id": 123456,
                            "name": "ARGENTUM",
                            "realm": "Test Realm",
                            "report_count": "17",
                        }
                    ]
                },
            }
        ],
    }
    private_access_body = _canonical_body(private_access)
    private_access_path.write_bytes(private_access_body)

    public_access_path = tmp_path / "access.json"
    public_access = {
        "schema_version": 1,
        "diagnostic_kind": "guild_identity_search_access_diagnostic",
        "diagnostic_version": "guild-identity-search-access-diagnostic-v1",
        "source_private_diagnostic_sha256": _sha256(private_access_body),
        "target": {
            "guild_label": "Argentum",
            "request_url_published": False,
            "source_guild_id_published": False,
        },
        "summary": {
            "all_integrity_checks_passed": True,
            "selected_access_profile": "spa_fetch_context",
            "contains_source_scalar_values": False,
        },
        "decision_boundary": {
            "ready_for_profiled_guild_search_probe": True,
            "selected_access_profile": "spa_fetch_context",
            "guild_api_route_semantics_verified": False,
            "ready_for_full_guild_crawl": False,
            "planner_scoring_allowed": False,
        },
    }
    public_access_path.write_bytes(_canonical_body(public_access))
    return contract_path, public_access_path, private_access_path


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


def _success_body() -> bytes:
    return json.dumps(
        {
            "guilds": [
                {
                    "id": 123456,
                    "name": "ARGENTUM",
                    "realm": "Test Realm",
                    "report_count": "17",
                }
            ]
        }
    ).encode()


def _run(
    tmp_path: Path,
    runner: _FakeRunner,
    *,
    contract_path: Path | None = None,
    public_access_path: Path | None = None,
    private_access_path: Path | None = None,
) -> dict[str, object]:
    if contract_path is None or public_access_path is None or private_access_path is None:
        contract_path, public_access_path, private_access_path = _write_inputs(tmp_path)
    return capture_guild_route_semantics(
        _registry(),
        RawArchive(tmp_path / "raw"),
        full_crawl_contract_path=contract_path,
        public_access_diagnostic_path=public_access_path,
        private_access_diagnostic_path=private_access_path,
        private_output_path=tmp_path / "capture.private.json",
        receipt_output_path=tmp_path / "capture.json",
        curl_executable="curl",
        timeout_seconds=60,
        max_bytes=256 * 1024,
        runner=runner,
    )


def test_capture_is_review_ready_without_promoting_route_semantics(
    tmp_path: Path,
) -> None:
    body = _success_body()
    runner = _FakeRunner(
        [
            (0, 200, "application/json", body),
            (0, 200, "application/json", body),
            (0, 200, "application/json", body),
        ]
    )

    receipt = _run(tmp_path, runner)

    summary = receipt["summary"]
    boundary = receipt["decision_boundary"]
    review = receipt["cross_case_review"]
    assert summary["all_integrity_checks_passed"] is True
    assert summary["attempt_count"] == 3
    assert summary["completed_attempt_count"] == 3
    assert summary["ready_for_route_semantics_review"] is True
    assert review["route_shapes_observed"] is True
    assert review["response_shape_consistent"] is True
    assert review["target_name_casefold_match_stable"] is True
    assert review["source_id_set_stable_by_hash"] is True
    assert review["limit_truncation_semantics_verified"] is False
    assert review["pagination_object_observed"] is False
    assert boundary["bounded_route_semantics_capture_completed"] is True
    assert boundary["guild_api_route_semantics_verified"] is False
    assert boundary["ready_for_full_guild_crawl"] is False
    assert boundary["planner_scoring_allowed"] is False

    public_text = (tmp_path / "capture.json").read_text(encoding="utf-8")
    assert "123456" not in public_text
    assert "Test Realm" not in public_text
    assert "example.test" not in public_text
    assert '"request_urls_published": false' in public_text
    assert '"contains_source_scalar_values": false' in public_text

    assert len(runner.commands) == 3
    urls = [command[-1] for command in runner.commands]
    assert urls[0].endswith("q=Argentum&limit=1")
    assert urls[1].endswith("q=Argentum&limit=25")
    assert urls[2].endswith("q=Argentum")
    for command in runner.commands:
        assert command[command.index("--max-redirs") + 1] == "0"
        assert command[command.index("--retry") + 1] == "0"
        joined = "\n".join(command).casefold()
        assert "authorization:" not in joined
        assert "cookie:" not in joined


def test_private_access_hash_mismatch_blocks_network(tmp_path: Path) -> None:
    contract_path, public_access_path, private_access_path = _write_inputs(tmp_path)
    private_access_path.write_text("{}\n", encoding="utf-8")
    runner = _FakeRunner([])

    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        _run(
            tmp_path,
            runner,
            contract_path=contract_path,
            public_access_path=public_access_path,
            private_access_path=private_access_path,
        )

    assert runner.commands == []


def test_partial_capture_is_not_review_ready(tmp_path: Path) -> None:
    body = _success_body()
    failure = json.dumps({"error": "temporary"}).encode()
    runner = _FakeRunner(
        [
            (0, 200, "application/json", body),
            (0, 500, "application/json", failure),
            (0, 200, "application/json", body),
        ]
    )

    receipt = _run(tmp_path, runner)

    summary = receipt["summary"]
    boundary = receipt["decision_boundary"]
    assert summary["attempt_count"] == 3
    assert summary["completed_attempt_count"] == 2
    assert summary["ready_for_route_semantics_review"] is False
    assert boundary["bounded_route_semantics_capture_completed"] is False
    assert boundary["guild_api_route_semantics_verified"] is False
    assert boundary["ready_for_full_guild_crawl"] is False

    public_text = (tmp_path / "capture.json").read_text(encoding="utf-8")
    assert "temporary" not in public_text


def test_capture_rejects_unbounded_response_limit(tmp_path: Path) -> None:
    contract_path, public_access_path, private_access_path = _write_inputs(tmp_path)

    with pytest.raises(ValueError, match="between 64 KiB and 1 MiB"):
        capture_guild_route_semantics(
            _registry(),
            RawArchive(tmp_path / "raw"),
            full_crawl_contract_path=contract_path,
            public_access_diagnostic_path=public_access_path,
            private_access_diagnostic_path=private_access_path,
            private_output_path=tmp_path / "capture.private.json",
            receipt_output_path=tmp_path / "capture.json",
            curl_executable="curl",
            max_bytes=2 * 1024 * 1024,
            runner=_FakeRunner([]),
        )
