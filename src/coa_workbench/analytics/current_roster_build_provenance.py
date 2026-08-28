from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from coa_workbench.analytics.public_api_encounter_context import EncounterReference

CURRENT_ROSTER_BUILD_PROVENANCE_VERSION = "current-roster-build-provenance-v1"
_EXPECTED_PROVENANCE_TYPE = "source_observatory_current_report_runtime_v1"
_ENTITY_TYPES = (
    "current_report_observation",
    "current_roster_character_observation",
    "current_roster_snapshot_observation",
    "current_talent_entry_observation",
    "current_gear_slot_observation",
)


@dataclass(frozen=True, slots=True)
class CurrentRosterBuildProvenanceReview:
    report_identity_resolved: bool
    character_count: int
    snapshot_count: int
    talent_entry_count: int
    gear_slot_observation_count: int
    characters_with_snapshot_count: int
    snapshot_character_link_count: int
    snapshot_entity_key_match_count: int
    snapshot_player_guid_present_count: int
    snapshot_player_realm_present_count: int
    snapshot_name_alignment_count: int
    snapshot_observed_timestamp_count: int
    snapshot_specialization_present_count: int
    snapshots_with_talent_count: int
    snapshots_with_gear_count: int
    source_provenance_observation_count: int
    total_scoped_observation_count: int
    cross_character_guid_conflict_count: int

    @property
    def report_scoped_player_identity_complete(self) -> bool:
        return (
            self.report_identity_resolved
            and self.character_count > 0
            and self.characters_with_snapshot_count == self.character_count
            and self.snapshot_character_link_count == self.snapshot_count
            and self.snapshot_entity_key_match_count == self.snapshot_count
            and self.snapshot_player_guid_present_count == self.snapshot_count
            and self.snapshot_player_realm_present_count == self.snapshot_count
            and self.snapshot_name_alignment_count == self.snapshot_count
            and self.cross_character_guid_conflict_count == 0
        )

    @property
    def observed_build_linkage_complete(self) -> bool:
        return (
            self.snapshot_count > 0
            and self.snapshot_specialization_present_count == self.snapshot_count
            and self.snapshots_with_talent_count == self.snapshot_count
            and self.snapshots_with_gear_count == self.snapshot_count
        )

    @property
    def source_provenance_complete(self) -> bool:
        return (
            self.total_scoped_observation_count > 0
            and self.source_provenance_observation_count == self.total_scoped_observation_count
        )

    @property
    def observed_build_provenance_complete(self) -> bool:
        return (
            self.report_scoped_player_identity_complete
            and self.observed_build_linkage_complete
            and self.source_provenance_complete
        )

    @property
    def observed_timestamp_coverage_complete(self) -> bool:
        return self.snapshot_count > 0 and self.snapshot_observed_timestamp_count == self.snapshot_count

    def public_summary(self) -> dict[str, Any]:
        return {
            "review_version": CURRENT_ROSTER_BUILD_PROVENANCE_VERSION,
            "report_identity_resolved": self.report_identity_resolved,
            "character_count": self.character_count,
            "snapshot_count": self.snapshot_count,
            "talent_entry_count": self.talent_entry_count,
            "gear_slot_observation_count": self.gear_slot_observation_count,
            "characters_with_snapshot_count": self.characters_with_snapshot_count,
            "snapshot_character_link_count": self.snapshot_character_link_count,
            "snapshot_entity_key_match_count": self.snapshot_entity_key_match_count,
            "snapshot_player_guid_present_count": self.snapshot_player_guid_present_count,
            "snapshot_player_realm_present_count": self.snapshot_player_realm_present_count,
            "snapshot_name_alignment_count": self.snapshot_name_alignment_count,
            "snapshot_observed_timestamp_count": self.snapshot_observed_timestamp_count,
            "snapshot_specialization_present_count": self.snapshot_specialization_present_count,
            "snapshots_with_talent_count": self.snapshots_with_talent_count,
            "snapshots_with_gear_count": self.snapshots_with_gear_count,
            "source_provenance_observation_count": self.source_provenance_observation_count,
            "total_scoped_observation_count": self.total_scoped_observation_count,
            "cross_character_guid_conflict_count": self.cross_character_guid_conflict_count,
            "report_scoped_player_identity_complete": self.report_scoped_player_identity_complete,
            "observed_build_linkage_complete": self.observed_build_linkage_complete,
            "source_provenance_complete": self.source_provenance_complete,
            "observed_build_provenance_complete": self.observed_build_provenance_complete,
            "observed_timestamp_coverage_complete": self.observed_timestamp_coverage_complete,
            "current_build_freshness_verified": False,
            "latest_snapshot_semantics_verified": False,
            "cross_report_identity_verified": False,
            "player_capability_semantics_verified": False,
            "mechanic_semantics_verified": False,
            "planner_scoring_allowed": False,
            "report_ids_included": False,
            "encounter_ids_included": False,
            "player_ids_included": False,
            "player_names_included": False,
            "player_guids_included": False,
            "realm_values_included": False,
            "build_values_included": False,
            "talent_values_included": False,
            "gear_values_included": False,
            "snapshot_hashes_included": False,
            "source_capture_ids_included": False,
            "raw_ids_included": False,
            "raw_paths_included": False,
            "source_fingerprints_included": False,
            "public_release_safe": True,
        }


