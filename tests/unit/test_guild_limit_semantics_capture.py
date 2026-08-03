from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from coa_workbench.collector.guild_limit_semantics_capture import (
    capture_guild_limit_semantics,
)
from coa_workbench.collector.raw_archive import RawArchive
from coa_workbench.collector.source_registry import SourceRegistry


def _body(payload: object) -> bytes:
    return json.dumps(payload).encode()


def _canonical_body(payload: object) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()


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


def _route_review_path(tmp_path: Path) -> Path:
    checks = {f"check_{index:02d}": True for index in range(22)}
    receipt = {
        "schema_version": 1,
        "review_kind": "guild_route_semantics_review",
        "review_version": "guild-route-semantics-review-v1",
        "integrity_checks": checks,
        "summary": {
            "all_integrity_checks_passed": True,
            "contains_raw_payload": False,
            "contains_source_scalar_values": False,
            "route_shape_and_response_schema_reviewed": True,
            "limit_parameter_accepted": True,
            "ready_for_bounded_limit_semantics_capture": True,
            "limit_truncation_semantics_verified": False,
            "pagination_semantics_verified": False,
            "termination_semantics_verified": False,
            "completeness_verified": False,
            "guild_api_route_semantics_verified": False,
            "ready_for_full_guild_crawl": False,
            "planner_scoring_allowed": False,
        },
        "route_review": {
            "route_template": "/api/guilds/search",
            "contains_query_values": False,
            "query_parameter_q_observed": True,
            "query_shape_with_limit_verified": True,
            "limit_parameter_accepted": True,
            "limit_truncation_semantics_verified": False,
        },
        "response_schema_review": {
            "contains_source_scalar_values": False,
            "guild_collection_field": "guilds",
            "guild_record_fields": [
                {"field": "id", "types": ["integer"]},
                {"field": "name", "types": ["string"]},
                {"field": "realm", "types": ["string"]},
                {"field": "report_count", "types": ["string"]},
            ],
            "guild_record_schema_verified": True,
            "top_level_keys": ["guilds", "success"],
            "top_level_kind": "object",
        },
        "decision_boundary": {
            "guild_route_template_verified": True,
            "guild_query_shapes_verified": True,
            "guild_response_schema_verified": True,
            "limit_parameter_accepted": True,
            "ready_for_bounded_limit_semantics_capture": True,
            "limit_truncation_semantics_verified": False,
            "pagination_semantics_verified": False,
            "termination_semantics_verified": False,
            "completeness_verified": False,
            "guild_api_route_semantics_verified": False,
            "automatic_full_guild_crawl_allowed": False,
            "ready_for_full_guild_crawl": False,
            "ready_for_multi_report_character_graph": False,
            "ready_for_performance_model": False,
            "ready_for_bis25_scoring": False,
            "planner_scoring_allowed": False,
        },
        "target": {
            "raw_payload_published": False,
            "report_ids_published": False,
            "request_urls_published": False,
            "source_guild_id_published": False,
        },
    }
    path = tmp_path / "route-review.json"
    path.write_bytes(_canonical_body(receipt))
    return path


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


def _record(source_id: int, name: str) -> dict[str, object]:
    return {
        "id": source_id,
        "name": name,
        "realm": "Private Realm",
        "report_count": "7",
    }


def _run(tmp_path: Path, runner: _FakeRunner) -> dict[str, object]:
    return capture_guild_limit_semantics(
        _registry(),
        RawArchive(tmp_path / "raw"),
        route_review_path=_route_review_path(tmp_path),
        query="PrivateNeedle",
        low_limit=1,
        high_limit=25,
        private_output_path=tmp_path / "limit.private.json",
        receipt_output_path=tmp_path / "limit.json",
        curl_executable="curl",
        runner=runner,
    )


