from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from coa_workbench.collector.current_report_analytics import CurrentReportAnalyticsParseResult
from coa_workbench.collector.current_report_har import CurrentReportHarSlice, HarJsonObservation
from coa_workbench.collector.raw_archive import request_key_from_url
from coa_workbench.normalizer.canonical import stable_id

from .migrations import apply_migrations

CURRENT_REPORT_ANALYTICS_PERSISTENCE_VERSION = "current-report-analytics-persistence-v1"
_CURRENT_ANALYSIS_TYPE = "current_report_analytics_parse"
_CURRENT_ARTIFACT_TYPE = "current_report_analytics_read_model"
_PROVENANCE_TYPE = "source_observatory_current_report_analytics_v1"


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
    return {
        "capture_id": capture_id,
        "raw_id": raw_id,
        "payload_hash": observation.payload_hash,
    }


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
        raise ValueError(f"existing {table} row conflicts with deterministic analytics output")
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
        "current_report_analytics_observation",
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


def _source_identity(
    connection: Any,
    har_slice: CurrentReportHarSlice,
) -> tuple[dict[str, list[dict[str, str]]], dict[int, str]]:
    observations = (
        har_slice.report_detail,
        har_slice.encounter_catalog,
        har_slice.combatants_roster,
        *har_slice.throughput,
        har_slice.damage_taken_abilities,
        har_slice.spell_healing,
    )
    identity: dict[str, list[dict[str, str]]] = {}
    throughput_capture_by_index: dict[int, str] = {}
    throughput_index = 0
    for observation in observations:
        resolved = _resolve_source_capture(connection, observation)
        identity.setdefault(observation.endpoint_code, []).append(resolved)
        if observation.endpoint_code == "report_encounter_throughput_timeline_api":
            throughput_capture_by_index[throughput_index] = resolved["capture_id"]
            throughput_index += 1
    return identity, throughput_capture_by_index


