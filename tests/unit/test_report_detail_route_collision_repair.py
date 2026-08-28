from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import duckdb

from coa_workbench.collector.raw_archive import RawArchive
from coa_workbench.collector.source_acquisition import observe_reviewed_har
from coa_workbench.collector.source_observatory import ReviewedGetContract


def test_route_collision_repair_preserves_raw_evidence(tmp_path: Path) -> None:
    database = tmp_path / "coa.duckdb"
    raw_root = tmp_path / "raw"
    migrations = Path("migrations").resolve()
    har = tmp_path / "reports.har"
    har.write_text(
        json.dumps(
            {
                "log": {
                    "entries": [
                        {
                            "startedDateTime": "2026-08-14T10:43:13.616Z",
                            "_resourceType": "xhr",
                            "request": {
                                "method": "GET",
                                "url": "https://coa.ascensionlogs.gg/api/reports/queue-status",
                            },
                            "response": {
                                "status": 200,
                                "content": {
                                    "mimeType": "application/json",
                                    "text": json.dumps(
                                        {
                                            "success": True,
                                            "backlog": 0,
                                            "maintenance": False,
                                        }
                                    ),
                                },
                            },
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    archive = RawArchive(
        raw_root,
        database_path=database,
        migrations_dir=migrations,
    )
    false_dynamic_contract = ReviewedGetContract(
        source_code="coa_ascension_logs",
        endpoint_code="report_detail_api",
        base_url="https://coa.ascensionlogs.gg",
        route_template="/api/reports/{reportId}",
        auth_state="historical_public_observed",
        discovery_source="regression_fixture",
        review_state="verified",
        logical_name="report_detail_observation",
    )

    observations = observe_reviewed_har(
        har,
        archive=archive,
        database_path=database,
        migrations_dir=migrations,
        contract=false_dynamic_contract,
    )
    assert len(observations) == 1

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/repair_report_detail_route_collision.py",
            "--database",
            str(database),
            "--migrations",
            str(migrations),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(completed.stdout)
    assert result["status"] == "repaired"
    assert result["removed_acquisition_count"] == 1
    assert result["removed_capture_count"] == 1
    assert result["raw_objects_deleted"] is False
    assert result["raw_fetch_observations_deleted"] is False

    with duckdb.connect(str(database), read_only=True) as connection:
        assert (
            connection.execute(
                """
                SELECT COUNT(*) FROM source_acquisition_observation
                WHERE endpoint_code = 'report_detail_api'
                """
            ).fetchone()[0]
            == 0
        )
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM source_endpoint WHERE endpoint_code = 'report_detail_api'"
            ).fetchone()[0]
            == 0
        )
        assert connection.execute("SELECT COUNT(*) FROM raw_object").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM raw_fetch_observation").fetchone()[0] == 1
        assert connection.execute("SELECT endpoint_id FROM raw_object").fetchone()[0] is None
