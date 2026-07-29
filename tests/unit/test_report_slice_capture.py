from __future__ import annotations

import gzip
import json
from pathlib import Path
from urllib.parse import urlsplit

import pytest

from coa_workbench.collector import RawArchive, load_source_registry
from coa_workbench.collector.report_slice_capture import (
    COMBATANTS_INFO_ROUTE_SHAPE,
    ENCOUNTER_DETAIL_ROUTE_SHAPE,
    REPORT_DETAIL_ROUTE_SHAPE,
    capture_observed_report_slice,
    observed_report_slice_capture_to_dict,
)


class _Headers:
    def get_content_type(self) -> str:
        return "application/json"


class _Response:
    def __init__(self, body: bytes, *, status: int = 200) -> None:
        self.status = status
        self.headers = _Headers()
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self, size: int = -1) -> bytes:
        if size is None or size < 0:
            return self._body
        return self._body[:size]


class _RouteOpener:
    def __init__(self, payloads: dict[str, object]) -> None:
        self.payloads = payloads
        self.requests = []

    def __call__(self, request, **_kwargs):
        self.requests.append(request)
        path = urlsplit(request.full_url).path
        payload = self.payloads[path]
        body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        return _Response(body)


def _registry():
    return load_source_registry(Path("config/ascension_logs_sources.yaml"))


def _route_inventory(path: Path, *, include_combatants: bool = True) -> Path:
    routes = [
        {
            "route_shape": REPORT_DETAIL_ROUTE_SHAPE,
            "archive_count": 1,
            "semantic_status": "unverified_candidate",
        },
        {
            "route_shape": ENCOUNTER_DETAIL_ROUTE_SHAPE,
            "archive_count": 1,
            "semantic_status": "unverified_candidate",
        },
    ]
    if include_combatants:
        routes.append(
            {
                "route_shape": COMBATANTS_INFO_ROUTE_SHAPE,
                "archive_count": 1,
                "semantic_status": "unverified_candidate",
            }
        )
    payload = {
        "schema_version": 1,
        "inventory_kind": "archived_spa_api_route_inventory",
        "routes": routes,
        "summary": {
            "all_archives_verified": True,
            "contains_source_record_scalar_values": False,
            "semantic_verification_required": True,
            "network_requests_performed": False,
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_capture_uses_only_inventory_gated_routes_and_emits_scalar_free_result(tmp_path):
    report_id = 9988776655
    encounter_id = 5544332211
    paths = {
        f"/api/reports/{report_id}": {
            "report": {"id": report_id, "title": "Private report title"},
            "success": True,
        },
        f"/api/reports/{report_id}/encounters/{encounter_id}": {
            "encounter": {"id": encounter_id, "name": "Private encounter"},
            "success": True,
        },
        f"/api/reports/{report_id}/encounters/{encounter_id}/combatants-info": {
            "combatants": [{"name": "Private player"}],
            "success": True,
        },
    }
    opener = _RouteOpener(paths)
    progress_counts = []

    result = capture_observed_report_slice(
        _registry(),
        RawArchive(tmp_path / "raw"),
        route_inventory_path=_route_inventory(tmp_path / "inventory.json"),
        report_id=report_id,
        encounter_id=encounter_id,
        opener=opener,
        on_progress=lambda partial: progress_counts.append(len(partial.endpoints)),
    )
    rendered = observed_report_slice_capture_to_dict(result)

    assert result.all_complete is True
    assert progress_counts == [1, 2, 3]
    assert [urlsplit(request.full_url).path for request in opener.requests] == list(paths)
    assert rendered["summary"] == {
        "expected_endpoint_count": 3,
        "attempted_endpoint_count": 3,
        "complete_endpoint_count": 3,
        "all_complete": True,
        "contains_source_scalar_values": False,
        "semantic_verification_required": True,
        "normalization_allowed": False,
    }
    assert [row["route_template"] for row in rendered["endpoints"]] == [
        REPORT_DETAIL_ROUTE_SHAPE,
        ENCOUNTER_DETAIL_ROUTE_SHAPE,
        COMBATANTS_INFO_ROUTE_SHAPE,
    ]

    safe_output = json.dumps(rendered)
    assert str(report_id) not in safe_output
    assert str(encounter_id) not in safe_output
    assert "Private report title" not in safe_output
    assert "Private encounter" not in safe_output
    assert "Private player" not in safe_output

    for endpoint, source_payload in zip(result.endpoints, paths.values(), strict=True):
        assert endpoint.capture is not None
        archived = json.loads(gzip.decompress(Path(endpoint.capture.payload_path).read_bytes()))
        assert archived == source_payload
        observation = json.loads(
            Path(endpoint.capture.manifest_path).read_text(encoding="utf-8")
        )
        metadata = observation["metadata"]
        assert metadata["capture_mode"] == "observed_report_slice"
        assert metadata["route_template"] == endpoint.route_template
        serialized_metadata = json.dumps(metadata)
        assert str(report_id) not in serialized_metadata
        assert str(encounter_id) not in serialized_metadata


def test_missing_observed_route_blocks_all_network_requests(tmp_path):
    opener = _RouteOpener({})

    with pytest.raises(ValueError, match="missing required observed routes"):
        capture_observed_report_slice(
            _registry(),
            RawArchive(tmp_path / "raw"),
            route_inventory_path=_route_inventory(
                tmp_path / "inventory.json",
                include_combatants=False,
            ),
            report_id=1,
            encounter_id=2,
            opener=opener,
        )

    assert opener.requests == []


def test_invalid_json_is_archived_and_blocks_normalization(tmp_path):
    report_id = 100
    encounter_id = 200
    paths = {
        f"/api/reports/{report_id}": b"{broken",
        f"/api/reports/{report_id}/encounters/{encounter_id}": {"success": True},
        f"/api/reports/{report_id}/encounters/{encounter_id}/combatants-info": {
            "success": True
        },
    }

    result = capture_observed_report_slice(
        _registry(),
        RawArchive(tmp_path / "raw"),
        route_inventory_path=_route_inventory(tmp_path / "inventory.json"),
        report_id=report_id,
        encounter_id=encounter_id,
        opener=_RouteOpener(paths),
    )
    rendered = observed_report_slice_capture_to_dict(result)

    assert result.endpoints[0].capture is not None
    assert result.endpoints[0].error == "response was not valid JSON"
    assert result.all_complete is False
    assert rendered["summary"]["normalization_allowed"] is False


@pytest.mark.parametrize(
    ("report_id", "encounter_id"),
    [(0, 1), (1, 0), (-1, 2), (2, -1)],
)
def test_non_positive_identifiers_are_rejected_before_network(
    tmp_path,
    report_id,
    encounter_id,
):
    opener = _RouteOpener({})

    with pytest.raises(ValueError, match="positive integer"):
        capture_observed_report_slice(
            _registry(),
            RawArchive(tmp_path / "raw"),
            route_inventory_path=_route_inventory(tmp_path / "inventory.json"),
            report_id=report_id,
            encounter_id=encounter_id,
            opener=opener,
        )

    assert opener.requests == []