def persist_current_report_analytics_observations(
    *,
    database_path: Path,
    migrations_path: Path,
    har_slice: CurrentReportHarSlice,
    analytics: CurrentReportAnalyticsParseResult,
) -> dict[str, Any]:
    """Persist deterministic report analytics read-model observations without semantic promotion."""
    apply_migrations(database_path, migrations_path)

    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("DuckDB is required for current report analytics persistence") from exc

    with duckdb.connect(str(database_path)) as connection:
        source_identity, throughput_capture_by_index = _source_identity(connection, har_slice)
        required_endpoints = {
            "report_detail_api",
            "report_encounters_api",
            "report_combatants_roster_api",
            "report_encounter_throughput_timeline_api",
            "report_character_damage_taken_abilities_api",
            "report_character_spell_healing_api",
        }
        if set(source_identity) != required_endpoints:
            raise ValueError("current report analytics source endpoint set is incomplete")

        input_fingerprint = _sha256_json(
            {
                "persistence_version": CURRENT_REPORT_ANALYTICS_PERSISTENCE_VERSION,
                "source": source_identity,
            }
        )
        persistence_run_id = stable_id(
            "current_report_analytics_persistence_run",
            CURRENT_REPORT_ANALYTICS_PERSISTENCE_VERSION,
            input_fingerprint,
        )

        report_capture = source_identity["report_detail_api"][0]["capture_id"]
        encounter_capture = source_identity["report_encounters_api"][0]["capture_id"]
        roster_capture = source_identity["report_combatants_roster_api"][0]["capture_id"]
        damage_capture = source_identity["report_character_damage_taken_abilities_api"][0][
            "capture_id"
        ]
        healing_capture = source_identity["report_character_spell_healing_api"][0]["capture_id"]

        rows: list[dict[str, Any]] = []

        for entity in analytics.throughput_requests:
            request_index = int(entity["request_index"])
            capture_id = throughput_capture_by_index.get(request_index)
            if capture_id is None:
                raise ValueError("throughput analytics request has no exact source capture")
            entity_key = stable_id(
                "current_throughput_request",
                analytics.source_report_id,
                entity["source_encounter_id"],
                request_index,
                entity["metric"],
                entity.get("perspective"),
            )
            rows.append(
                _observation_row(
                    persistence_run_id=persistence_run_id,
                    entity_type="current_throughput_request_observation",
                    entity_key=entity_key,
                    entity=entity,
                    source_capture_ids=(
                        report_capture,
                        encounter_capture,
                        roster_capture,
                        capture_id,
                    ),
                )
            )

        for entity in analytics.throughput_characters:
            request_index = int(entity["request_index"])
            capture_id = throughput_capture_by_index.get(request_index)
            if capture_id is None:
                raise ValueError("throughput character observation has no exact source capture")
            entity_key = stable_id(
                "current_throughput_character",
                analytics.source_report_id,
                entity["source_encounter_id"],
                request_index,
                entity["source_character_id"],
            )
            rows.append(
                _observation_row(
                    persistence_run_id=persistence_run_id,
                    entity_type="current_throughput_character_observation",
                    entity_key=entity_key,
                    entity=entity,
                    source_capture_ids=(
                        report_capture,
                        encounter_capture,
                        roster_capture,
                        capture_id,
                    ),
                )
            )

        for index, entity in enumerate(analytics.throughput_points):
            request_index = int(entity["request_index"])
            capture_id = throughput_capture_by_index.get(request_index)
            if capture_id is None:
                raise ValueError("throughput point observation has no exact source capture")
            entity_key = stable_id(
                "current_throughput_point",
                analytics.source_report_id,
                entity["source_encounter_id"],
                request_index,
                index,
                entity.get("source_group_key"),
                entity.get("source_subgroup_key"),
                entity.get("bucket_ms"),
            )
            rows.append(
                _observation_row(
                    persistence_run_id=persistence_run_id,
                    entity_type="current_throughput_point_observation",
                    entity_key=entity_key,
                    entity=entity,
                    source_capture_ids=(
                        report_capture,
                        encounter_capture,
                        roster_capture,
                        capture_id,
                    ),
                )
            )

        for index, entity in enumerate(analytics.damage_taken_abilities):
            entity_key = stable_id(
                "current_damage_taken_ability",
                analytics.source_report_id,
                index,
                entity.get("source_group_key"),
                entity.get("source_subgroup_key"),
                entity.get("spell_id"),
            )
            rows.append(
                _observation_row(
                    persistence_run_id=persistence_run_id,
                    entity_type="current_damage_taken_ability_observation",
                    entity_key=entity_key,
                    entity=entity,
                    source_capture_ids=(report_capture, encounter_capture, damage_capture),
                )
            )

        for index, entity in enumerate(analytics.healing_spells):
            entity_key = stable_id(
                "current_healing_spell",
                analytics.source_report_id,
                index,
                entity.get("source_group_key"),
                entity.get("source_subgroup_key"),
                entity.get("source_character_id"),
                entity.get("spell_id"),
            )
            rows.append(
                _observation_row(
                    persistence_run_id=persistence_run_id,
                    entity_type="current_healing_spell_observation",
                    entity_key=entity_key,
                    entity=entity,
                    source_capture_ids=(report_capture, roster_capture, healing_capture),
                )
            )

        for entity_type, values in (
            (
                "current_healing_source_breakdown_observation",
                analytics.healing_source_breakdowns,
            ),
            (
                "current_healing_target_breakdown_observation",
                analytics.healing_target_breakdowns,
            ),
        ):
            for index, entity in enumerate(values):
                entity_key = stable_id(
                    entity_type,
                    analytics.source_report_id,
                    index,
                    entity.get("source_group_key"),
                    entity.get("source_subgroup_key"),
                )
                rows.append(
                    _observation_row(
                        persistence_run_id=persistence_run_id,
                        entity_type=entity_type,
                        entity_key=entity_key,
                        entity=entity,
                        source_capture_ids=(report_capture, roster_capture, healing_capture),
                    )
                )

        counts: dict[str, int] = {}
        for row in rows:
            entity_type = str(row["entity_type"])
            counts[entity_type] = counts.get(entity_type, 0) + 1
        output_fingerprint = _sha256_json(
            sorted(
                (
                    str(row["entity_type"]),
                    str(row["entity_key"]),
                    str(row["entity_hash"]),
                )
                for row in rows
            )
        )

        run_values = {
            "persistence_run_id": persistence_run_id,
            "reconstruction_sha256": input_fingerprint,
            "reconstruction_version": CURRENT_REPORT_ANALYTICS_PERSISTENCE_VERSION,
            "source_code": "coa_ascension_logs",
            "source_normalization_name": "current_report_analytics_v1",
            "status": "completed",
            "input_counts_json": _json(
                {
                    "source_capture_count": sum(len(values) for values in source_identity.values()),
                    "throughput_request_count": len(analytics.throughput_requests),
                    "throughput_character_count": len(analytics.throughput_characters),
                    "throughput_point_count": len(analytics.throughput_points),
                    "damage_taken_ability_count": len(analytics.damage_taken_abilities),
                    "healing_spell_count": len(analytics.healing_spells),
                    "healing_source_breakdown_count": len(
                        analytics.healing_source_breakdowns
                    ),
                    "healing_target_breakdown_count": len(
                        analytics.healing_target_breakdowns
                    ),
                }
            ),
            "persisted_counts_json": _json(counts),
            "source_batch_hashes_json": _json(source_identity),
            "metadata_json": _json(
                {
                    "persistence_version": CURRENT_REPORT_ANALYTICS_PERSISTENCE_VERSION,
                    "provenance_type": _PROVENANCE_TYPE,
                    "read_model_only": True,
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
                _CURRENT_ANALYSIS_TYPE,
                CURRENT_REPORT_ANALYTICS_PERSISTENCE_VERSION,
                input_fingerprint,
            )
            analysis_values = {
                "analysis_run_id": analysis_run_id,
                "analysis_type": _CURRENT_ANALYSIS_TYPE,
                "analysis_version": CURRENT_REPORT_ANALYTICS_PERSISTENCE_VERSION,
                "artifact_type": _CURRENT_ARTIFACT_TYPE,
                "artifact_key": input_fingerprint,
                "target_scope_json": _json(
                    {
                        "scope": "one_private_current_report_analytics_slice",
                        "source_capture_count": sum(
                            len(values) for values in source_identity.values()
                        ),
                    }
                ),
                "input_fingerprint": input_fingerprint,
                "output_fingerprint": output_fingerprint,
                "status": "completed",
                "metadata_json": _json(
                    {
                        "persisted_counts": counts,
                        "read_model_only": True,
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
        "persistence_version": CURRENT_REPORT_ANALYTICS_PERSISTENCE_VERSION,
        "status": "completed",
        "source_capture_count": sum(len(values) for values in source_identity.values()),
        "entity_count": len(rows),
        "entity_counts": dict(sorted(counts.items())),
        "inserted_observation_count": inserted,
        "matched_observation_count": matched,
        "input_fingerprint": input_fingerprint,
        "output_fingerprint": output_fingerprint,
        "contains_source_scalar_values": False,
        "contains_source_capture_ids": False,
        "read_model_only": True,
        "mechanic_semantics_verified": False,
        "planner_scoring_allowed": False,
        "reanalysis_dependencies_registered": False,
    }


__all__ = [
    "CURRENT_REPORT_ANALYTICS_PERSISTENCE_VERSION",
    "persist_current_report_analytics_observations",
]
