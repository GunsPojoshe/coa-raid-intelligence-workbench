from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

import pytest

from coa_workbench.storage.migrations import apply_migrations


duckdb = pytest.importorskip("duckdb")
ROOT = Path(__file__).resolve().parents[2]
MIGRATION_0005 = "0005_canonical_normalization.sql"


def copy_migrations(destination: Path, *, through: int = 5) -> None:
    destination.mkdir()
    for migration in sorted((ROOT / "migrations").glob("*.sql")):
        if int(migration.name[:4]) <= through:
            shutil.copyfile(migration, destination / migration.name)


def test_migration_0005_compatibility_preserves_data_schema_and_checksum(tmp_path: Path) -> None:
    migrations = tmp_path / "migrations"
    copy_migrations(migrations, through=4)
    database = tmp_path / "coa.duckdb"

    assert apply_migrations(database, migrations) == [
        "0001_initial",
        "0002_web_plan_fields",
        "0003_log_evidence_refactor",
        "0004_raw_capture_archive",
    ]
    with duckdb.connect(str(database)) as connection:
        connection.execute(
            """
            INSERT INTO aura_state_interval (
                interval_id, encounter_id, spell_id, target_actor_id,
                started_at_ms, reconstruction_version
            ) VALUES ('interval-1', 'encounter-1', 'spell-1', 'target-1', 10, 'test-v1')
            """
        )

    source_0005 = ROOT / "migrations" / MIGRATION_0005
    copied_0005 = migrations / MIGRATION_0005
    shutil.copyfile(source_0005, copied_0005)
    source_checksum = hashlib.sha256(source_0005.read_bytes()).hexdigest()

    assert apply_migrations(database, migrations) == ["0005_canonical_normalization"]
    assert apply_migrations(database, migrations) == []

    with duckdb.connect(str(database)) as connection:
        refresh_column = next(
            row
            for row in connection.execute("DESCRIBE aura_state_interval").fetchall()
            if row[0] == "refresh_count"
        )
        assert refresh_column[2] == "NO"
        assert refresh_column[4] == "0"
        assert connection.execute(
            "SELECT interval_id, refresh_count FROM aura_state_interval"
        ).fetchall() == [("interval-1", 0)]
        recorded = connection.execute(
            "SELECT migration_id, checksum_sha256 FROM schema_migration ORDER BY migration_id"
        ).fetchall()

    assert len(recorded) == 5
    assert recorded[-1] == ("0005_canonical_normalization", source_checksum)

    copied_0005.write_text(copied_0005.read_text(encoding="utf-8") + "\n-- changed\n")
    with pytest.raises(
        RuntimeError, match="Applied migration 0005_canonical_normalization changed"
    ):
        apply_migrations(database, migrations)


def test_migration_0005_requires_the_exact_compatibility_expression(tmp_path: Path) -> None:
    migrations = tmp_path / "migrations"
    copy_migrations(migrations)
    migration = migrations / MIGRATION_0005
    migration.write_text(
        migration.read_text(encoding="utf-8").replace(
            "ALTER TABLE aura_state_interval ADD COLUMN refresh_count INTEGER NOT NULL DEFAULT 0;",
            "ALTER TABLE aura_state_interval ADD COLUMN refresh_count INTEGER DEFAULT 0;",
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        RuntimeError, match="compatibility expression expected exactly once; found 0"
    ):
        apply_migrations(tmp_path / "coa.duckdb", migrations)
