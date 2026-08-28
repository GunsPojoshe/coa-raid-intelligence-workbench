from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlsplit

from coa_workbench.analytics.public_api_encounter_context import EncounterReference

SELECTED_REPORT_SOURCE_AVAILABILITY_VERSION = "selected-report-source-availability-v1"
_ALLOWED_HOST = "coa.ascensionlogs.gg"
_SCHEMA_CANDIDATE_OUTCOME = "schema_candidate"


@dataclass(frozen=True, slots=True)
class _RequiredSourceFamily:
    endpoint_code: str
    route_suffix: str
    expected_query_keys: frozenset[str]

    def path(self, report_id: int) -> str:
        return f"/api/reports/{report_id}{self.route_suffix}"


_REQUIRED_SOURCE_FAMILIES = (
    _RequiredSourceFamily(
        endpoint_code="report_detail_api",
        route_suffix="",
        expected_query_keys=frozenset(),
    ),
    _RequiredSourceFamily(
        endpoint_code="report_encounters_api",
        route_suffix="/encounters",
        expected_query_keys=frozenset({"includeTrash"}),
    ),
    _RequiredSourceFamily(
        endpoint_code="report_combatants_roster_api",
        route_suffix="/combatants-roster",
        expected_query_keys=frozenset({"encounterIds"}),
    ),
)


@dataclass(frozen=True, slots=True)
class _SourceRow:
    observation_id: str
    raw_id: str
    request_url_sanitized: str | None
    request_key: str
    storage_path: str
    capture_id: str | None
    capture_endpoint_code: str | None
    latest_acquisition_outcome: str | None


@dataclass(frozen=True, slots=True)
class SelectedReportSourceFamilyAvailability:
    endpoint_code: str
    expected_query_key_count: int
    raw_observation_count: int
    reviewed_query_keys_match_count: int
    raw_payload_count: int
    raw_payload_file_present_count: int
    source_capture_count: int
    schema_candidate_capture_count: int
    schema_candidate_with_payload_count: int

    @property
    def archived_payload_available(self) -> bool:
        return self.raw_payload_file_present_count > 0

    @property
    def source_observatory_ready(self) -> bool:
        return self.schema_candidate_with_payload_count > 0

    def public_summary(self) -> dict[str, Any]:
        return {
            "endpoint_code": self.endpoint_code,
            "expected_query_key_count": self.expected_query_key_count,
            "raw_observation_count": self.raw_observation_count,
            "reviewed_query_keys_match_count": self.reviewed_query_keys_match_count,
            "raw_payload_count": self.raw_payload_count,
            "raw_payload_file_present_count": self.raw_payload_file_present_count,
            "source_capture_count": self.source_capture_count,
            "schema_candidate_capture_count": self.schema_candidate_capture_count,
            "schema_candidate_with_payload_count": self.schema_candidate_with_payload_count,
            "archived_payload_available": self.archived_payload_available,
            "source_observatory_ready": self.source_observatory_ready,
        }