def _object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def _nonempty_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    prepared = value.strip()
    return prepared or None


def _scalar_identity(value: Any) -> str | None:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        return None
    prepared = str(value).strip()
    return prepared or None


def _valid_observed_timestamp(value: Any) -> bool:
    text = _nonempty_text(value)
    if text is None:
        return False
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _load_rows(database_path: Path) -> list[tuple[str, str, str, str, str]]:
    if not database_path.is_file():
        raise FileNotFoundError(database_path)
    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("DuckDB is required to review current roster build provenance") from exc

    with duckdb.connect(str(database_path), read_only=True) as connection:
        tables = {str(row[0]) for row in connection.execute("SHOW TABLES").fetchall()}
        if "canonical_entity_observation" not in tables:
            raise ValueError("canonical_entity_observation is unavailable")
        return [
            (str(row[0]), str(row[1]), str(row[2]), str(row[3]), str(row[4]))
            for row in connection.execute(
                """
                SELECT entity_type, entity_key, entity_json, source_batch_ids_json, provenance_type
                FROM canonical_entity_observation
                WHERE entity_type IN (?, ?, ?, ?, ?)
                  AND trust_status = 'observed'
                ORDER BY entity_type, entity_key, observation_id
                """,
                list(_ENTITY_TYPES),
            ).fetchall()
        ]


