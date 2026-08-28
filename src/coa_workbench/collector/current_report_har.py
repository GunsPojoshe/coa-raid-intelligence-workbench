from __future__ import annotations

import base64
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

CURRENT_REPORT_HAR_EXTRACTOR_VERSION = "current-report-har-extractor-v1"

_RE_REPORT_DETAIL = re.compile(r"^/api/reports/([^/]+)$")
_RE_ENCOUNTERS = re.compile(r"^/api/reports/([^/]+)/encounters$")
_RE_ROSTER = re.compile(r"^/api/reports/([^/]+)/combatants-roster$")
_RE_THROUGHPUT = re.compile(
    r"^/api/reports/([^/]+)/encounters/([^/]+)/throughput-timeline$"
)
_RE_DAMAGE = re.compile(r"^/api/reports/([^/]+)/character_damage_taken_abilities$")
_RE_HEALING = re.compile(r"^/api/reports/([^/]+)/character_spell_healing$")


def _utc_text(value: str) -> str:
    prepared = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(prepared)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("HAR startedDateTime must include timezone")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _response_body(content: dict[str, Any]) -> bytes | None:
    text = content.get("text")
    if text is None:
        return None
    if content.get("encoding") == "base64":
        try:
            return base64.b64decode(str(text), validate=True)
        except ValueError:
            return None
    return str(text).encode("utf-8")


@dataclass(frozen=True, slots=True)
class HarJsonObservation:
    endpoint_code: str
    request_url: str
    observed_at: str
    payload_bytes: bytes
    payload: dict[str, Any]

    @property
    def payload_hash(self) -> str:
        return hashlib.sha256(self.payload_bytes).hexdigest()


@dataclass(frozen=True, slots=True)
class CurrentReportHarSlice:
    report_detail: HarJsonObservation
    encounter_catalog: HarJsonObservation
    combatants_roster: HarJsonObservation
    throughput: tuple[HarJsonObservation, ...]
    damage_taken_abilities: HarJsonObservation
    spell_healing: HarJsonObservation

    def observations(self) -> tuple[HarJsonObservation, ...]:
        return (
            self.report_detail,
            self.encounter_catalog,
            self.combatants_roster,
            *self.throughput,
            self.damage_taken_abilities,
            self.spell_healing,
        )

    def public_summary(self) -> dict[str, Any]:
        return {
            "extractor_version": CURRENT_REPORT_HAR_EXTRACTOR_VERSION,
            "report_detail_count": 1,
            "encounter_catalog_count": 1,
            "combatants_roster_count": 1,
            "throughput_count": len(self.throughput),
            "damage_taken_abilities_count": 1,
            "spell_healing_count": 1,
            "contains_report_ids": False,
            "contains_encounter_ids": False,
            "contains_query_values": False,
            "contains_response_bodies": False,
        }


def _single(values: list[HarJsonObservation], label: str) -> HarJsonObservation:
    if len(values) != 1:
        raise ValueError(f"expected exactly one {label} response, found {len(values)}")
    return values[0]


