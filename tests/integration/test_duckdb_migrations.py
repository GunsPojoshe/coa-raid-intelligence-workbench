from pathlib import Path

import pytest

from coa_workbench.storage.migrations import apply_migrations


duckdb = pytest.importorskip("duckdb")


def test_migrations_apply_idempotently(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    database = tmp_path / "coa.duckdb"
    assert apply_migrations(database, root / "migrations") == [
        "0001_initial",
        "0002_web_plan_fields",
        "0003_log_evidence_refactor",
        "0004_raw_capture_archive",
        "0005_canonical_normalization",
    ]
    assert apply_migrations(database, root / "migrations") == []
    with duckdb.connect(str(database)) as connection:
        tables = {row[0] for row in connection.execute("SHOW TABLES").fetchall()}
        raid_plan_columns = {
            row[0] for row in connection.execute("DESCRIBE raid_plan").fetchall()
        }
        raid_slot_columns = {
            row[0] for row in connection.execute("DESCRIBE raid_slot").fetchall()
        }
        effect_columns = {
            row[0] for row in connection.execute("DESCRIBE effect_family").fetchall()
        }
        capability_columns = {
            row[0] for row in connection.execute("DESCRIBE provider_capability").fetchall()
        }
        raw_fetch_columns = {
            row[0]
            for row in connection.execute("DESCRIBE raw_fetch_observation").fetchall()
        }
        interval_columns = {
            row[0]
            for row in connection.execute("DESCRIBE aura_state_interval").fetchall()
        }
    assert {"source_endpoint", "raw_object", "raid_plan", "raid_slot", "job"} <= tables
    assert {
        "observation_batch",
        "aura_observation",
        "aura_state_interval",
        "mechanic_hypothesis",
        "hypothesis_evidence_link",
        "evidence_weight_policy",
        "mechanic_inference_run",
        "source_route_probe",
        "raw_fetch_observation",
        "payload_schema_profile",
        "normalization_mapping",
        "normalization_run",
        "normalization_reject",
    } <= tables
    assert "plan_name" in raid_plan_columns
    assert {"player_name", "class_code", "spec_code", "role"} <= raid_slot_columns
    assert {"trust_status", "source_kind"} <= effect_columns
    assert {"trust_status", "source_kind"} <= capability_columns
    assert {
        "observation_id",
        "raw_id",
        "fetched_at",
        "request_url_sanitized",
    } <= raw_fetch_columns
    assert {"max_stack_count", "refresh_count", "termination_reason"} <= interval_columns
