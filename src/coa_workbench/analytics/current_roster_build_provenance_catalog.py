from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from coa_workbench.analytics.current_roster_build_provenance import (
    CurrentRosterBuildProvenanceReview,
    review_current_roster_build_provenance,
)
from coa_workbench.analytics.public_api_encounter_context import EncounterReference

CURRENT_ROSTER_BUILD_PROVENANCE_CATALOG_VERSION = (
    "current-roster-build-provenance-catalog-v1"
)


def _source_report_id(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        prepared = value.strip()
        if prepared.isdigit():
            return int(prepared)
    return None


def _load_persisted_source_report_ids(database_path: Path) -> tuple[int, ...]:
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
        rows = connection.execute(
            """
            SELECT entity_json
            FROM canonical_entity_observation
            WHERE entity_type = 'current_report_observation'
              AND trust_status = 'observed'
            ORDER BY observation_id
            """
        ).fetchall()

    if not rows:
        raise ValueError("no persisted current report observations are available")

    source_report_ids: list[int] = []
    seen: set[int] = set()
    for row in rows:
        try:
            entity = json.loads(str(row[0]))
        except json.JSONDecodeError as exc:
            raise ValueError("current_report_observation contains invalid entity_json") from exc
        if not isinstance(entity, dict):
            raise ValueError("current_report_observation.entity_json must be an object")
        source_report_id = _source_report_id(entity.get("source_report_id"))
        if source_report_id is None:
            raise ValueError("persisted current report observation has no source_report_id")
        if source_report_id in seen:
            raise ValueError(
                "persisted current report observations contain duplicate source_report_id values"
            )
        seen.add(source_report_id)
        source_report_ids.append(source_report_id)

    return tuple(source_report_ids)


@dataclass(frozen=True, slots=True)
class CurrentRosterBuildProvenanceCatalogReview:
    persisted_report_count: int
    reviewed_report_scope_count: int
    report_scope_with_roster_count: int
    report_scoped_player_identity_complete_count: int
    observed_build_linkage_complete_count: int
    source_provenance_complete_count: int
    observed_build_provenance_complete_count: int
    observed_timestamp_coverage_complete_count: int
    character_count: int
    snapshot_count: int
    talent_entry_count: int
    gear_slot_observation_count: int
    selected_reference_present: bool
    selected_reference_report_scoped_player_identity_complete: bool
    selected_reference_observed_build_provenance_complete: bool

    @property
    def all_persisted_report_scopes_reviewed(self) -> bool:
        return (
            self.persisted_report_count > 0
            and self.reviewed_report_scope_count == self.persisted_report_count
        )

    @property
    def all_persisted_report_build_provenance_complete(self) -> bool:
        return (
            self.all_persisted_report_scopes_reviewed
            and self.observed_build_provenance_complete_count == self.persisted_report_count
        )

    @property
    def selected_reference_same_report_build_binding_proven(self) -> bool:
        return (
            self.selected_reference_present
            and self.selected_reference_report_scoped_player_identity_complete
            and self.selected_reference_observed_build_provenance_complete
        )

    def public_summary(self) -> dict[str, Any]:
        return {
            "catalog_version": CURRENT_ROSTER_BUILD_PROVENANCE_CATALOG_VERSION,
            "persisted_report_count": self.persisted_report_count,
            "reviewed_report_scope_count": self.reviewed_report_scope_count,
            "report_scope_with_roster_count": self.report_scope_with_roster_count,
            "report_scoped_player_identity_complete_count": (
                self.report_scoped_player_identity_complete_count
            ),
            "observed_build_linkage_complete_count": self.observed_build_linkage_complete_count,
            "source_provenance_complete_count": self.source_provenance_complete_count,
            "observed_build_provenance_complete_count": (
                self.observed_build_provenance_complete_count
            ),
            "observed_timestamp_coverage_complete_count": (
                self.observed_timestamp_coverage_complete_count
            ),
            "character_count": self.character_count,
            "snapshot_count": self.snapshot_count,
            "talent_entry_count": self.talent_entry_count,
            "gear_slot_observation_count": self.gear_slot_observation_count,
            "all_persisted_report_scopes_reviewed": self.all_persisted_report_scopes_reviewed,
            "all_persisted_report_build_provenance_complete": (
                self.all_persisted_report_build_provenance_complete
            ),
            "selected_reference_present": self.selected_reference_present,
            "selected_reference_report_scoped_player_identity_complete": (
                self.selected_reference_report_scoped_player_identity_complete
            ),
            "selected_reference_observed_build_provenance_complete": (
                self.selected_reference_observed_build_provenance_complete
            ),
            "selected_reference_same_report_build_binding_proven": (
                self.selected_reference_same_report_build_binding_proven
            ),
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


def review_current_roster_build_provenance_catalog(
    database_path: Path,
    *,
    reference: EncounterReference,
) -> CurrentRosterBuildProvenanceCatalogReview:
    source_report_ids = _load_persisted_source_report_ids(database_path)
    reviews: dict[int, CurrentRosterBuildProvenanceReview] = {}
    for source_report_id in source_report_ids:
        reviews[source_report_id] = review_current_roster_build_provenance(
            database_path,
            reference=EncounterReference(report_id=source_report_id, encounter_id=0),
        )

    selected = reviews.get(reference.report_id)
    values = tuple(reviews.values())
    return CurrentRosterBuildProvenanceCatalogReview(
        persisted_report_count=len(source_report_ids),
        reviewed_report_scope_count=len(values),
        report_scope_with_roster_count=sum(review.character_count > 0 for review in values),
        report_scoped_player_identity_complete_count=sum(
            review.report_scoped_player_identity_complete for review in values
        ),
        observed_build_linkage_complete_count=sum(
            review.observed_build_linkage_complete for review in values
        ),
        source_provenance_complete_count=sum(review.source_provenance_complete for review in values),
        observed_build_provenance_complete_count=sum(
            review.observed_build_provenance_complete for review in values
        ),
        observed_timestamp_coverage_complete_count=sum(
            review.observed_timestamp_coverage_complete for review in values
        ),
        character_count=sum(review.character_count for review in values),
        snapshot_count=sum(review.snapshot_count for review in values),
        talent_entry_count=sum(review.talent_entry_count for review in values),
        gear_slot_observation_count=sum(review.gear_slot_observation_count for review in values),
        selected_reference_present=selected is not None,
        selected_reference_report_scoped_player_identity_complete=(
            selected.report_scoped_player_identity_complete if selected is not None else False
        ),
        selected_reference_observed_build_provenance_complete=(
            selected.observed_build_provenance_complete if selected is not None else False
        ),
    )


__all__ = [
    "CURRENT_ROSTER_BUILD_PROVENANCE_CATALOG_VERSION",
    "CurrentRosterBuildProvenanceCatalogReview",
    "review_current_roster_build_provenance_catalog",
]