def extract_current_report_har_slice(
    path: Path,
    *,
    allowed_host: str = "coa.ascensionlogs.gg",
) -> CurrentReportHarSlice:
    """Extract one current-report browser slice without guessing identifiers.

    v1 intentionally fails if the HAR contains more than one concrete report detail. That keeps
    provenance unambiguous until multi-report session grouping is implemented.
    """
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries = payload.get("log", {}).get("entries", [])
    if not isinstance(entries, list):
        raise ValueError("HAR log.entries must be an array")

    candidates: list[tuple[str, dict[str, Any], dict[str, Any], bytes, dict[str, Any]]] = []
    for raw_entry in entries:
        if not isinstance(raw_entry, dict):
            continue
        request = raw_entry.get("request", {})
        response = raw_entry.get("response", {})
        if not isinstance(request, dict) or not isinstance(response, dict):
            continue
        if str(request.get("method", "")).upper() != "GET":
            continue
        try:
            status = int(response.get("status") or 0)
        except (TypeError, ValueError):
            continue
        if status != 200:
            continue
        request_url = str(request.get("url") or "")
        parts = urlsplit(request_url)
        if parts.scheme != "https" or parts.hostname != allowed_host:
            continue
        if not parts.path.startswith("/api/reports/"):
            continue
        content = response.get("content", {})
        if not isinstance(content, dict):
            continue
        body = _response_body(content)
        if body is None:
            continue
        try:
            body_json = json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        if not isinstance(body_json, dict):
            continue
        candidates.append((parts.path, request, raw_entry, body, body_json))

    report_candidates = []
    for concrete_path, request, raw_entry, body, body_json in candidates:
        match = _RE_REPORT_DETAIL.fullmatch(concrete_path)
        if match and {"report", "encounters", "summary"} <= set(body_json):
            report_candidates.append((match.group(1), request, raw_entry, body, body_json))
    if len(report_candidates) != 1:
        raise ValueError(
            "current-report HAR extractor v1 requires exactly one concrete report detail; "
            f"found {len(report_candidates)}"
        )

    report_segment = report_candidates[0][0]
    buckets: dict[str, list[HarJsonObservation]] = {
        "report_detail_api": [],
        "report_encounters_api": [],
        "report_combatants_roster_api": [],
        "report_encounter_throughput_timeline_api": [],
        "report_character_damage_taken_abilities_api": [],
        "report_character_spell_healing_api": [],
    }

    for concrete_path, request, raw_entry, body, body_json in candidates:
        endpoint_code: str | None = None
        matched_report: str | None = None
        if (match := _RE_REPORT_DETAIL.fullmatch(concrete_path)) and {
            "report",
            "encounters",
            "summary",
        } <= set(body_json):
            endpoint_code = "report_detail_api"
            matched_report = match.group(1)
        elif match := _RE_ENCOUNTERS.fullmatch(concrete_path):
            endpoint_code = "report_encounters_api"
            matched_report = match.group(1)
        elif match := _RE_ROSTER.fullmatch(concrete_path):
            endpoint_code = "report_combatants_roster_api"
            matched_report = match.group(1)
        elif match := _RE_THROUGHPUT.fullmatch(concrete_path):
            endpoint_code = "report_encounter_throughput_timeline_api"
            matched_report = match.group(1)
        elif match := _RE_DAMAGE.fullmatch(concrete_path):
            endpoint_code = "report_character_damage_taken_abilities_api"
            matched_report = match.group(1)
        elif match := _RE_HEALING.fullmatch(concrete_path):
            endpoint_code = "report_character_spell_healing_api"
            matched_report = match.group(1)

        if endpoint_code is None or matched_report != report_segment:
            continue
        observed_at = _utc_text(str(raw_entry.get("startedDateTime") or ""))
        buckets[endpoint_code].append(
            HarJsonObservation(
                endpoint_code=endpoint_code,
                request_url=str(request.get("url") or ""),
                observed_at=observed_at,
                payload_bytes=body,
                payload=body_json,
            )
        )

    throughput = tuple(buckets["report_encounter_throughput_timeline_api"])
    if not throughput:
        raise ValueError("current-report HAR contains no throughput timeline responses")

    return CurrentReportHarSlice(
        report_detail=_single(buckets["report_detail_api"], "report detail"),
        encounter_catalog=_single(buckets["report_encounters_api"], "encounter catalog"),
        combatants_roster=_single(buckets["report_combatants_roster_api"], "combatants roster"),
        throughput=throughput,
        damage_taken_abilities=_single(
            buckets["report_character_damage_taken_abilities_api"],
            "damage taken abilities",
        ),
        spell_healing=_single(
            buckets["report_character_spell_healing_api"],
            "spell healing",
        ),
    )


__all__ = [
    "CURRENT_REPORT_HAR_EXTRACTOR_VERSION",
    "CurrentReportHarSlice",
    "HarJsonObservation",
    "extract_current_report_har_slice",
]