@dataclass(frozen=True, slots=True)
class SelectedReportSourceAvailabilityReview:
    selected_report_current_runtime_persisted: bool
    families: tuple[SelectedReportSourceFamilyAvailability, ...]

    @property
    def archived_required_source_family_count(self) -> int:
        return sum(family.archived_payload_available for family in self.families)

    @property
    def observatory_ready_required_source_family_count(self) -> int:
        return sum(family.source_observatory_ready for family in self.families)

    @property
    def required_source_family_count(self) -> int:
        return len(self.families)

    @property
    def missing_required_source_family_count(self) -> int:
        return self.required_source_family_count - self.archived_required_source_family_count

    @property
    def offline_source_reuse_candidate(self) -> bool:
        return self.archived_required_source_family_count == self.required_source_family_count

    @property
    def offline_source_observatory_reuse_ready(self) -> bool:
        return self.observatory_ready_required_source_family_count == self.required_source_family_count

    @property
    def offline_current_report_runtime_reconstruction_possible(self) -> bool:
        return self.offline_source_observatory_reuse_ready

    def public_summary(self) -> dict[str, Any]:
        return {
            "review_version": SELECTED_REPORT_SOURCE_AVAILABILITY_VERSION,
            "required_source_family_count": self.required_source_family_count,
            "archived_required_source_family_count": self.archived_required_source_family_count,
            "observatory_ready_required_source_family_count": (
                self.observatory_ready_required_source_family_count
            ),
            "missing_required_source_family_count": self.missing_required_source_family_count,
            "selected_report_current_runtime_persisted": (
                self.selected_report_current_runtime_persisted
            ),
            "offline_source_reuse_candidate": self.offline_source_reuse_candidate,
            "offline_source_observatory_reuse_ready": self.offline_source_observatory_reuse_ready,
            "offline_current_report_runtime_reconstruction_possible": (
                self.offline_current_report_runtime_reconstruction_possible
            ),
            "source_families": [family.public_summary() for family in self.families],
            "network_request_count": 0,
            "raw_payload_bodies_read": False,
            "browser_har_used_this_run": False,
            "events_read_used": False,
            "selected_reference_same_report_build_binding_proven": False,
            "current_build_freshness_verified": False,
            "latest_snapshot_semantics_verified": False,
            "cross_report_identity_verified": False,
            "mechanic_semantics_verified": False,
            "planner_scoring_allowed": False,
            "report_ids_included": False,
            "encounter_ids_included": False,
            "request_urls_included": False,
            "query_values_included": False,
            "raw_ids_included": False,
            "raw_paths_included": False,
            "source_capture_ids_included": False,
            "source_fingerprints_included": False,
            "player_ids_included": False,
            "player_names_included": False,
            "build_values_included": False,
            "public_release_safe": True,
        }


def _request_key_scope(request_key: str) -> tuple[str, frozenset[str]] | None:
    if not request_key.startswith("GET:"):
        return None
    head = request_key[4:].split("#", 1)[0]
    if "?keys=" not in head:
        return head, frozenset()
    path, raw_keys = head.split("?keys=", 1)
    keys = frozenset(key for key in raw_keys.split(",") if key)
    return path, keys


def _request_scope(row: _SourceRow) -> tuple[str, frozenset[str]] | None:
    if row.request_url_sanitized:
        parsed = urlsplit(row.request_url_sanitized)
        if parsed.hostname != _ALLOWED_HOST:
            return None
        return parsed.path, frozenset(key for key, _value in parse_qsl(parsed.query))
    return _request_key_scope(row.request_key)


def _payload_present(raw_root: Path, storage_path: str) -> bool:
    stored = Path(storage_path)
    if stored.is_absolute():
        return False
    root = raw_root.resolve()
    candidate = (root / stored).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return candidate.is_file()


def _selected_runtime_persisted(entity_json_rows: list[str], report_id: int) -> bool:
    matches = 0
    for raw in entity_json_rows:
        try:
            entity = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("current_report_observation contains invalid entity_json") from exc
        if not isinstance(entity, dict):
            raise ValueError("current_report_observation entity_json must be an object")
        value = entity.get("source_report_id")
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, str)) and str(value).strip() == str(report_id):
            matches += 1
    if matches > 1:
        raise ValueError("selected report has duplicate persisted current-report identities")
    return matches == 1


def _load_local_state(database_path: Path) -> tuple[list[_SourceRow], list[str]]:
    if not database_path.is_file():
        raise FileNotFoundError(database_path)
    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("DuckDB is required to review selected-report source availability") from exc

    with duckdb.connect(str(database_path), read_only=True) as connection:
        tables = {str(row[0]) for row in connection.execute("SHOW TABLES").fetchall()}
        required = {
            "raw_object",
            "raw_fetch_observation",
            "source_capture",
            "source_acquisition_observation",
            "canonical_entity_observation",
        }
        missing = sorted(required - tables)
        if missing:
            raise ValueError(f"selected-report source availability requires tables: {missing}")

        rows = [
            _SourceRow(
                observation_id=str(row[0]),
                raw_id=str(row[1]),
                request_url_sanitized=str(row[2]) if row[2] is not None else None,
                request_key=str(row[3]),
                storage_path=str(row[4]),
                capture_id=str(row[5]) if row[5] is not None else None,
                capture_endpoint_code=str(row[6]) if row[6] is not None else None,
                latest_acquisition_outcome=str(row[7]) if row[7] is not None else None,
            )
            for row in connection.execute(
                """
                SELECT
                    rfo.observation_id,
                    rfo.raw_id,
                    rfo.request_url_sanitized,
                    ro.request_key,
                    ro.storage_path,
                    sc.capture_id,
                    sc.endpoint_code,
                    (
                        SELECT sao.outcome
                        FROM source_acquisition_observation AS sao
                        WHERE sao.source_capture_id = sc.capture_id
                        ORDER BY sao.observed_at DESC, sao.acquisition_id DESC
                        LIMIT 1
                    ) AS latest_acquisition_outcome
                FROM raw_fetch_observation AS rfo
                JOIN raw_object AS ro ON ro.raw_id = rfo.raw_id
                LEFT JOIN source_capture AS sc
                    ON sc.raw_observation_id = rfo.observation_id
                ORDER BY rfo.observation_id, sc.capture_id
                """
            ).fetchall()
        ]
        report_rows = [
            str(row[0])
            for row in connection.execute(
                """
                SELECT entity_json
                FROM canonical_entity_observation
                WHERE entity_type = 'current_report_observation'
                  AND trust_status = 'observed'
                ORDER BY entity_key, observation_id
                """
            ).fetchall()
        ]
    return rows, report_rows