def review_current_roster_build_provenance(
    database_path: Path,
    *,
    reference: EncounterReference,
) -> CurrentRosterBuildProvenanceReview:
    rows = _load_rows(database_path)
    decoded: list[tuple[str, str, dict[str, Any], str, str]] = []
    for entity_type, entity_key, entity_json, source_batch_ids_json, provenance_type in rows:
        try:
            entity = json.loads(entity_json)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{entity_type} contains invalid entity_json") from exc
        decoded.append(
            (
                entity_type,
                entity_key,
                _object(entity, f"{entity_type}.entity_json"),
                source_batch_ids_json,
                provenance_type,
            )
        )

    report_matches = [
        row
        for row in decoded
        if row[0] == "current_report_observation"
        and _scalar_identity(row[2].get("source_report_id")) == str(reference.report_id)
    ]
    if len(report_matches) != 1:
        raise ValueError(
            "current roster build provenance requires exactly one persisted report identity; "
            f"found {len(report_matches)}"
        )
    report = report_matches[0][2]
    canonical_report_id = _scalar_identity(report.get("report_id"))
    if canonical_report_id is None:
        raise ValueError("persisted current report observation has no canonical report_id")

    scoped = [
        row
        for row in decoded
        if row[0] == "current_report_observation"
        and row is report_matches[0]
        or row[0] != "current_report_observation"
        and _scalar_identity(row[2].get("report_id")) == canonical_report_id
    ]

    characters = [row for row in scoped if row[0] == "current_roster_character_observation"]
    snapshots = [row for row in scoped if row[0] == "current_roster_snapshot_observation"]
    talents = [row for row in scoped if row[0] == "current_talent_entry_observation"]
    gear = [row for row in scoped if row[0] == "current_gear_slot_observation"]

    character_by_key: dict[str, dict[str, Any]] = {}
    source_character_ids: set[str] = set()
    for _entity_type, entity_key, entity, _source_ids, _provenance in characters:
        character_key = _scalar_identity(entity.get("current_roster_character_id"))
        source_character_id = _scalar_identity(entity.get("source_character_id"))
        if character_key is None or character_key != entity_key:
            raise ValueError("current roster character entity key does not match persisted identity")
        if character_key in character_by_key:
            raise ValueError("current roster contains duplicate deterministic character identities")
        if source_character_id is None or source_character_id in source_character_ids:
            raise ValueError("current roster contains missing or duplicate source_character_id values")
        character_by_key[character_key] = entity
        source_character_ids.add(source_character_id)

    snapshots_by_character: dict[str, int] = {key: 0 for key in character_by_key}
    snapshot_keys: set[str] = set()
    snapshot_character_link_count = 0
    snapshot_entity_key_match_count = 0
    snapshot_player_guid_present_count = 0
    snapshot_player_realm_present_count = 0
    snapshot_name_alignment_count = 0
    snapshot_observed_timestamp_count = 0
    snapshot_specialization_present_count = 0
    guid_to_characters: dict[str, set[str]] = {}

    for _entity_type, entity_key, entity, _source_ids, _provenance in snapshots:
        character_key = _scalar_identity(entity.get("current_roster_character_id"))
        snapshot_hash = _nonempty_text(entity.get("snapshot_hash"))
        if snapshot_hash is not None:
            if snapshot_hash in snapshot_keys:
                raise ValueError("current roster contains duplicate snapshot hashes in one report")
            snapshot_keys.add(snapshot_hash)
        if snapshot_hash == entity_key:
            snapshot_entity_key_match_count += 1

        character = character_by_key.get(character_key or "")
        if character is not None:
            snapshot_character_link_count += 1
            snapshots_by_character[character_key or ""] += 1

        player = entity.get("player")
        outer = entity.get("outer_character")
        specialization = entity.get("specialization")
        if isinstance(player, dict):
            guid = _scalar_identity(player.get("guid"))
            if guid is not None:
                snapshot_player_guid_present_count += 1
                if character_key is not None:
                    guid_to_characters.setdefault(guid, set()).add(character_key)
            if _nonempty_text(player.get("realm")) is not None:
                snapshot_player_realm_present_count += 1
        else:
            player = {}
        if not isinstance(outer, dict):
            outer = {}
        if isinstance(specialization, dict) and (
            _nonempty_text(specialization.get("active_spec_name")) is not None
            or _scalar_identity(specialization.get("active_spec_idx")) is not None
            or _scalar_identity(specialization.get("active_spec_slot")) is not None
        ):
            snapshot_specialization_present_count += 1

        if character is not None:
            names = (
                _nonempty_text(character.get("name")),
                _nonempty_text(outer.get("name")),
                _nonempty_text(player.get("name")),
            )
            if names[0] is not None and names[0] == names[1] == names[2]:
                snapshot_name_alignment_count += 1

        if _valid_observed_timestamp(entity.get("captured_at")):
            snapshot_observed_timestamp_count += 1

    talent_snapshot_keys = {
        key
        for _entity_type, _entity_key, entity, _source_ids, _provenance in talents
        if (key := _nonempty_text(entity.get("snapshot_hash"))) is not None
        and _scalar_identity(entity.get("current_roster_character_id")) in character_by_key
    }
    gear_snapshot_keys = {
        key
        for _entity_type, _entity_key, entity, _source_ids, _provenance in gear
        if (key := _nonempty_text(entity.get("snapshot_hash"))) is not None
        and _scalar_identity(entity.get("current_roster_character_id")) in character_by_key
    }

    source_provenance_observation_count = 0
    for _entity_type, _entity_key, _entity, source_ids_json, provenance_type in scoped:
        try:
            source_ids = json.loads(source_ids_json)
        except json.JSONDecodeError:
            continue
        if (
            provenance_type == _EXPECTED_PROVENANCE_TYPE
            and isinstance(source_ids, list)
            and len(source_ids) > 0
            and all(_nonempty_text(value) is not None for value in source_ids)
        ):
            source_provenance_observation_count += 1

    return CurrentRosterBuildProvenanceReview(
        report_identity_resolved=True,
        character_count=len(characters),
        snapshot_count=len(snapshots),
        talent_entry_count=len(talents),
        gear_slot_observation_count=len(gear),
        characters_with_snapshot_count=sum(value > 0 for value in snapshots_by_character.values()),
        snapshot_character_link_count=snapshot_character_link_count,
        snapshot_entity_key_match_count=snapshot_entity_key_match_count,
        snapshot_player_guid_present_count=snapshot_player_guid_present_count,
        snapshot_player_realm_present_count=snapshot_player_realm_present_count,
        snapshot_name_alignment_count=snapshot_name_alignment_count,
        snapshot_observed_timestamp_count=snapshot_observed_timestamp_count,
        snapshot_specialization_present_count=snapshot_specialization_present_count,
        snapshots_with_talent_count=len(snapshot_keys & talent_snapshot_keys),
        snapshots_with_gear_count=len(snapshot_keys & gear_snapshot_keys),
        source_provenance_observation_count=source_provenance_observation_count,
        total_scoped_observation_count=len(scoped),
        cross_character_guid_conflict_count=sum(
            len(character_keys) > 1 for character_keys in guid_to_characters.values()
        ),
    )


__all__ = [
    "CURRENT_ROSTER_BUILD_PROVENANCE_VERSION",
    "CurrentRosterBuildProvenanceReview",
    "review_current_roster_build_provenance",
]