def test_multi_result_prefix_capture_is_review_ready(tmp_path: Path) -> None:
    low = {"guilds": [_record(101, "Alpha")], "success": True}
    high = {
        "guilds": [
            _record(101, "Alpha"),
            _record(202, "Beta"),
            _record(303, "Gamma"),
        ],
        "success": True,
    }
    runner = _FakeRunner(
        [
            (0, 200, "application/json", _body(low)),
            (0, 200, "application/json", _body(high)),
            (0, 200, "application/json", _body(high)),
        ]
    )

    receipt = _run(tmp_path, runner)

    summary = receipt["summary"]
    evidence = receipt["cross_case_evidence"]
    boundary = receipt["decision_boundary"]
    assert summary["all_integrity_checks_passed"] is True
    assert summary["completed_attempt_count"] == 3
    assert summary["multi_result_observed"] is True
    assert summary["limit_truncation_evidence_observed"] is True
    assert summary["ready_for_limit_semantics_review"] is True
    assert evidence["low_limit_saturated"] is True
    assert evidence["high_limit_repeat_stable"] is True
    assert evidence["low_result_is_high_result_prefix_by_id_hash"] is True
    assert boundary["limit_truncation_semantics_verified"] is False
    assert boundary["pagination_semantics_verified"] is False
    assert boundary["ready_for_full_guild_crawl"] is False
    assert boundary["planner_scoring_allowed"] is False

    public_text = (tmp_path / "limit.json").read_text(encoding="utf-8")
    assert "PrivateNeedle" not in public_text
    assert "Private Realm" not in public_text
    assert "Alpha" not in public_text
    assert "101" not in public_text
    assert '"query_value_published": false' in public_text
    assert '"contains_source_scalar_values": false' in public_text

    assert len(runner.commands) == 3
    assert runner.commands[0][-1].endswith("q=PrivateNeedle&limit=1")
    assert runner.commands[1][-1].endswith("q=PrivateNeedle&limit=25")
    assert runner.commands[2][-1].endswith("q=PrivateNeedle&limit=25")
    for command in runner.commands:
        assert command[command.index("--max-redirs") + 1] == "0"
        assert command[command.index("--retry") + 1] == "0"
        joined = "\n".join(command).casefold()
        assert "authorization:" not in joined
        assert "cookie:" not in joined


def test_single_result_capture_is_not_review_ready(tmp_path: Path) -> None:
    single = {"guilds": [_record(101, "Alpha")], "success": True}
    body = _body(single)
    receipt = _run(
        tmp_path,
        _FakeRunner(
            [
                (0, 200, "application/json", body),
                (0, 200, "application/json", body),
                (0, 200, "application/json", body),
            ]
        ),
    )

    assert receipt["summary"]["multi_result_observed"] is False
    assert receipt["summary"]["ready_for_limit_semantics_review"] is False
    assert receipt["decision_boundary"]["ready_for_full_guild_crawl"] is False


def test_high_limit_repeat_drift_blocks_review(tmp_path: Path) -> None:
    low = {"guilds": [_record(101, "Alpha")], "success": True}
    high = {
        "guilds": [_record(101, "Alpha"), _record(202, "Beta")],
        "success": True,
    }
    drifted = {
        "guilds": [_record(101, "Alpha"), _record(303, "Gamma")],
        "success": True,
    }
    receipt = _run(
        tmp_path,
        _FakeRunner(
            [
                (0, 200, "application/json", _body(low)),
                (0, 200, "application/json", _body(high)),
                (0, 200, "application/json", _body(drifted)),
            ]
        ),
    )

    evidence = receipt["cross_case_evidence"]
    assert evidence["multi_result_observed"] is True
    assert evidence["high_limit_repeat_stable"] is False
    assert evidence["limit_truncation_evidence_observed"] is False
    assert receipt["summary"]["ready_for_limit_semantics_review"] is False


def test_changed_route_review_blocks_network(tmp_path: Path) -> None:
    review_path = _route_review_path(tmp_path)
    review = json.loads(review_path.read_text(encoding="utf-8"))
    review["decision_boundary"]["ready_for_full_guild_crawl"] = True
    review_path.write_bytes(_canonical_body(review))
    runner = _FakeRunner([])

    with pytest.raises(ValueError, match="boundary mismatch"):
        capture_guild_limit_semantics(
            _registry(),
            RawArchive(tmp_path / "raw"),
            route_review_path=review_path,
            query="PrivateNeedle",
            low_limit=1,
            high_limit=25,
            private_output_path=tmp_path / "limit.private.json",
            receipt_output_path=tmp_path / "limit.json",
            curl_executable="curl",
            runner=runner,
        )

    assert runner.commands == []
