from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlsplit

import pytest

from coa_workbench.collector import RawArchive, capture_armory_api, load_source_registry
from coa_workbench.collector.http_profile import FETCH_CONTEXT_PROFILE_VERSION


class _Headers:
    def __init__(self, content_type: str = "application/json") -> None:
        self._content_type = content_type

    def get_content_type(self) -> str:
        return self._content_type


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
        parts = urlsplit(request.full_url)
        route = parts.path + (f"?{parts.query}" if parts.query else "")
        payload = self.payloads[route]
        body = payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")
        return _Response(body)


def _registry():
    return load_source_registry(Path("config/ascension_logs_sources.yaml"))


def _full_chain_payloads() -> dict[str, object]:
    return {
        "/api/armory/by-name/Gunspojoshe?realm=Vol%27Jin": {
            "success": True,
            "has_armory": True,
            "character": {"id": 123, "class": "Warlock"},
        },
        "/api/armory/character/123": {
            "success": True,
            "character": {"id": 123},
        },
        "/api/armory/character/123/captures?limit=7": {
            "success": True,
            "captures": [],
        },
        "/api/armory/talent-grid/warlock": {
            "success": True,
            "grid": [],
        },
    }


def test_full_armory_chain_uses_one_profile_and_archives_safe_metadata(tmp_path):
    opener = _RouteOpener(_full_chain_payloads())
    result = capture_armory_api(
        _registry(),
        RawArchive(tmp_path / "raw"),
        character="Gunspojoshe",
        realm="Vol'Jin",
        captures_limit=7,
        opener=opener,
    )

    assert result.character_id == 123
    assert result.character_class == "Warlock"
    assert result.has_armory is True
    assert result.identity_source == "by_name"
    assert result.http_profile_version == FETCH_CONTEXT_PROFILE_VERSION
    assert [item.observation_kind for item in result.observations] == [
        "by_name",
        "character",
        "captures",
        "talent_grid",
    ]
    assert len(opener.requests) == 4

    for request in opener.requests:
        headers = {name.casefold(): value for name, value in request.header_items()}
        assert headers["accept"] == "application/json, text/plain, */*"
        assert headers["referer"] == "https://coa.ascensionlogs.gg/"
        assert headers["sec-fetch-site"] == "same-origin"

    for observation in result.observations:
        assert observation.capture is not None
        manifest = json.loads(
            Path(observation.capture.manifest_path).read_text(encoding="utf-8")
        )
        metadata = manifest["metadata"]
        assert metadata["http_profile_version"] == FETCH_CONTEXT_PROFILE_VERSION
        assert "Cookie" not in metadata["request_header_names"]
        serialized = json.dumps(metadata).casefold()
        assert "mozilla/5.0" not in serialized
        assert "same-origin" not in serialized
        assert "application/json, text/plain" not in serialized


def test_has_armory_false_stops_after_by_name(tmp_path):
    opener = _RouteOpener(
        {
            "/api/armory/by-name/Gunspojoshe?realm=Vol%27Jin": {
                "success": True,
                "has_armory": False,
                "character": {"id": 123, "class": "Warlock"},
            }
        }
    )

    result = capture_armory_api(
        _registry(),
        RawArchive(tmp_path / "raw"),
        character="Gunspojoshe",
        realm="Vol'Jin",
        opener=opener,
    )

    assert result.has_armory is False
    assert [item.observation_kind for item in result.observations] == ["by_name"]
    assert len(opener.requests) == 1


def test_character_search_requires_one_exact_name_and_realm_match(tmp_path):
    payloads = {
        "/api/armory/by-name/Gunspojoshe?realm=Vol%27Jin": {"success": True},
        "/api/characters/search?q=Gunspojoshe&limit=20": {
            "success": True,
            "characters": [
                {"id": 1, "name": "Gunspojoshe", "realm": "Area 52", "class": "Mage"},
                {"id": 2, "name": "Other", "realm": "Vol'Jin", "class": "Priest"},
                {"id": 321, "name": "GUNSPOJOSHE", "realm": "VOL'JIN", "class": "Warlock"},
            ],
        },
        "/api/armory/character/321": {"success": True},
        "/api/armory/character/321/captures?limit=100": {
            "success": True,
            "captures": [],
        },
        "/api/armory/talent-grid/warlock": {"success": True, "grid": []},
    }
    opener = _RouteOpener(payloads)

    result = capture_armory_api(
        _registry(),
        RawArchive(tmp_path / "raw"),
        character="Gunspojoshe",
        realm="Vol'Jin",
        opener=opener,
    )

    assert result.character_id == 321
    assert result.character_class == "Warlock"
    assert result.identity_source == "character_search"


def test_invalid_json_is_archived_before_fallback(tmp_path):
    opener = _RouteOpener(
        {
            "/api/armory/by-name/Gunspojoshe?realm=Vol%27Jin": b"{broken",
            "/api/characters/search?q=Gunspojoshe&limit=20": {
                "success": True,
                "characters": [],
            },
        }
    )

    result = capture_armory_api(
        _registry(),
        RawArchive(tmp_path / "raw"),
        character="Gunspojoshe",
        realm="Vol'Jin",
        opener=opener,
    )

    by_name = result.observations[0]
    assert by_name.capture is not None
    assert Path(by_name.capture.payload_path).is_file()
    assert by_name.error == "response was not valid JSON"
    assert by_name.top_level_keys == ()


@pytest.mark.parametrize("limit", [0, 101])
def test_captures_limit_is_validated(limit, tmp_path):
    with pytest.raises(ValueError, match="between 1 and 100"):
        capture_armory_api(
            _registry(),
            RawArchive(tmp_path / "raw"),
            character="Gunspojoshe",
            realm="Vol'Jin",
            captures_limit=limit,
            opener=lambda *_args, **_kwargs: None,
        )
