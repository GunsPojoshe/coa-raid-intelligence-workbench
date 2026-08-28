from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.collector.raw_archive import RawArchive
from coa_workbench.collector.source_acquisition import (
    capture_reviewed_get_observation,
    observe_reviewed_har,
)
from coa_workbench.collector.source_observatory import ReviewedGetContract


duckdb = pytest.importorskip("duckdb")


def _contract() -> ReviewedGetContract:
    return ReviewedGetContract(
        source_code="coa_logs",
        endpoint_code="guild_progression_rankings",
        base_url="https://coa.ascensionlogs.gg",
        route_template="/api/guilds/progression/rankings",
        parameter_keys=("bracket", "difficulty", "location", "phaseId", "realm"),
        auth_state="probe_without_auth",
        discovery_source="archived_spa_review",
        review_state="verified",
        logical_name="Guild progression rankings",
    )


def _har(path: Path, *, status: int, mime_type: str, body: str) -> None:
    payload = {
        "log": {
            "entries": [
                {
                    "startedDateTime": "2026-08-14T08:00:00.000Z",
                    "request": {
                        "method": "GET",
                        "url": "https://coa.ascensionlogs.gg/api/guilds/progression/rankings",
                    },
                    "response": {
                        "status": status,
                        "content": {"mimeType": mime_type, "text": body},
                    },
                }
            ]
        }
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_browser_har_json_response_records_schema_and_acquisition(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    database = tmp_path / "coa.duckdb"
    archive = RawArchive(
        tmp_path / "raw",
        database_path=database,
        migrations_dir=root / "migrations",
    )
    har = tmp_path / "capture.har"
    _har(har, status=200, mime_type="application/json", body='{"rows":[{"bossId":1}]}')

    observations = observe_reviewed_har(
        har,
        archive=archive,
        database_path=database,
        migrations_dir=root / "migrations",
        contract=_contract(),
        dimension_keys=("bossId",),
    )
    assert len(observations) == 1
    assert observations[0].outcome == "schema_candidate"
    assert observations[0].source_observation is not None

    with duckdb.connect(str(database)) as connection:
        acquisition = connection.execute(
            """
            SELECT capture_mode, outcome, blocker_class, body_kind, http_status
            FROM source_acquisition_observation
            """
        ).fetchone()
        assert acquisition == ("browser_har", "schema_candidate", None, "json", 200)
        assert connection.execute("SELECT COUNT(*) FROM source_capture").fetchone()[0] == 1
        assert connection.execute(
            "SELECT COUNT(*) FROM source_schema_snapshot"
        ).fetchone()[0] == 1


def test_browser_har_edge_challenge_is_archived_without_schema_claim(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    database = tmp_path / "coa.duckdb"
    archive = RawArchive(
        tmp_path / "raw",
        database_path=database,
        migrations_dir=root / "migrations",
    )
    har = tmp_path / "capture.har"
    challenge = (
        "<!DOCTYPE html><script src='/cdn-cgi/challenge-platform/x'></script>"
        "<iframe src='https://challenges.cloudflare.com/test'></iframe>"
    )
    _har(har, status=403, mime_type="text/html", body=challenge)

    observations = observe_reviewed_har(
        har,
        archive=archive,
        database_path=database,
        migrations_dir=root / "migrations",
        contract=_contract(),
    )
    assert len(observations) == 1
    assert observations[0].outcome == "blocked"
    assert observations[0].blocker_class == "managed_edge_challenge"
    assert observations[0].source_observation is None
    assert observations[0].capture is not None

    with duckdb.connect(str(database)) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM source_acquisition_observation"
        ).fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM source_capture").fetchone()[0] == 0
        assert connection.execute(
            "SELECT COUNT(*) FROM source_schema_snapshot"
        ).fetchone()[0] == 0
        endpoint = connection.execute(
            "SELECT status, schema_fingerprint FROM source_endpoint"
        ).fetchone()
        assert endpoint == ("reviewed", None)


class _Headers:
    def get_content_type(self) -> str:
        return "text/html"


class _Response:
    status = 403
    headers = _Headers()

    def __init__(self, body: bytes) -> None:
        self._body = body
        self._read = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read1(self, _size: int) -> bytes:
        if self._read:
            return b""
        self._read = True
        return self._body


def test_direct_http_edge_challenge_becomes_acquisition_observation(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    database = tmp_path / "coa.duckdb"
    archive = RawArchive(
        tmp_path / "raw",
        database_path=database,
        migrations_dir=root / "migrations",
    )
    challenge = (
        b"<!DOCTYPE html><script src='/cdn-cgi/challenge-platform/x'></script>"
        b"<iframe src='https://challenges.cloudflare.com/test'></iframe>"
    )

    def opener(*_args, **_kwargs):
        return _Response(challenge)

    observation = capture_reviewed_get_observation(
        archive=archive,
        database_path=database,
        migrations_dir=root / "migrations",
        contract=_contract(),
        opener=opener,
    )
    assert observation.capture_mode == "direct_http"
    assert observation.http_status == 403
    assert observation.outcome == "blocked"
    assert observation.blocker_class == "managed_edge_challenge"
    assert observation.source_observation is None

    with duckdb.connect(str(database)) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM source_acquisition_observation"
        ).fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM source_capture").fetchone()[0] == 0
