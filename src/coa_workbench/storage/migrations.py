from __future__ import annotations

import hashlib
from pathlib import Path


class DuckDBUnavailableError(RuntimeError):
    pass


_MIGRATION_0005_ID = "0005_canonical_normalization"
_MIGRATION_0005_UNSUPPORTED_SQL = (
    "ALTER TABLE aura_state_interval ADD COLUMN refresh_count INTEGER NOT NULL DEFAULT 0;"
)
_MIGRATION_0005_COMPATIBLE_SQL = """ALTER TABLE aura_state_interval
ADD COLUMN refresh_count INTEGER DEFAULT 0;
UPDATE aura_state_interval SET refresh_count = 0 WHERE refresh_count IS NULL;
ALTER TABLE aura_state_interval ALTER COLUMN refresh_count SET NOT NULL;"""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _sql_for_execution(migration_id: str, source_sql: str) -> str:
    """Return the SQL DuckDB can execute without changing the migration source."""
    if migration_id != _MIGRATION_0005_ID:
        return source_sql

    occurrence_count = source_sql.count(_MIGRATION_0005_UNSUPPORTED_SQL)
    if occurrence_count != 1:
        raise RuntimeError(
            f"Migration {_MIGRATION_0005_ID} compatibility expression expected exactly once; "
            f"found {occurrence_count}"
        )
    return source_sql.replace(
        _MIGRATION_0005_UNSUPPORTED_SQL,
        _MIGRATION_0005_COMPATIBLE_SQL,
        1,
    )


def apply_migrations(database_path: Path, migrations_dir: Path) -> list[str]:
    """Apply ordered SQL migrations to DuckDB and record their checksums."""
    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover - depends on runtime packaging
        raise DuckDBUnavailableError(
            "DuckDB is not installed. Install project dependencies with `uv sync` before init-db."
        ) from exc

    database_path.parent.mkdir(parents=True, exist_ok=True)
    migration_files = sorted(migrations_dir.glob("*.sql"))
    applied: list[str] = []

    with duckdb.connect(str(database_path)) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migration (
                migration_id VARCHAR PRIMARY KEY,
                checksum_sha256 VARCHAR NOT NULL,
                applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        existing = {
            row[0]: row[1]
            for row in connection.execute(
                "SELECT migration_id, checksum_sha256 FROM schema_migration"
            ).fetchall()
        }
        for migration in migration_files:
            migration_id = migration.stem
            checksum = _sha256(migration)
            if migration_id in existing:
                if existing[migration_id] != checksum:
                    raise RuntimeError(
                        f"Applied migration {migration_id} changed: {existing[migration_id]} != {checksum}"
                    )
                continue
            source_sql = migration.read_text(encoding="utf-8")
            sql = _sql_for_execution(migration_id, source_sql)
            connection.execute("BEGIN TRANSACTION")
            try:
                connection.execute(sql)
                connection.execute(
                    "INSERT INTO schema_migration (migration_id, checksum_sha256) VALUES (?, ?)",
                    [migration_id, checksum],
                )
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise
            applied.append(migration_id)
    return applied
