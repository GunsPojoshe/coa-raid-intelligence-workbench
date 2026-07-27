from __future__ import annotations

import gzip
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from coa_workbench.collector import (
    RawArchive,
    build_armory_url,
    build_character_url,
    capture_character_build_pages,
    load_source_registry,
)


class _Headers:
    def __init__(self, content_type: str) -> None:
        self._content_type = content_type

    def get_content_type(self) -> str:
        return self._content_type


class _Response:
    def __init__(self, body: bytes, content_type: str = "text/html") -> None:
        self.status = 200
        self.headers = _Headers(content_type)
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self) -> bytes:
        return self._body


def _registry():
    return load_source_registry(Path("config/ascension_logs_sources.yaml"))


def test_build_urls_encode_character_realm_and_query():
    base_url = "https://coa.ascensionlogs.gg"
    armory = build_armory_url(base_url, character="Gunspojoshe", realm="Vol'Jin")
    character = build_character_url(
        base_url,
        character="Gunspojoshe",
        realm="Vol'Jin",
        phase=0,
        location="World Bosses",
        difficulty="normal",
        spec="Tyrant",
    )

    assert armory == "https://coa.ascensionlogs.gg/armory/Gunspojoshe/Vol%27Jin"
    parts = urlsplit(character)
    assert parts.path == "/characters/Gunspojoshe/Vol%27Jin"
    assert parse_qs(parts.query) == {
        "phase": ["0"],
        "location": ["World Bosses"],
        "difficulty": ["normal"],
        "spec": ["Tyrant"],
    }


def test_capture_archives_pages_and_embedded_json(tmp_path):
    html = b"""<!doctype html>
<html><body>
<script id="__NEXT_DATA__" type="application/json">
{"build":{"spec":"Tyrant","talents":[{"id":123,"rank":2}]}}
</script>
<script>window.notJson = true;</script>
</body></html>"""
    requested_urls: list[str] = []

    def opener(request, **_kwargs):
        requested_urls.append(request.full_url)
        return _Response(html)

    raw_root = tmp_path / "raw"
    results = capture_character_build_pages(
        _registry(),
        RawArchive(raw_root),
        character="Gunspojoshe",
        realm="Vol'Jin",
        spec="Tyrant",
        opener=opener,
    )

    assert len(results) == 2
    assert all(item.status == 200 for item in results)
    assert all(item.error is None for item in results)
    assert all(item.capture is not None for item in results)
    assert all(len(item.embedded_json) == 1 for item in results)
    assert requested_urls[0].startswith("https://coa.ascensionlogs.gg/characters/")
    assert requested_urls[1] == "https://coa.ascensionlogs.gg/armory/Gunspojoshe/Vol%27Jin"

    for result in results:
        embedded = result.embedded_json[0]
        assert embedded.script_id == "__NEXT_DATA__"
        path = Path(embedded.capture.payload_path)
        assert path.is_file()
        payload = json.loads(gzip.decompress(path.read_bytes()))
        assert payload["build"]["spec"] == "Tyrant"
        assert payload["build"]["talents"] == [{"id": 123, "rank": 2}]


def test_capture_does_not_persist_request_header_values(tmp_path):
    html = b"<html><body>public</body></html>"

    def opener(_request, **_kwargs):
        return _Response(html)

    result = capture_character_build_pages(
        _registry(),
        RawArchive(tmp_path / "raw"),
        character="Name",
        realm="Realm",
        opener=opener,
    )[0]

    observation = json.loads(Path(result.capture.manifest_path).read_text(encoding="utf-8"))
    metadata = observation["metadata"]
    assert metadata["request_header_names"] == ["Accept", "User-agent"]
    serialized = json.dumps(observation).casefold()
    assert "coa-raid-intelligence-workbench/0.1 armory-capture" not in serialized
