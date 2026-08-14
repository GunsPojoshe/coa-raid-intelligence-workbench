from __future__ import annotations

import json
from pathlib import Path

import pytest

from coa_workbench.collector.current_report_dependencies import (
    register_current_report_scoped_dependencies,
)
from coa_workbench.collector.raw_archive import RawArchive
from coa_workbench.collector.source_acquisition import observe_reviewed_har
from coa_workbench.collector.source_observatory import ReviewedGetContract
from coa_workbench.collector.source_registry import load_source_registry
from coa_workbench.storage.current_report_observations import (
    CURRENT_REPORT_PERSISTENCE_VERSION,
)


duckdb = pytest.importorskip("duckdb")


def _entry(path: str, body: dict[str, object], timestamp: str) -> dict[str, object]:
    return {
        "startedDateTime": timestamp,
        "_resourceType": "xhr",
        "request": {
            "method": "GET",
            "url": f"https://coa.ascensionlogs.gg{path}",
        },
        "response": {
            "status": 200,
            "content": {
                "mimeType": "application/json",
                "text": json.dumps(body),
            },
        },
    }


def test_current_report_dependencies_share_one_private_report_scope(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    migrations = root / "migrations"
    registry = load_source_registry(root / "config" / "ascension_logs_sources.yaml")
    database = tmp_path / "coa.duckdb"
    archive = RawArchive(
        tmp_path / "raw",
        database_path=database,
        migrations_dir=migrations,
    )
    har = tmp_path / "report.har"
    har.write_text(
        json.dumps(
            {
                "log": {
                    "entries": [
                        _entry(
                            "/api/reports/123",
                            {"success": True, "report": {"id": 123}},
                            "2026-08-14T12:00:00.000Z",
                        ),
                        _entry(
                            "/api/reports/123/encounters?includeTrash=false",
                            {"success": True, "encounters": []},
                            "2026-08-14T12:00:00.010Z",
                        ),
                        _entry(
                            "/api/reports/123/combatants-roster?encounterIds=1",
                            {"success": True, "roster": []},
                            "2026-08-14T12:00:00.020Z",
                        ),
                    ]
                }
            }
        ),
        encoding="utf-8",
    )

    identities: dict[str, dict[str, str]] = {}
    for endpoint_code in (
        "report_detail_api",
        "report_encounters_api",
        "report_combatants_roster_api",
    ):
        route = registry.route(endpoint_code)
        contract = ReviewedGetContract(
            source_code=registry.source_code,
            endpoint_code=route.endpoint_code,
            base_url=registry.base_url,
            route_template=str(route.route_template),
            parameter_keys=route.parameter_keys,
            auth_state=route.auth_mode,
            discovery_source="test",
            review_state="verified",
        )
        observations = observe_reviewed_har(
            har,
            archive=archive,
            database_path=database,
            migrations_dir=migrations,
            contract=contract,
        )
        assert len(observations) == 1
        observation = observations[0]
        assert observation.capture is not None
        assert observation.source_observation is not None
        identities[endpoint_code] = {
            "capture_id": observation.source_observation.source_capture_id,
            "raw_id": observation.capture.raw_id,
            "payload_hash": observation.capture.payload_hash,
        }

    artifact_key = "a" * 64
    with duckdb.connect(str(database)) as connection:
        connection.execute(
            """
            INSERT INTO parser_slice_persistence_run (
                persistence_run_id, reconstruction_sha256, reconstruction_version,
                source_code, source_normalization_name, status, input_counts_json,
                persisted_counts_json, source_batch_hashes_json, metadata_json,
                finished_at
            ) VALUES (?, ?, ?, ?, ?, 'completed', '{}', '{}', ?, '{}', CURRENT_TIMESTAMP)
            """,
            [
                "persistence-run",
                artifact_key,
                CURRENT_REPORT_PERSISTENCE_VERSION,
                registry.source_code,
                "coa-report-detail-v1",
                json.dumps(identities, sort_keys=True),
            ],
        )
        connection.execute(
            """
            INSERT INTO analysis_run (
                analysis_run_id, analysis_type, analysis_version, artifact_type,
                artifact_key, target_scope_json, input_fingerprint, output_fingerprint,
                status, metadata_json, finished_at
            ) VALUES (?, ?, ?, ?, ?, '{}', ?, ?, 'completed', '{}', CURRENT_TIMESTAMP)
            """,
            [
                "analysis-run",
                "current_report_runtime_parse",
                CURRENT_REPORT_PERSISTENCE_VERSION,
                "current_report_derived_observations",
                artifact_key,
                artifact_key,
                "b" * 64,
            ],
        )

    first = register_current_report_scoped_dependencies(
        database,
        migrations,
        registry=registry,
        artifact_key=artifact_key,
    )
    second = register_current_report_scoped_dependencies(
        database,
        migrations,
        registry=registry,
        artifact_key=artifact_key,
    )

    assert first.dependency_count == 3
    assert second.dependency_count == 3
    assert first.scope_path_keys == ("reportId",)
    public = first.public_summary()
    assert public["scope_values_included"] is False
    assert public["scope_fingerprints_included"] is False
    assert public["source_capture_ids_included"] is False

    with duckdb.connect(str(database), read_only=True) as connection:
        rows = connection.execute(
            """
            SELECT dependency_key, dependency_version, metadata_json
            FROM artifact_dependency
            WHERE artifact_type = 'current_report_derived_observations'
              AND artifact_key = ?
              AND dependency_type = 'source_endpoint_scope'
            ORDER BY dependency_key
            """,
            [artifact_key],
        ).fetchall()
    assert len(rows) == 3
    assert len({str(row[1]) for row in rows}) == 1
    assert all(str(row[1]) for row in rows)
    for endpoint_code, _scope_fingerprint, metadata_json in rows:
        assert str(endpoint_code) in first.endpoint_codes
        metadata = json.loads(str(metadata_json))
        assert metadata["scope_path_keys"] == ["reportId"]
        assert metadata["scope_values_included"] is False
        assert metadata["scope_fingerprint_public"] is False