def _review_family(
    rows: list[_SourceRow],
    *,
    raw_root: Path,
    report_id: int,
    family: _RequiredSourceFamily,
) -> SelectedReportSourceFamilyAvailability:
    expected_path = family.path(report_id)
    exact_path_rows: list[_SourceRow] = []
    exact_contract_rows: list[_SourceRow] = []
    for row in rows:
        scope = _request_scope(row)
        if scope is None:
            continue
        path, query_keys = scope
        if path != expected_path:
            continue
        exact_path_rows.append(row)
        if query_keys == family.expected_query_keys:
            exact_contract_rows.append(row)

    observation_ids = {row.observation_id for row in exact_path_rows}
    contract_observation_ids = {row.observation_id for row in exact_contract_rows}
    raw_ids = {row.raw_id for row in exact_contract_rows}
    payload_raw_ids = {
        row.raw_id
        for row in exact_contract_rows
        if _payload_present(raw_root, row.storage_path)
    }
    capture_ids = {
        row.capture_id
        for row in exact_contract_rows
        if row.capture_id is not None and row.capture_endpoint_code == family.endpoint_code
    }
    schema_candidate_capture_ids = {
        row.capture_id
        for row in exact_contract_rows
        if row.capture_id is not None
        and row.capture_endpoint_code == family.endpoint_code
        and row.latest_acquisition_outcome == _SCHEMA_CANDIDATE_OUTCOME
    }
    schema_candidate_with_payload_ids = {
        row.capture_id
        for row in exact_contract_rows
        if row.capture_id is not None
        and row.capture_endpoint_code == family.endpoint_code
        and row.latest_acquisition_outcome == _SCHEMA_CANDIDATE_OUTCOME
        and _payload_present(raw_root, row.storage_path)
    }

    return SelectedReportSourceFamilyAvailability(
        endpoint_code=family.endpoint_code,
        expected_query_key_count=len(family.expected_query_keys),
        raw_observation_count=len(observation_ids),
        reviewed_query_keys_match_count=len(contract_observation_ids),
        raw_payload_count=len(raw_ids),
        raw_payload_file_present_count=len(payload_raw_ids),
        source_capture_count=len(capture_ids),
        schema_candidate_capture_count=len(schema_candidate_capture_ids),
        schema_candidate_with_payload_count=len(schema_candidate_with_payload_ids),
    )


def review_selected_report_source_availability(
    database_path: Path,
    *,
    raw_root: Path,
    reference: EncounterReference,
) -> SelectedReportSourceAvailabilityReview:
    rows, report_rows = _load_local_state(database_path)
    families = tuple(
        _review_family(
            rows,
            raw_root=raw_root,
            report_id=reference.report_id,
            family=family,
        )
        for family in _REQUIRED_SOURCE_FAMILIES
    )
    return SelectedReportSourceAvailabilityReview(
        selected_report_current_runtime_persisted=_selected_runtime_persisted(
            report_rows,
            reference.report_id,
        ),
        families=families,
    )


__all__ = [
    "SELECTED_REPORT_SOURCE_AVAILABILITY_VERSION",
    "SelectedReportSourceAvailabilityReview",
    "SelectedReportSourceFamilyAvailability",
    "review_selected_report_source_availability",
]
