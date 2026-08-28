from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from coa_workbench.collector.compatible_normalization import CompatibleNormalizationResult
from coa_workbench.collector.current_combatants_roster import CurrentRosterParseResult
from coa_workbench.collector.current_report_har import CurrentReportHarSlice, HarJsonObservation
from coa_workbench.collector.raw_archive import request_key_from_url
from coa_workbench.normalizer.canonical import stable_id

from .migrations import apply_migrations

CURRENT_REPORT_PERSISTENCE_VERSION = "current-report-derived-persistence-v1"
_CURRENT_REPORT_ANALYSIS_TYPE = "current_report_runtime_parse"
_CURRENT_REPORT_ARTIFACT_TYPE = "current_report_derived_observations"
_PROVENANCE_TYPE = "source_observatory_current_report_runtime_v1"


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _utc_naive(value: str) -> datetime:
    prepared = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(prepared)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("observation timestamp must include timezone")
    return parsed.astimezone(timezone.utc).replace(tzinfo=None)


def _require_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def _require_array(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    return value


def _resolve_source_capture(
    connection: Any,
    observation: HarJsonObservation,
) -> dict[str, str]:
    request_key = request_key_from_url("GET", observation.request_url)
    rows = connection.execute(
        """
        SELECT sc.capture_id, sc.raw_id, sc.captured_at, cv.last_seen_at
        FROM source_capture AS sc
        JOIN raw_object AS ro ON ro.raw_id = sc.raw_id
        JOIN source_contract_version AS cv ON cv.contract_id = sc.contract_id
        WHERE sc.endpoint_code = ?
          AND ro.request_key = ?
          AND ro.payload_hash = ?
        ORDER BY cv.last_seen_at DESC, sc.captured_at DESC, sc.capture_id DESC
        """,
        [observation.endpoint_code, request_key, observation.payload_hash],
    ).fetchall()
    expected_time = _utc_naive(observation.observed_at)
    exact = [row for row in rows if row[2] == expected_time]
    if not exact:
        raise ValueError(
            f"no persisted Source Observatory capture matches {observation.endpoint_code} "
            "at the HAR observation timestamp"
        )
    capture_id, raw_id = str(exact[0][0]), str(exact[0][1])
    outcome = connection.execute(
        """
        SELECT outcome
        FROM source_acquisition_observation
        WHERE source_capture_id = ?
        ORDER BY observed_at DESC, acquisition_id DESC
        LIMIT 1
        """,
        [capture_id],
    ).fetchone()
    if outcome is None or str(outcome[0]) != "schema_candidate":
        raise ValueError(
            f"source capture for {observation.endpoint_code} is not a schema_candidate"
        )
    return {"capture_id": capture_id, "raw_id": raw_id, "payload_hash": observation.payload_hash}


def _insert_or_match(
    connection: Any,
    *,
    table: str,
    key_fields: tuple[str, ...],
    values: Mapping[str, Any],
) -> str:
    columns = tuple(values)
    where = " AND ".join(f"{field} = ?" for field in key_fields)
    existing = connection.execute(
        f"SELECT {', '.join(columns)} FROM {table} WHERE {where}",
        [values[field] for field in key_fields],
    ).fetchone()
    if existing is None:
        placeholders = ", ".join("?" for _ in columns)
        connection.execute(
            f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
            [values[field] for field in columns],
        )
        return "inserted"
    existing_values = dict(zip(columns, existing, strict=True))
    if existing_values != dict(values):
        raise ValueError(f"existing {table} row conflicts with deterministic current-report output")
    return "matched"


def _observation_row(
    *,
    persistence_run_id: str,
    entity_type: str,
    entity_key: str,
    entity: Mapping[str, Any],
    source_capture_ids: Iterable[str],
) -> dict[str, Any]:
    payload = dict(entity)
    entity_hash = _sha256_json(payload)
    observation_id = stable_id(
        "current_report_derived_observation",
        persistence_run_id,
        entity_type,
        entity_key,
    )
    return {
        "observation_id": observation_id,
        "persistence_run_id": persistence_run_id,
        "entity_type": entity_type,
        "entity_key": entity_key,
        "entity_hash": entity_hash,
        "source_batch_ids_json": _json(sorted(set(source_capture_ids))),
        "provenance_type": _PROVENANCE_TYPE,
        "trust_status": "observed",
        "entity_json": _json(payload),
    }


def _encounter_catalog_entities(
    normalization: CompatibleNormalizationResult,
    encounter_catalog: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if len(normalization.batch.reports) != 1:
        raise ValueError("current report persistence requires exactly one normalized report")
    if normalization.batch.rejects:
        raise ValueError("current report persistence refuses normalized rejects")
    report = normalization.batch.reports[0]
    canonical_report_id = str(report["report_id"])
    source_report_id = str(report["source_report_id"])
    normalized = {
        str(row["source_encounter_id"]): row for row in normalization.batch.encounters
    }
    catalog_rows = _require_array(encounter_catalog.get("encounters"), "encounter_catalog.encounters")
    if len(catalog_rows) != len(normalized):
        raise ValueError(
            "encounter catalog count does not match the verified report-detail encounter set"
        )

    entities: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw_row in enumerate(catalog_rows):
        row = _require_object(raw_row, f"encounter_catalog.encounters[{index}]")
        if "id" not in row:
            raise ValueError("encounter catalog row has no id")
        source_encounter_id = str(row["id"])
        if source_encounter_id in seen:
            raise ValueError("encounter catalog contains duplicate ids")
        seen.add(source_encounter_id)
        normalized_row = normalized.get(source_encounter_id)
        if normalized_row is None:
            raise ValueError("encounter catalog id is absent from verified report-detail mapping")
        expected_id = stable_id(
            "encounter",
            normalization.batch.source_code,
            source_report_id,
            source_encounter_id,
        )
        if str(normalized_row["encounter_id"]) != expected_id:
            raise ValueError("normalized encounter identity is inconsistent")
        entities.append(
            {
                "encounter_id": expected_id,
                "report_id": canonical_report_id,
                "source_encounter_id": source_encounter_id,
                "normalized": normalized_row,
                "catalog_observation": row,
            }
        )
    if set(normalized) != seen:
        raise ValueError("verified report-detail encounters are missing from encounter catalog")
    return entities


def persist_current_report_derived_observations(
    *,
    database_path: Path,
    migrations_path: Path,
    har_slice: CurrentReportHarSlice,
    normalization: CompatibleNormalizationResult,
    roster: CurrentRosterParseResult,
) -> dict[str, Any]:
    """Persist current report parser observations without mutating canonical core entities."""
    apply_migrations(database_path, migrations_path)

    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("DuckDB is required for current report persistence") from exc

    if len(normalization.batch.reports) != 1:
        raise ValueError("current report persistence requires exactly one normalized report")
    if normalization.batch.rejects:
        raise ValueError("current report persistence refuses normalized rejects")

    with duckdb.connect(str(database_path)) as connection:
        source = {
            observation.endpoint_code: _resolve_source_capture(connection, observation)
            for observation in (
                har_slice.report_detail,
                har_slice.encounter_catalog,
                har_slice.combatants_roster,
            )
        }

        input_identity = {
            endpoint_code: {
                "capture_id": value["capture_id"],
                "raw_id": value["raw_id"],
                "payload_hash": value["payload_hash"],
            }
            for endpoint_code, value in sorted(source.items())
        }
        input_fingerprint = _sha256_json(
            {
                "persistence_version": CURRENT_REPORT_PERSISTENCE_VERSION,
                "mapping_id": normalization.batch.mapping_id,
                "mapping_version": normalization.batch.mapping_version,
                "source": input_identity,
            }
        )
        persistence_run_id = stable_id(
            "current_report_derived_persistence_run",
            CURRENT_REPORT_PERSISTENCE_VERSION,
            input_fingerprint,
        )

        report = normalization.batch.reports[0]
        report_id = str(report["report_id"])
        report_capture = source["report_detail_api"]["capture_id"]
        encounter_capture = source["report_encounters_api"]["capture_id"]
        roster_capture = source["report_combatants_roster_api"]["capture_id"]

        rows: list[dict[str, Any]] = []
        rows.append(
            _observation_row(
                persistence_run_id=persistence_run_id,
                entity_type="current_report_observation",
                entity_key=report_id,
                entity=report,
                source_capture_ids=(report_capture,),
            )
        )

        encounter_entities = _encounter_catalog_entities(
            normalization,
            har_slice.encounter_catalog.payload,
        )
        for entity in encounter_entities:
            rows.append(
                _observation_row(
                    persistence_run_id=persistence_run_id,
                    entity_type="current_encounter_observation",
                    entity_key=str(entity["encounter_id"]),
                    entity=entity,
                    source_capture_ids=(report_capture, encounter_capture),
                )
            )

        character_keys: dict[str, str] = {}
        for character in roster.characters:
            source_character_id = str(character["source_character_id"])
            character_key = stable_id(
                "current_roster_character",
                normalization.batch.source_code,
                report_id,
                source_character_id,
            )
            character_keys[source_character_id] = character_key
            rows.append(
                _observation_row(
                    persistence_run_id=persistence_run_id,
                    entity_type="current_roster_character_observation",
                    entity_key=character_key,
                    entity={
                        "current_roster_character_id": character_key,
                        "report_id": report_id,
                        **character,
                    },
                    source_capture_ids=(report_capture, roster_capture),
                )
            )

        snapshot_keys: set[str] = set()
        for snapshot in roster.snapshots:
            source_character_id = str(snapshot["source_character_id"])
            character_key = character_keys.get(source_character_id)
            if character_key is None:
                raise ValueError("roster snapshot references an unknown current roster character")
            snapshot_key = str(snapshot["snapshot_hash"])
            if snapshot_key in snapshot_keys:
                raise ValueError("current roster contains duplicate full snapshot hashes")
            snapshot_keys.add(snapshot_key)
            rows.append(
                _observation_row(
                    persistence_run_id=persistence_run_id,
                    entity_type="current_roster_snapshot_observation",
                    entity_key=snapshot_key,
                    entity={
                        "current_roster_character_id": character_key,
                        "report_id": report_id,
                        **snapshot,
                    },
                    source_capture_ids=(report_capture, roster_capture),
                )
            )

        for talent in roster.talent_entries:
            source_character_id = str(talent["source_character_id"])
            snapshot_key = str(talent["snapshot_hash"])
            if source_character_id not in character_keys or snapshot_key not in snapshot_keys:
                raise ValueError("talent observation references an unknown roster snapshot")
            entity_key = stable_id(
                "current_talent_entry",
                snapshot_key,
                talent["entry_id"],
            )
            rows.append(
                _observation_row(
                    persistence_run_id=persistence_run_id,
                    entity_type="current_talent_entry_observation",
                    entity_key=entity_key,
                    entity={
                        "current_roster_character_id": character_keys[source_character_id],
                        "report_id": report_id,
                        **talent,
                    },
                    source_capture_ids=(roster_capture,),
                )
            )

        for gear in roster.gear_entries:
            source_character_id = str(gear["source_character_id"])
            snapshot_key = str(gear["snapshot_hash"])
            if source_character_id not in character_keys or snapshot_key not in snapshot_keys:
                raise ValueError("gear observation references an unknown roster snapshot")
            entity_key = stable_id(
                "current_gear_slot",
                snapshot_key,
                gear["slot_key"],
            )
            rows.append(
                _observation_row(
                    persistence_run_id=persistence_run_id,
                    entity_type="current_gear_slot_observation",
                    entity_key=entity_key,
                    entity={
                        "current_roster_character_id": character_keys[source_character_id],
                        "report_id": report_id,
                        **gear,
                    },
                    source_capture_ids=(roster_capture,),
                )
            )

        counts: dict[str, int] = {}
        for row in rows:
            entity_type = str(row["entity_type"])
            counts[entity_type] = counts.get(entity_type, 0) + 1
        output_fingerprint = _sha256_json(
            sorted((str(row["entity_type"]), str(row["entity_key"]), str(row["entity_hash"])) for row in rows)
        )

        run_values = {
            "persistence_run_id": persistence_run_id,
            "reconstruction_sha256": input_fingerprint,
            "reconstruction_version": CURRENT_REPORT_PERSISTENCE_VERSION,
            "source_code": normalization.batch.source_code,
            "source_normalization_name": normalization.batch.mapping_id,
            "status": "completed",
            "input_counts_json": _json(
                {
                    "source_capture_count": len(source),
                    "normalized_report_count": len(normalization.batch.reports),
                    "normalized_encounter_count": len(normalization.batch.encounters),
                    "roster_character_count": len(roster.characters),
                    "roster_snapshot_count": len(roster.snapshots),
                }
            ),
            "persisted_counts_json": _json(counts),
            "source_batch_hashes_json": _json(input_identity),
            "metadata_json": _json(
                {
                    "persistence_version": CURRENT_REPORT_PERSISTENCE_VERSION,
                    "provenance_type": _PROVENANCE_TYPE,
                    "core_entity_mutation_allowed": False,
                    "mechanic_semantics_verified": False,
                    "planner_scoring_allowed": False,
                }
            ),
        }

        connection.execute("BEGIN TRANSACTION")
        try:
            _insert_or_match(
                connection,
                table="parser_slice_persistence_run",
                key_fields=("persistence_run_id",),
                values=run_values,
            )
            inserted = 0
            matched = 0
            for row in rows:
                result = _insert_or_match(
                    connection,
                    table="canonical_entity_observation",
                    key_fields=("observation_id",),
                    values=row,
                )
                if result == "inserted":
                    inserted += 1
                else:
                    matched += 1

            analysis_run_id = stable_id(
                "analysis_run",
                _CURRENT_REPORT_ANALYSIS_TYPE,
                CURRENT_REPORT_PERSISTENCE_VERSION,
                input_fingerprint,
            )
            analysis_values = {
                "analysis_run_id": analysis_run_id,
                "analysis_type": _CURRENT_REPORT_ANALYSIS_TYPE,
                "analysis_version": CURRENT_REPORT_PERSISTENCE_VERSION,
                "artifact_type": _CURRENT_REPORT_ARTIFACT_TYPE,
                "artifact_key": input_fingerprint,
                "target_scope_json": _json(
                    {
                        "scope": "one_private_current_report_slice",
                        "source_capture_count": len(source),
                    }
                ),
                "input_fingerprint": input_fingerprint,
                "output_fingerprint": output_fingerprint,
                "status": "completed",
                "metadata_json": _json(
                    {
                        "persisted_counts": counts,
                        "core_entity_mutation_allowed": False,
                        "mechanic_semantics_verified": False,
                        "planner_scoring_allowed": False,
                    }
                ),
            }
            _insert_or_match(
                connection,
                table="analysis_run",
                key_fields=("analysis_run_id",),
                values=analysis_values,
            )
            connection.execute(
                """
                UPDATE parser_slice_persistence_run
                SET finished_at = COALESCE(finished_at, CURRENT_TIMESTAMP)
                WHERE persistence_run_id = ?
                """,
                [persistence_run_id],
            )
            connection.execute(
                """
                UPDATE analysis_run
                SET finished_at = COALESCE(finished_at, CURRENT_TIMESTAMP)
                WHERE analysis_run_id = ?
                """,
                [analysis_run_id],
            )
            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise

    return {
        "persistence_version": CURRENT_REPORT_PERSISTENCE_VERSION,
        "status": "completed",
        "source_capture_count": len(source),
        "entity_count": len(rows),
        "entity_counts": dict(sorted(counts.items())),
        "inserted_observation_count": inserted,
        "matched_observation_count": matched,
        "input_fingerprint": input_fingerprint,
        "output_fingerprint": output_fingerprint,
        "contains_source_scalar_values": False,
        "contains_source_capture_ids": False,
        "core_entity_mutation_allowed": False,
        "mechanic_semantics_verified": False,
        "planner_scoring_allowed": False,
        "reanalysis_dependencies_registered": False,
    }


__all__ = [
    "CURRENT_REPORT_PERSISTENCE_VERSION",
    "persist_current_report_derived_observations",
]
