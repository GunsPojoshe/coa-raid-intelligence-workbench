from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

from coa_workbench.storage.combatants_observations import (
    persist_observed_combatants_info_observations,
)
from coa_workbench.storage.migrations import apply_migrations


duckdb = pytest.importorskip("duckdb")


def _promotion_test_module() -> ModuleType:
    path = Path(__file__).resolve().parents[1] / "unit" / "test_combatants_candidate_promotion.py"
    spec = importlib.util.spec_from_file_location("combatants_candidate_promotion_test_support", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load combatants promotion test support")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _packet(tmp_path: Path) -> tuple[Path, Path, Path, dict[str, object]]:
    support = _promotion_test_module()
    extraction_receipt_path, private_path = support._packet(tmp_path)
    promotion = support._promote(extraction_receipt_path, private_path)
    promotion_path = tmp_path / "observed-combatants-info-candidate-promotion.json"
    _write(promotion_path, promotion)
    private_payload = json.loads(private_path.read_text(encoding="utf-8"))
    return promotion_path, extraction_receipt_path, private_path, private_payload


def _seed_core(database: Path, private_payload: dict[str, object], *, omit_last_actor: bool = False) -> None:
    report_id = private_payload["report_id"]
    encounter_id = private_payload["encounter_id"]
    actor_rows = private_payload["observations"]["coa-combatants-actor-enrichment-v1"]
    if omit_last_actor:
        actor_rows = actor_rows[:-1]
    with duckdb.connect(str(database)) as connection:
        connection.execute(
            """
            INSERT INTO report (report_id, source_report_id, status)
            VALUES (?, ?, ?)
            """,
            [report_id, "PRIVATE-REPORT", "observed"],
        )
        connection.execute(
            """
            INSERT INTO encounter (
                encounter_id,
                source_encounter_id,
                report_id,
                data_quality_status
            ) VALUES (?, ?, ?, ?)
            """,
            [encounter_id, "PRIVATE-ENCOUNTER", report_id, "observed_parser_verified"],
        )
        for row in actor_rows:
            connection.execute(
                """
                INSERT INTO actor (actor_id, source_actor_id, nickname, actor_type)
                VALUES (?, ?, ?, ?)
                """,
                [
                    row["actor_id"],
                    row["source_actor_id"],
                    row["selected_fields"]["field_4"],
                    "player",
                ],
            )


def _persist(
    root: Path,
    database: Path,
    promotion_path: Path,
    extraction_receipt_path: Path,
    private_path: Path,
) -> dict[str, object]:
    return persist_observed_combatants_info_observations(
        promotion_path,
        extraction_receipt_path=extraction_receipt_path,
        private_extraction_path=private_path,
        database_path=database,
        migrations_path=root / "migrations",
    )


def test_persists_promoted_combatants_observations_idempotently(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    promotion_path, extraction_receipt_path, private_path, private_payload = _packet(tmp_path)
    database = tmp_path / "coa.duckdb"
    apply_migrations(database, root / "migrations")
    _seed_core(database, private_payload)

    first = _persist(
        root,
        database,
        promotion_path,
        extraction_receipt_path,
        private_path,
    )
    second = _persist(
        root,
        database,
        promotion_path,
        extraction_receipt_path,
        private_path,
    )

    assert first["summary"]["persisted_observation_count"] == 1343
    assert first["summary"]["actor_build_observation_count"] == 1339
    assert first["summary"]["linked_actor_count"] == 11
    assert first["summary"]["transaction_committed"] is True
    assert first["summary"]["core_entity_mutation_performed"] is False
    assert first["summary"]["planner_scoring_allowed"] is False
    assert first["decision_boundary"]["ready_for_actor_build_observation_queries"] is True
    assert first["database_changes"]["persistence_runs"] == {"inserted": 1, "matched": 0}
    assert first["database_changes"]["canonical_entity_observations"] == {
        "inserted": 1343,
        "matched": 0,
    }
    assert second["database_changes"]["persistence_runs"] == {"inserted": 0, "matched": 1}
    assert second["database_changes"]["canonical_entity_observations"] == {
        "inserted": 0,
        "matched": 1343,
    }
    assert "PRIVATE" not in json.dumps(first, ensure_ascii=False)

    with duckdb.connect(str(database)) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM combatants_observation_persistence_run"
        ).fetchone()[0] == 1
        assert connection.execute(
            """
            SELECT COUNT(*) FROM canonical_entity_observation
            WHERE trust_status = 'verified_parser_observation'
            """
        ).fetchone()[0] == 1343
        assert connection.execute(
            "SELECT COUNT(*) FROM combatants_parser_observation_v1"
        ).fetchone()[0] == 1343
        assert connection.execute(
            "SELECT COUNT(*) FROM combatants_actor_build_observation_v1"
        ).fetchone()[0] == 1339
        assert connection.execute(
            "SELECT COUNT(DISTINCT actor_id) FROM combatants_actor_build_observation_v1"
        ).fetchone()[0] == 11


def test_rolls_back_when_a_promoted_actor_is_missing_from_core_storage(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    promotion_path, extraction_receipt_path, private_path, private_payload = _packet(tmp_path)
    database = tmp_path / "coa.duckdb"
    apply_migrations(database, root / "migrations")
    _seed_core(database, private_payload, omit_last_actor=True)

    with pytest.raises(ValueError, match="actor references are incomplete"):
        _persist(
            root,
            database,
            promotion_path,
            extraction_receipt_path,
            private_path,
        )

    with duckdb.connect(str(database)) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM combatants_observation_persistence_run"
        ).fetchone()[0] == 0
        assert connection.execute(
            """
            SELECT COUNT(*) FROM canonical_entity_observation
            WHERE trust_status = 'verified_parser_observation'
            """
        ).fetchone()[0] == 0
