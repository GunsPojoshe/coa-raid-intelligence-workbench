from pathlib import Path

import pytest

from coa_workbench.storage.migrations import apply_migrations


duckdb = pytest.importorskip("duckdb")


def test_migrations_apply_idempotently(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    database = tmp_path / "coa.duckdb"
    assert apply_migrations(database, root / "migrations") == ["0001_initial"]
    assert apply_migrations(database, root / "migrations") == []
    with duckdb.connect(str(database)) as connection:
        tables = {row[0] for row in connection.execute("SHOW TABLES").fetchall()}
    assert {"source_endpoint", "raw_object", "raid_plan", "raid_slot", "job"} <= tables
