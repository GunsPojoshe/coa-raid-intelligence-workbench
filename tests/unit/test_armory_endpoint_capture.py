from __future__ import annotations

import gzip
import json
from pathlib import Path
from urllib.parse import urlsplit

from coa_workbench.collector import (
    RawArchive,
    capture_armory_endpoints_progressively,
    load_source_registry,
)


class _Headers:
    def get_content_type(self) -> str:
        return "application/json"


class _Response:
    def __init__(self, payload: object, *, status: int = 200) -> None:
        self.status = status
        self.headers = _Headers()
        self._body = json.dumps(payload).encode("utf-8")

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
        route = urlsplit(request.full_url).path
        return _Response(self.payloads[route])


def _registry():
    return load_source_registry(Path("config/ascension_logs_sources.yaml"))


def _payloads() -> dict[str, object]:
    return {
        "/api/armory/character/156120": {
            "success": True,
            "character": {"id": 156120},
        },
        "/api/armory/talent-grid/felsworn": {
            "success": True,
            "grid": [],
        },
    }


def test_progressive_capture_writes_safe_complete_manifest(tmp_path):
    raw_root = tmp_path / "raw"
    output = tmp_path / "out" / "progress.json"
    opener = _RouteOpener(_payloads())

    result = capture_armory_endpoints_progressively(
        _registry(),
        RawArchive(raw_root),
        character_id="156120",
        class_slug="Felsworn",
        output_path=output,
        opener=opener,
    )

    assert output.is_file()
    assert result["summary"] == {
        "endpoint_count": 2,
        "captured": 2,
        "reused": 0,
        "failed": 0,
        "pending": 0,
        "complete": True,
    }
    assert [urlsplit(request.full_url).path for request in opener.requests] == [
        "/api/armory/character/156120",
        "/api/armory/talent-grid/felsworn",
    ]

    persisted = json.loads(output.read_text(encoding="utf-8"))
    assert persisted["subject"] == {
        "character_id": "156120",
        "class_slug": "felsworn",
    }
    serialized = json.dumps(persisted)
    assert str(tmp_path) not in serialized
    for endpoint_kind in ("character", "talent_grid"):
        entry = persisted["endpoints"][endpoint_kind]
        assert entry["state"] == "captured"
        assert entry["error"] is None
        assert entry["capture"]["schema_fingerprint"]
        assert not Path(entry["capture"]["payload_path"]).is_absolute()
        assert not Path(entry["capture"]["observation_manifest_path"]).is_absolute()


def test_resume_reuses_verified_archive_without_network(tmp_path):
    raw_root = tmp_path / "raw"
    output = tmp_path / "progress.json"
    first_opener = _RouteOpener(_payloads())
    archive = RawArchive(raw_root)

    capture_armory_endpoints_progressively(
        _registry(),
        archive,
        character_id=156120,
        class_slug="felsworn",
        output_path=output,
        opener=first_opener,
    )

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("network must not be used for a verified resumable capture")

    result = capture_armory_endpoints_progressively(
        _registry(),
        archive,
        character_id=156120,
        class_slug="felsworn",
        output_path=output,
        opener=fail_if_called,
    )

    assert result["summary"]["complete"] is True
    assert result["summary"]["reused"] == 2
    assert result["summary"]["captured"] == 0
    assert result["endpoints"]["character"]["reuse_count"] == 1
    assert result["endpoints"]["talent_grid"]["reuse_count"] == 1


def test_corrupt_archived_payload_is_not_reused(tmp_path):
    raw_root = tmp_path / "raw"
    output = tmp_path / "progress.json"
    archive = RawArchive(raw_root)
    first_opener = _RouteOpener(_payloads())

    capture_armory_endpoints_progressively(
        _registry(),
        archive,
        character_id=156120,
        class_slug="felsworn",
        output_path=output,
        endpoint_kinds=("character",),
        opener=first_opener,
    )
    manifest = json.loads(output.read_text(encoding="utf-8"))
    relative_payload = manifest["endpoints"]["character"]["capture"]["payload_path"]
    payload_path = raw_root / relative_payload
    with gzip.open(payload_path, "wb") as stream:
        stream.write(b'{"corrupt":true}')

    second_opener = _RouteOpener(_payloads())
    result = capture_armory_endpoints_progressively(
        _registry(),
        archive,
        character_id=156120,
        class_slug="felsworn",
        output_path=output,
        endpoint_kinds=("character",),
        opener=second_opener,
    )

    assert len(second_opener.requests) == 1
    assert result["endpoints"]["character"]["state"] == "captured"
    assert result["endpoints"]["character"]["attempt_count"] == 2


def test_transport_failure_is_persisted_without_capture(tmp_path):
    output = tmp_path / "progress.json"

    def timeout(*_args, **_kwargs):
        raise TimeoutError

    result = capture_armory_endpoints_progressively(
        _registry(),
        RawArchive(tmp_path / "raw"),
        character_id=156120,
        class_slug="felsworn",
        output_path=output,
        endpoint_kinds=("character",),
        timeout_seconds=1,
        opener=timeout,
    )

    entry = result["endpoints"]["character"]
    assert entry["state"] == "failed"
    assert entry["capture"] is None
    assert "timeout" in entry["error"]
    assert result["summary"]["complete"] is False
