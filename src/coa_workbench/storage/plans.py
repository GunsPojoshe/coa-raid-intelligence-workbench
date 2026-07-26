from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any
from uuid import uuid4

from coa_workbench.storage.migrations import apply_migrations


class PlanNotFoundError(LookupError):
    pass


class PlanRepository:
    def __init__(self, database_path: Path, migrations_dir: Path) -> None:
        self.database_path = database_path
        self.migrations_dir = migrations_dir

    def initialize(self) -> None:
        apply_migrations(self.database_path, self.migrations_dir)

    def _connect(self):
        import duckdb

        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        return duckdb.connect(str(self.database_path))

    def save(self, payload: dict[str, Any]) -> str:
        self.initialize()
        plan_id = payload.get("plan_id") or uuid4().hex
        with self._connect() as connection:
            exists = connection.execute(
                "SELECT 1 FROM raid_plan WHERE plan_id = ?", [plan_id]
            ).fetchone()
            if exists:
                connection.execute(
                    """
                    UPDATE raid_plan
                    SET plan_name = ?, raid_date = ?, boss_id = ?, raid_format = ?,
                        target_size = ?, ruleset_version = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE plan_id = ?
                    """,
                    [
                        payload["plan_name"], payload.get("raid_date"), payload.get("boss_id"),
                        payload["raid_format"], payload["target_size"], "web-v1", "draft", plan_id,
                    ],
                )
                connection.execute("DELETE FROM raid_slot WHERE plan_id = ?", [plan_id])
            else:
                connection.execute(
                    """
                    INSERT INTO raid_plan (
                        plan_id, plan_name, raid_date, boss_id, raid_format, target_size,
                        ruleset_version, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        plan_id, payload["plan_name"], payload.get("raid_date"), payload.get("boss_id"),
                        payload["raid_format"], payload["target_size"], "web-v1", "draft",
                    ],
                )
            for slot in payload["slots"]:
                connection.execute(
                    """
                    INSERT INTO raid_slot (
                        plan_id, slot_no, active, locked, player_name, class_code, spec_code, role
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        plan_id, slot["slot_no"], slot["active"], slot["locked"],
                        slot["player_name"] or None, slot["class_code"] or None,
                        slot["spec_code"] or None, slot["role"] or None,
                    ],
                )
        return plan_id

    def list(self) -> list[dict[str, Any]]:
        self.initialize()
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT plan_id, COALESCE(plan_name, ''), raid_format, target_size, status,
                       CAST(updated_at AS VARCHAR)
                FROM raid_plan ORDER BY updated_at DESC
                """
            ).fetchall()
        return [
            {"plan_id": row[0], "plan_name": row[1], "raid_format": row[2],
             "target_size": row[3], "status": row[4], "updated_at": row[5]}
            for row in rows
        ]

    def get(self, plan_id: str) -> dict[str, Any]:
        self.initialize()
        with self._connect() as connection:
            plan = connection.execute(
                """
                SELECT plan_id, COALESCE(plan_name, ''), raid_date, boss_id, raid_format,
                       target_size, status FROM raid_plan WHERE plan_id = ?
                """,
                [plan_id],
            ).fetchone()
            if not plan:
                raise PlanNotFoundError(plan_id)
            slots = connection.execute(
                """
                SELECT slot_no, active, COALESCE(player_name, ''), COALESCE(class_code, ''),
                       COALESCE(spec_code, ''), COALESCE(role, ''), locked
                FROM raid_slot WHERE plan_id = ? ORDER BY slot_no
                """,
                [plan_id],
            ).fetchall()
        return {
            "plan_id": plan[0], "plan_name": plan[1],
            "raid_date": plan[2].isoformat() if isinstance(plan[2], date) else plan[2],
            "boss_id": plan[3] or "", "raid_format": plan[4], "target_size": plan[5],
            "status": plan[6],
            "slots": [
                {"slot_no": row[0], "active": row[1], "player_name": row[2],
                 "class_code": row[3], "spec_code": row[4], "role": row[5], "locked": row[6]}
                for row in slots
            ],
        }

    def delete(self, plan_id: str) -> None:
        self.initialize()
        with self._connect() as connection:
            exists = connection.execute("SELECT 1 FROM raid_plan WHERE plan_id = ?", [plan_id]).fetchone()
            if not exists:
                raise PlanNotFoundError(plan_id)
            connection.execute("DELETE FROM raid_slot WHERE plan_id = ?", [plan_id])
            connection.execute("DELETE FROM raid_plan WHERE plan_id = ?", [plan_id])
