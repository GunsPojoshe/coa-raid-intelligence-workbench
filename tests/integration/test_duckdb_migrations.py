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
        "0006_aura_interval_provenance",
        "0007_selected_parser_persistence",
        "0008_combatants_observation_persistence",
        "0009_source_observatory",
        "0010_source_acquisition_observation",
        "0011_source_dimension_index",
        "0012_profile_schema_cycle",
        "0013_public_api_statistics",
    ]
    assert apply_migrations(database, root / "migrations") == []
    with duckdb.connect(str(database)) as connection:
        tables = {row[0] for row in connection.execute("SHOW TABLES").fetchall()}
        source_endpoint_columns = {
            row[0] for row in connection.execute("DESCRIBE source_endpoint").fetchall()
        }
        source_acquisition_columns = {
            row[0]
            for row in connection.execute(
                "DESCRIBE source_acquisition_observation"
            ).fetchall()
        }
        source_dimension_index_columns = {
            row[0]
            for row in connection.execute(
                "DESCRIBE source_dimension_index_value"
            ).fetchall()
        }
        source_profile_schema_cycle_columns = {
            row[0]
            for row in connection.execute(
                "DESCRIBE source_profile_schema_cycle"
            ).fetchall()
        }
        public_statistics_batch_columns = {
            row[0]
            for row in connection.execute("DESCRIBE public_api_statistics_batch").fetchall()
        }
        public_statistics_spec_columns = {
            row[0]
            for row in connection.execute("DESCRIBE public_api_statistics_spec").fetchall()
        }
        population_prior_columns = {
            row[0]
            for row in connection.execute("DESCRIBE public_api_population_prior_v1").fetchall()
        }
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
        persistence_run_columns = {
            row[0]
            for row in connection.execute("DESCRIBE parser_slice_persistence_run").fetchall()
        }
        entity_observation_columns = {
            row[0]
            for row in connection.execute("DESCRIBE canonical_entity_observation").fetchall()
        }
        combatants_run_columns = {
            row[0]
            for row in connection.execute(
                "DESCRIBE combatants_observation_persistence_run"
            ).fetchall()
        }
        combatants_parser_view_columns = {
            row[0]
            for row in connection.execute(
                "DESCRIBE combatants_parser_observation_v1"
            ).fetchall()
        }
        combatants_actor_view_columns = {
            row[0]
            for row in connection.execute(
                "DESCRIBE combatants_actor_build_observation_v1"
            ).fetchall()
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
        "parser_slice_persistence_run",
        "canonical_entity_observation",
        "combatants_observation_persistence_run",
        "combatants_parser_observation_v1",
        "combatants_actor_build_observation_v1",
        "source_contract_version",
        "source_capture",
        "source_schema_snapshot",
        "source_change_event",
        "artifact_dependency",
        "analysis_run",
        "reanalysis_request",
        "source_acquisition_observation",
        "source_dimension_index_value",
        "source_profile_schema_cycle",
        "public_api_statistics_batch",
        "public_api_statistics_class",
        "public_api_statistics_spec",
        "public_api_population_prior_v1",
    } <= tables
    assert {
        "source_code",
        "logical_name",
        "first_seen_at",
        "last_seen_at",
    } <= source_endpoint_columns
    assert {
        "acquisition_id",
        "contract_id",
        "source_code",
        "endpoint_code",
        "observed_at",
        "capture_mode",
        "request_fingerprint",
        "raw_id",
        "raw_observation_id",
        "source_capture_id",
        "http_status",
        "content_type",
        "body_kind",
        "outcome",
        "blocker_class",
        "error_class",
        "metadata_json",
    } <= source_acquisition_columns
    assert {
        "analysis_run_id",
        "artifact_key",
        "source_code",
        "endpoint_code",
        "dimension_name",
        "dimension_value",
    } <= source_dimension_index_columns
    assert {
        "cycle_snapshot_id",
        "source_code",
        "endpoint_code",
        "contract_id",
        "observation_profile_key",
        "cycle_fingerprint",
        "observed_at",
        "member_capture_count",
        "member_capture_ids_json",
        "schema_fingerprint",
        "root_type",
        "path_types_json",
        "dimension_values_json",
        "scan_truncated",
        "metadata_json",
    } <= source_profile_schema_cycle_columns
    assert {
        "batch_id",
        "raw_id",
        "source_code",
        "endpoint_code",
        "normalizer_version",
        "phase_number",
        "difficulty",
        "metric",
        "bracket",
        "location",
        "boss_id",
        "damage_mode",
        "role",
        "class_filter",
        "spec_filter",
        "week_number",
        "realm",
        "day_number",
        "class_count",
        "spec_record_count",
        "percentile_value_count",
        "output_fingerprint",
        "metadata_json",
    } <= public_statistics_batch_columns
    assert {
        "batch_id",
        "class_name",
        "spec_name",
        "avg",
        "median",
        "max",
        "min",
        "total_parses",
        "percentiles_json",
    } <= public_statistics_spec_columns
    assert {
        "phase_number",
        "difficulty",
        "metric",
        "damage_mode",
        "role",
        "class_name",
        "spec_name",
        "total_parses",
        "local_parse_share",
    } <= population_prior_columns
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
    assert {
        "max_stack_count",
        "refresh_count",
        "termination_reason",
        "state_status",
        "metadata_json",
    } <= interval_columns
    assert {
        "persistence_run_id",
        "reconstruction_sha256",
        "reconstruction_version",
        "persisted_counts_json",
        "source_batch_hashes_json",
    } <= persistence_run_columns
    assert {
        "observation_id",
        "persistence_run_id",
        "entity_type",
        "entity_key",
        "entity_hash",
        "source_batch_ids_json",
        "provenance_type",
        "trust_status",
        "entity_json",
    } <= entity_observation_columns
    assert {
        "persistence_run_id",
        "promotion_receipt_sha256",
        "promotion_version",
        "private_extraction_sha256",
        "source_payload_hash",
        "schema_fingerprint",
        "design_counts_json",
        "observation_count",
        "reviewed_by",
        "reviewed_at",
    } <= combatants_run_columns
    assert {
        "storage_observation_id",
        "persistence_run_id",
        "entity_type",
        "source_observation_id",
        "design_id",
        "report_id",
        "encounter_id",
        "actor_id",
        "source_actor_id",
        "selected_record_sha256",
        "selected_fields_json",
    } <= combatants_parser_view_columns
    assert {
        "storage_observation_id",
        "persistence_run_id",
        "entity_type",
        "actor_id",
        "source_actor_id",
        "selected_fields_json",
    } <= combatants_actor_view_columns
